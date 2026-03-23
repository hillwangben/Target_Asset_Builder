"""目录索引管理 - JSON 格式的全局目录文件"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models import AssetMeta, CollectionStats

logger = logging.getLogger(__name__)


class CatalogManager:
    """目录索引管理器，维护 catalog.json 文件。"""

    def __init__(self, root_dir: str = "./data", catalog_file: str = "catalog.json"):
        self._root = Path(root_dir).resolve()
        self._catalog_path = self._root / catalog_file
        self._assets: list[dict] = []
        self._version = "1.0"
        self._loaded = False

    @property
    def catalog_path(self) -> Path:
        return self._catalog_path

    @property
    def assets(self) -> list[dict]:
        return self._assets

    def load(self) -> None:
        """从磁盘加载目录索引。"""
        if self._loaded:
            return

        if not self._catalog_path.exists():
            logger.info("目录索引文件不存在，将创建新索引")
            self._assets = []
        else:
            try:
                with open(self._catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._version = data.get("version", "1.0")
                self._assets = data.get("assets", [])
                logger.info(f"已加载目录索引: {len(self._assets)} 条记录")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"目录索引文件损坏，将重新创建: {e}")
                self._assets = []

        self._loaded = True

    def save(self) -> None:
        """将目录索引保存到磁盘（原子写入）。"""
        self._root.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self._version,
            "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "assets": self._assets,
            "stats": self._compute_stats(),
        }

        # 原子写入：先写临时文件再重命名
        try:
            fd, tmp_path = tempfile.mkstemp(
                suffix=".tmp",
                prefix="catalog_",
                dir=str(self._root),
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            os.replace(tmp_path, str(self._catalog_path))
            logger.info(f"目录索引已保存: {self._catalog_path} ({len(self._assets)} 条)")
        except OSError as e:
            logger.error(f"保存目录索引失败: {e}")
            # 清理临时文件
            if "tmp_path" in locals():
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def add_asset(self, asset: AssetMeta) -> bool:
        """添加资产记录。如果已存在（基于 hash），返回 False。"""
        # 去重检查
        if self.exists(asset.id):
            logger.debug(f"资产已存在，跳过: {asset.file_path}")
            return False

        self._assets.append(asset.model_dump())
        return True

    def exists(self, asset_id: str) -> bool:
        """检查资产是否已存在。"""
        return any(a.get("id") == asset_id for a in self._assets)

    def exists_url(self, url: str) -> bool:
        """检查 URL 是否已采集（快速去重）。"""
        return any(
            a.get("source", {}).get("url") == url
            for a in self._assets
        )

    def remove_asset(self, asset_id: str) -> bool:
        """移除资产记录。"""
        original_len = len(self._assets)
        self._assets = [a for a in self._assets if a.get("id") != asset_id]
        return len(self._assets) < original_len

    def get_stats(self) -> CollectionStats:
        """获取采集统计信息。"""
        if not self._assets:
            return CollectionStats()

        stats = CollectionStats(total_files=len(self._assets))

        for asset in self._assets:
            # 按国家统计
            country = asset.get("country", "unknown")
            stats.by_country[country] = stats.by_country.get(country, 0) + 1

            # 按类型统计
            target_type = asset.get("type", "unknown")
            stats.by_type[target_type] = stats.by_type.get(target_type, 0) + 1

            # 按媒体类型统计
            media_type = asset.get("media_type", "unknown")
            stats.by_media[media_type] = stats.by_media.get(media_type, 0) + 1

            # 总大小
            stats.total_size += asset.get("file_size", 0)

        return stats

    def _compute_stats(self) -> dict:
        """计算统计信息（用于 JSON 输出）。"""
        stats = self.get_stats()
        return {
            "total_files": stats.total_files,
            "total_size": stats.total_size,
            "by_country": stats.by_country,
            "by_type": stats.by_type,
            "by_media": stats.by_media,
        }

    def get_assets_by_filter(
        self,
        country: Optional[str] = None,
        target_type: Optional[str] = None,
        model: Optional[str] = None,
        sensor: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> list[dict]:
        """按条件查询资产记录。"""
        results = self._assets

        if country:
            results = [a for a in results if a.get("country") == country]
        if target_type:
            results = [a for a in results if a.get("type") == target_type]
        if model:
            results = [a for a in results if a.get("model") == model]
        if sensor:
            results = [a for a in results if a.get("sensor") == sensor]
        if media_type:
            results = [a for a in results if a.get("media_type") == media_type]

        return results
