"""采集调度器 - 编排搜索→过滤→下载→存储的完整流程"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    DownloadColumn,
)

from src.catalog import CatalogManager
from src.config import AppConfig
from src.filters.resolution import ResolutionFilter
from src.models import (
    AssetMeta,
    CollectionStats,
    CollectionTask,
    MediaType,
    Resolution,
    SensorType,
    SourceInfo,
    SourceType,
)
from src.sources.base import DataSource
from src.sources.github_source import GitHubSource
from src.sources.url_source import UrlSource
from src.sources.web_source import WebSearchSource
from src.sources.huggingface_source import HuggingFaceSource
from src.sources.multi_source import MultiSourceCollector
from src.storage import StorageManager
from src.utils.downloader import AsyncDownloader
from src.utils.format_converter import FormatConverter
from src.utils.hashing import compute_file_hash
from src.utils.validator import FileValidator, check_audio_duration

logger = logging.getLogger(__name__)


class Collector:
    """采集调度器，负责编排完整的数据采集流程。"""

    def __init__(self, config: AppConfig):
        self._config = config
        self._storage = StorageManager(config.storage.root_dir)
        self._catalog = CatalogManager(
            config.storage.root_dir,
            config.storage.catalog_file,
        )
        self._resolution_filter = ResolutionFilter(
            enabled=config.filters.resolution.enabled,
            min_width=config.filters.resolution.min_width,
            min_height=config.filters.resolution.min_height,
            min_dimension=config.filters.resolution.min_dimension,
        )
        # 初始化格式转换器
        self._format_converter = FormatConverter(
            normalize=config.format.normalize,
            image_format=config.format.image_format,
            video_format=config.format.video_format,
            audio_format=config.format.audio_format,
        )
        # 初始化合法性校验器
        self._validator = FileValidator(
            enabled=config.validation.enabled,
            check_integrity=config.validation.check_integrity,
            check_safety=config.validation.check_safety,
            check_mime_type=config.validation.check_mime_type,
            min_audio_duration=config.validation.min_audio_duration,
        )
        self._stats = CollectionStats()

    def _create_source(self, source_name: str) -> DataSource:
        """根据名称创建数据源实例。"""
        if source_name == "github":
            gh_cfg = self._config.sources.github
            return GitHubSource(
                token=gh_cfg.token,
                per_page=gh_cfg.per_page,
                max_pages=gh_cfg.max_pages,
            )
        elif source_name == "url":
            url_cfg = self._config.sources.url
            return UrlSource(
                timeout=url_cfg.timeout,
                max_retries=url_cfg.max_retries,
            )
        elif source_name == "web":
            web_cfg = self._config.sources.web
            return WebSearchSource(
                timeout=web_cfg.timeout,
                max_retries=web_cfg.max_retries,
                user_agent=web_cfg.user_agent or None,
            )
        elif source_name == "huggingface":
            hf_cfg = self._config.sources.huggingface
            return HuggingFaceSource(
                timeout=hf_cfg.timeout,
                max_retries=hf_cfg.max_retries,
            )
        elif source_name == "multi":
            # 多源采集：同时使用多个数据源
            multi_cfg = self._config.sources.multi
            sources = []
            for src_name in multi_cfg.enabled_sources:
                if src_name != "multi":  # 避免递归
                    try:
                        sources.append(self._create_source(src_name))
                    except ValueError:
                        logger.warning(f"未知的数据源: {src_name}")
            return MultiSourceCollector(sources)
        else:
            raise ValueError(f"未知的数据源: {source_name}")

    async def collect(self, task: CollectionTask) -> CollectionStats:
        """执行采集任务。

        流程: 数据源搜索 → 去重检查 → 下载 → 分辨率过滤 → 存储 → 更新目录
        """
        logger.info(f"开始采集: {task.display_name}")

        self._catalog.load()
        self._storage.ensure_root()

        source = self._create_source(task.source)
        dl_cfg = self._config.download

        # 初始化限制条件
        collected_count = 0
        start_time = time.time()
        should_stop = False
        stop_reason = None

        try:
            async with AsyncDownloader(
                concurrency=dl_cfg.concurrency,
                timeout=dl_cfg.timeout,
                max_retries=dl_cfg.max_retries,
                max_file_size_mb=dl_cfg.max_file_size_mb,
            ) as downloader:

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=None,  # 使用默认 console
                ) as progress:
                    overall_task = progress.add_task(
                        f"[cyan]{task.display_name}[/cyan]",
                        total=None,
                    )

                    async for item in source.search(task):
                        # 检查是否达到停止条件
                        if should_stop:
                            logger.info(f"采集停止: {stop_reason}")
                            break

                        # 检查数量限制
                        if task.max_count is not None and collected_count >= task.max_count:
                            should_stop = True
                            stop_reason = f"已达到最大采集数量 {task.max_count}"
                            logger.info(stop_reason)
                            break

                        # 检查时间限制
                        if task.max_duration_seconds is not None:
                            elapsed = time.time() - start_time
                            if elapsed >= task.max_duration_seconds:
                                should_stop = True
                                stop_reason = f"已达到最大采集时长 {task.max_duration_seconds} 秒"
                                logger.info(stop_reason)
                                break
                        # URL 快速去重
                        if self._catalog.exists_url(item.url):
                            self._stats.skipped += 1
                            continue

                        # 下载到临时目录
                        tmp_dir = Path(self._storage.root) / ".tmp_downloads"
                        tmp_dir.mkdir(parents=True, exist_ok=True)

                        progress.update(
                            overall_task,
                            description=f"[cyan]下载: {item.filename}[/cyan]",
                        )

                        downloaded = await downloader.download(
                            url=item.url,
                            dest=tmp_dir,
                            filename=item.filename,
                        )

                        if downloaded is None:
                            self._stats.failed += 1
                            continue

                        # 分辨率过滤
                        passed, resolution = self._resolution_filter.check_file(
                            downloaded, item.media_type
                        )

                        if not passed:
                            logger.info(f"分辨率不达标，跳过: {item.filename}")
                            self._storage.remove_file(downloaded)
                            self._stats.skipped += 1
                            progress.advance(overall_task)
                            continue

                        # 合法性校验
                        validation_result = self._validator.validate(
                            downloaded,
                            item.media_type,
                        )
                        if not validation_result.valid:
                            logger.warning(f"合法性校验失败: {item.filename} - {validation_result.error}")
                            self._storage.remove_file(downloaded)
                            self._stats.skipped += 1
                            progress.advance(overall_task)
                            continue

                        # 格式规范化转换
                        converted = self._format_converter.convert(downloaded, item.media_type)
                        if converted is None and downloaded.suffix.lower() != converted.suffix.lower() if converted else False:
                            # 转换失败且原文件被删除
                            logger.warning(f"格式转换失败，跳过: {item.filename}")
                            self._storage.remove_file(downloaded)
                            self._stats.failed += 1
                            progress.advance(overall_task)
                            continue
                        if converted and converted != downloaded:
                            downloaded = converted
                            # 更新分辨率信息（格式转换可能改变分辨率）
                            passed, resolution = self._resolution_filter.check_file(
                                downloaded, item.media_type
                            )
                            if not passed:
                                logger.info(f"转换后分辨率不达标，跳过: {downloaded.name}")
                                self._storage.remove_file(downloaded)
                                self._stats.skipped += 1
                                progress.advance(overall_task)
                                continue

                        # 音频时长校验
                        if item.media_type == MediaType.AUDIO:
                            if not check_audio_duration(downloaded, self._config.validation.min_audio_duration):
                                logger.info(f"音频时长不达标，跳过: {downloaded.name}")
                                self._storage.remove_file(downloaded)
                                self._stats.skipped += 1
                                progress.advance(overall_task)
                                continue

                        # 计算文件哈希
                        file_hash = compute_file_hash(downloaded)

                        # 哈希去重
                        if self._catalog.exists(file_hash):
                            logger.debug(f"文件内容重复，跳过: {item.filename}")
                            self._storage.remove_file(downloaded)
                            self._stats.skipped += 1
                            progress.advance(overall_task)
                            continue

                        # 存储到分类目录
                        stored_path = self._storage.store_file(
                            src_file=downloaded,
                            country=task.country,
                            target_type=task.type.value,
                            model=task.model,
                            sensor=task.sensor,
                            media_type=item.media_type,
                        )

                        # 构建元信息并添加到目录
                        asset = self._build_asset_meta(
                            file_hash=file_hash,
                            file_path=str(self._storage.get_relative_path(stored_path)),
                            file_size=stored_path.stat().st_size,
                            resolution=resolution,
                            media_type=item.media_type,
                            task=task,
                            item=item,
                        )
                        self._catalog.add_asset(asset)
                        progress.advance(overall_task)

                    progress.update(overall_task, completed=True)

        finally:
            await source.close()

        # 保存目录索引
        self._catalog.save()
        self._stats = self._catalog.get_stats()
        return self._stats

    @staticmethod
    def _build_asset_meta(
        file_hash: str,
        file_path: str,
        file_size: int,
        resolution: Optional[Resolution],
        media_type: MediaType,
        task: CollectionTask,
        item,
    ) -> AssetMeta:
        """构建资产元信息对象。"""
        from pathlib import PurePosixPath

        source_type = SourceType.GITHUB if item.extra.get("repo") else SourceType.URL
        source_info = SourceInfo(
            type=source_type,
            repo=item.extra.get("repo"),
            url=item.url,
        )

        return AssetMeta(
            id=file_hash,
            country=task.country,
            type=task.type,
            model=task.model,
            sensor=task.sensor,
            media_type=media_type,
            format=PurePosixPath(file_path).suffix.lower().lstrip("."),
            resolution=resolution,
            file_path=file_path,
            file_size=file_size,
            source=source_info,
        )

    def get_stats(self) -> CollectionStats:
        """获取当前采集统计。"""
        self._catalog.load()
        return self._catalog.get_stats()
