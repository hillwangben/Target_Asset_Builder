"""数据源抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.models import CollectionTask, SearchResultItem


class DataSource(ABC):
    """数据源抽象基类，所有数据源必须实现此接口。"""

    @abstractmethod
    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """根据采集任务搜索资源。

        Args:
            task: 采集任务
            media_type: 可选，限定媒体类型（image/video/audio）

        Yields:
            SearchResultItem: 搜索结果条目
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭数据源连接，释放资源。"""
        ...
