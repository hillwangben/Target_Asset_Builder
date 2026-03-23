"""多源综合采集器 - 同时从多个数据源采集"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from src.models import CollectionTask, MediaType, SearchResultItem
from src.sources.base import DataSource


class MultiSourceCollector(DataSource):
    """多源综合采集器。

    从多个数据源同时采集数据，合并结果。
    支持的数据源：
    - github: GitHub 仓库
    - url: 直接 URL 列表
    - web: 网页搜索
    - huggingface: HuggingFace 数据集
    """

    def __init__(self, sources: list[DataSource]):
        """初始化多源采集器。

        Args:
            sources: 数据源列表
        """
        self._sources = sources

    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """从所有数据源搜索资源。

        并发搜索所有数据源，合并结果。
        """
        # 为每个数据源创建异步生成器
        async def search_source(source: DataSource) -> AsyncIterator[SearchResultItem]:
            try:
                async for item in source.search(task, media_type):
                    yield item
            except Exception as e:
                logger.error(f"[MultiSource] 数据源 {source.__class__.__name__} 搜索失败: {e}")

        # 合并所有数据源的生成器
        async def merge_generators(generators: list[AsyncIterator[SearchResultItem]]) -> AsyncIterator[SearchResultItem]:
            """合并多个异步生成器。"""
            # 创建任务队列
            queue: asyncio.Queue[Optional[SearchResultItem]] = asyncio.Queue()
            active_tasks = len(generators)

            # 消费者任务
            async def producer(gen: AsyncIterator[SearchResultItem]) -> None:
                nonlocal active_tasks
                try:
                    async for item in gen:
                        await queue.put(item)
                except Exception:
                    pass
                finally:
                    await queue.put(None)  # 发送结束信号
                    active_tasks -= 1

            # 启动所有生产者
            tasks = [asyncio.create_task(producer(gen)) for gen in generators]

            # 消费所有结果
            completed = 0
            while completed < len(generators):
                item = await queue.get()
                if item is None:
                    completed += 1
                else:
                    yield item

            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)

        # 创建所有数据源的生成器
        generators = [search_source(source) for source in self._sources]

        # 合并生成器
        async for item in merge_generators(generators):
            yield item

    async def close(self) -> None:
        """关闭所有数据源。"""
        await asyncio.gather(
            *[source.close() for source in self._sources],
            return_exceptions=True,
        )
