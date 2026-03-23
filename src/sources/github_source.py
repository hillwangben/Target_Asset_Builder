"""GitHub 数据源 - 通过 GitHub API 搜索和获取军事目标数据"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import PurePosixPath
from typing import AsyncIterator, Optional

from github import Github, GithubException
from github.Repository import Repository

from src.models import CollectionTask, MediaType, SearchResultItem
from src.sources.base import DataSource

logger = logging.getLogger(__name__)

# 支持的图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
# 支持的视频扩展名
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
# 支持的音频扩展名
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".wma", ".m4a"}


def _guess_media_type(filename: str) -> MediaType:
    """根据文件扩展名推断媒体类型。"""
    ext = PurePosixPath(filename).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    if ext in AUDIO_EXTENSIONS:
        return MediaType.AUDIO
    return MediaType.IMAGE


class GitHubSource(DataSource):
    """GitHub 数据源，支持仓库搜索、文件遍历和 Release 下载。"""

    def __init__(self, token: str = "", per_page: int = 30, max_pages: int = 5):
        self._github = Github(token) if token else Github()
        self._per_page = min(per_page, 100)
        self._max_pages = max_pages

    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """搜索 GitHub 仓库中的相关文件。

        策略：
        1. 使用关键词搜索仓库
        2. 遍历仓库文件树，过滤媒体文件
        3. 同时搜索仓库的 Release 资源
        """
        keywords = " ".join(task.keywords)
        logger.info(f"[GitHub] 搜索关键词: {keywords}")

        try:
            repos = self._github.search_repositories(
                keywords,
                sort="stars",
                order="desc",
            )
        except GithubException as e:
            logger.error(f"[GitHub] 搜索失败: {e}")
            return

        count = 0
        page = 0
        for repo in repos:
            if page >= self._max_pages:
                break
            page += 1
            count += 1

            logger.info(f"[GitHub] 处理仓库 ({count}/{self._max_pages}): {repo.full_name}")

            # 遍历仓库文件
            async for item in self._traverse_repo(repo, media_type):
                yield item

            # 搜索 Release 资源
            async for item in self._traverse_releases(repo, media_type):
                yield item

    async def _traverse_repo(
        self,
        repo: Repository,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """递归遍历仓库文件树，筛选媒体文件。"""
        try:
            contents = repo.get_contents("")
        except GithubException:
            return

        stack = list(contents) if isinstance(contents, list) else [contents]

        while stack:
            try:
                item = stack.pop()
            except (IndexError, AttributeError):
                break

            if item.type == "dir":
                try:
                    sub_contents = repo.get_contents(item.path)
                    if isinstance(sub_contents, list):
                        stack.extend(sub_contents)
                except GithubException:
                    continue
            elif item.type == "file":
                ext = PurePosixPath(item.name).suffix.lower()
                all_media_exts = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

                if ext not in all_media_exts:
                    continue

                mt = _guess_media_type(item.name)
                if media_type and mt.value != media_type:
                    continue

                download_url = (
                    item.download_url
                    if hasattr(item, "download_url") and item.download_url
                    else item.raw_url
                    if hasattr(item, "raw_url")
                    else f"https://raw.githubusercontent.com/{repo.full_name}/main/{item.path}"
                )

                yield SearchResultItem(
                    url=download_url,
                    filename=item.name,
                    media_type=mt,
                    file_size=item.size if hasattr(item, "size") else None,
                    preview_url=download_url,
                    extra={
                        "repo": repo.full_name,
                        "path": item.path,
                        "sha": item.sha if hasattr(item, "sha") else None,
                    },
                )

    async def _traverse_releases(
        self,
        repo: Repository,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """遍历仓库 Release 中的资产。"""
        try:
            releases = repo.get_releases()
            for release in releases[:3]:  # 只检查最近 3 个 release
                for asset in release.get_assets():
                    mt = _guess_media_type(asset.name)
                    if media_type and mt.value != media_type:
                        continue

                    ext = PurePosixPath(asset.name).suffix.lower()
                    all_media_exts = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
                    if ext not in all_media_exts:
                        continue

                    yield SearchResultItem(
                        url=asset.browser_download_url,
                        filename=asset.name,
                        media_type=mt,
                        file_size=asset.size,
                        extra={
                            "repo": repo.full_name,
                            "release": release.tag_name,
                        },
                    )
        except GithubException:
            pass

    async def close(self) -> None:
        """关闭 GitHub 连接。"""
        self._github.close()
