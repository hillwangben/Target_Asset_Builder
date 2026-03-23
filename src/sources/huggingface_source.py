"""HuggingFace 数据集数据源"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

import httpx

from src.models import CollectionTask, MediaType, SearchResultItem
from src.sources.base import DataSource

logger = logging.getLogger(__name__)

# 支持的图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
# 支持的视频扩展名
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
# 支持的音频扩展名
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".wma", ".m4a"}


class HuggingFaceSource(DataSource):
    """HuggingFace 数据集数据源。

    从 HuggingFace 数据集中获取相关资源。
    支持：
    - 搜索数据集
    - 获取数据集文件列表
    - 下载特定文件
    """

    API_BASE = "https://huggingface.co/api"

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）。"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
            )
        return self._client

    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """搜索 HuggingFace 数据集。

        keywords 可以是：
        1. 数据集名称（如 "huggingface/datasets"）
        2. 搜索关键词
        """
        client = await self._get_client()
        keywords = " ".join(task.keywords)

        logger.info(f"[HuggingFace] 搜索关键词: {keywords}")

        # 尝试作为数据集 ID 直接访问
        dataset_id = keywords.strip().replace("https://huggingface.co/datasets/", "")
        dataset_id = dataset_id.strip("/")

        try:
            # 获取数据集文件列表
            files = await self._get_dataset_files(client, dataset_id)

            for file_info in files:
                filename = file_info["path"]
                file_url = f"https://huggingface.co/datasets/{dataset_id}/resolve/main/{filename}"

                mt = self._guess_media_type(filename)
                if media_type and mt.value != media_type:
                    continue

                yield SearchResultItem(
                    url=file_url,
                    filename=filename.split("/")[-1],
                    media_type=mt,
                    file_size=file_info.get("size"),
                    extra={
                        "source_type": "huggingface",
                        "dataset": dataset_id,
                        "path": filename,
                    },
                )

        except Exception as e:
            logger.warning(f"[HuggingFace] 获取数据集失败 {dataset_id}: {e}")

    async def _get_dataset_files(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
    ) -> list[dict]:
        """获取数据集文件列表。"""
        # 尝试获取文件树
        try:
            response = await client.get(f"{self.API_BASE}/datasets/{dataset_id}/tree/main")
            response.raise_for_status()
            tree = response.json()

            files = []
            for item in tree:
                if item["type"] == "file":
                    files.append(item)

            return files

        except httpx.HTTPStatusError as e:
            # 如果树 API 不可用，尝试获取列表
            if e.response.status_code == 404:
                response = await client.get(f"{self.API_BASE}/datasets/{dataset_id}")
                response.raise_for_status()
                data = response.json()
                return data.get("siblings", [])
            raise

    def _guess_media_type(self, filename: str) -> MediaType:
        """根据文件扩展名推断媒体类型。"""
        from pathlib import PurePosixPath

        ext = PurePosixPath(filename).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        if ext in VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        if ext in AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        return MediaType.IMAGE

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client:
            await self._client.aclose()
            self._client = None
