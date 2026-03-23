"""通用 URL 数据源 - 从直接 URL 列表下载资源"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from src.models import CollectionTask, SearchResultItem
from src.sources.base import DataSource

logger = logging.getLogger(__name__)


class UrlSource(DataSource):
    """通用 URL 数据源，从给定的 URL 列表直接下载。

    需要在 CollectionTask.keywords 中传入 URL 列表。
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self._timeout = timeout
        self._max_retries = max_retries

    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """从 URL 列表中生成搜索结果。

        keywords 中每项被视为一个下载 URL。
        """
        for url in task.keywords:
            # 从 URL 推断文件名
            from urllib.parse import urlparse
            path = urlparse(url).path
            filename = path.rstrip("/").split("/")[-1] if path else "unknown_file"

            if not filename or "." not in filename:
                filename = "unknown_file"

            yield SearchResultItem(
                url=url,
                filename=filename,
                extra={"source_type": "url"},
            )

    async def close(self) -> None:
        """无需关闭。"""
        pass
