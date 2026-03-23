"""网页搜索数据源 - 通过搜索引擎查找相关资源"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator, Optional
from urllib.parse import urljoin, urlparse

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


class WebSearchSource(DataSource):
    """网页搜索数据源，从搜索引擎结果中提取媒体链接。

    支持从搜索引擎搜索结果页面中解析出图片、视频、音频链接。
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = None,
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）。"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": self._user_agent},
            )
        return self._client

    async def search(
        self,
        task: CollectionTask,
        media_type: str | None = None,
    ) -> AsyncIterator[SearchResultItem]:
        """从网页中提取媒体链接。

        keywords 中每项被视为一个网页 URL。
        遍历页面内容，提取所有媒体链接。
        """
        client = await self._get_client()

        for url in task.keywords:
            try:
                logger.info(f"[Web] 解析网页: {url}")

                # 获取网页内容
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

                # 提取所有媒体链接
                media_urls = self._extract_media_links(html, url, media_type)

                for media_url in media_urls:
                    filename = self._extract_filename(media_url)
                    mt = self._guess_media_type(filename)

                    if media_type and mt.value != media_type:
                        continue

                    yield SearchResultItem(
                        url=media_url,
                        filename=filename,
                        media_type=mt,
                        extra={
                            "source_type": "web",
                            "ref_url": url,
                        },
                    )

            except Exception as e:
                logger.warning(f"[Web] 处理网页失败 {url}: {e}")
                continue

    def _extract_media_links(
        self,
        html: str,
        base_url: str,
        media_type: str | None = None,
    ) -> list[str]:
        """从 HTML 中提取媒体链接。

        支持：
        - <img src="...">
        - <video poster="...">、<source src="...">
        - <audio src="...">
        - CSS 中的 background-image
        - data-src 等延迟加载属性
        """
        urls = set()

        # 图片标签
        img_pattern = r'<img[^>]+\bsrc=["\']([^"\']+)["\']'
        urls.update(re.findall(img_pattern, html, re.IGNORECASE))

        # video 和 audio 标签
        video_pattern = r'<(?:video|audio)[^>]+\bsrc=["\']([^"\']+)["\']'
        urls.update(re.findall(video_pattern, html, re.IGNORECASE))

        # source 标签
        source_pattern = r'<source[^>]+\bsrc=["\']([^"\']+)["\']'
        urls.update(re.findall(source_pattern, html, re.IGNORECASE))

        # data-src 等延迟加载属性
        lazy_pattern = r'data-(?:src|srcset|url)=["\']([^"\']+)["\']'
        urls.update(re.findall(lazy_pattern, html, re.IGNORECASE))

        # CSS background-image
        bg_pattern = r'background-image:\s*url\(["\']?([^"\'\\)]+)["\']?\)'
        urls.update(re.findall(bg_pattern, html, re.IGNORECASE))

        # 处理相对路径
        absolute_urls = []
        for url in urls:
            # 跳过 data: URL
            if url.startswith("data:"):
                continue
            # 转换为绝对路径
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                parsed = urlparse(base_url)
                url = f"{parsed.scheme}://{parsed.netloc}{url}"
            elif not url.startswith(("http://", "https://")):
                url = urljoin(base_url, url)
            absolute_urls.append(url)

        return absolute_urls

    def _extract_filename(self, url: str) -> str:
        """从 URL 中提取文件名。"""
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        filename = path.split("/")[-1] if path else "downloaded_file"
        return filename or "downloaded_file"

    def _guess_media_type(self, filename: str) -> MediaType:
        """根据文件扩展名推断媒体类型。"""
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
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
