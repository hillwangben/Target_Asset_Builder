"""异步文件下载器，支持并发控制、断点续传和重试"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import httpx
import aiofiles

logger = logging.getLogger(__name__)


class AsyncDownloader:
    """异步文件下载器。"""

    def __init__(
        self,
        concurrency: int = 5,
        timeout: int = 120,
        max_retries: int = 3,
        max_file_size_mb: int = 100,
    ):
        self._concurrency = concurrency
        self._timeout = timeout
        self._max_retries = max_retries
        self._max_file_size = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else 0
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout, connect=30.0),
                follow_redirects=True,
                headers={
                    "User-Agent": "TargetAssetBuilder/1.0",
                },
            )
        return self._client

    async def download(
        self,
        url: str,
        dest: Path,
        filename: str | None = None,
    ) -> Optional[Path]:
        """下载文件到指定目录。

        Args:
            url: 下载 URL
            dest: 目标目录
            filename: 文件名，为 None 时从 URL 或 Content-Disposition 推断

        Returns:
            下载成功的文件路径，失败返回 None
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._concurrency)

        async with self._semaphore:
            return await self._download_with_retry(url, dest, filename)

    async def _download_with_retry(
        self,
        url: str,
        dest: Path,
        filename: str | None = None,
    ) -> Optional[Path]:
        """带重试的下载逻辑。"""
        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._do_download(url, dest, filename)
            except (httpx.HTTPError, httpx.StreamError, IOError) as e:
                last_error = e
                logger.warning(
                    f"下载失败 (尝试 {attempt}/{self._max_retries}): {url} - {e}"
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"下载最终失败: {url} - {last_error}")
        return None

    async def _do_download(
        self,
        url: str,
        dest: Path,
        filename: str | None = None,
    ) -> Path:
        """执行实际下载。"""
        client = await self._get_client()

        async with client.stream("GET", url) as response:
            response.raise_for_status()

            # 检查文件大小
            content_length = response.headers.get("content-length")
            if content_length and self._max_file_size > 0:
                if int(content_length) > self._max_file_size:
                    raise IOError(
                        f"文件过大: {int(content_length)} bytes > {self._max_file_size} bytes"
                    )

            # 推断文件名
            if not filename:
                filename = self._extract_filename(url, response.headers)

            dest.mkdir(parents=True, exist_ok=True)
            file_path = dest / filename

            # 避免文件名冲突
            file_path = self._resolve_conflict(file_path)

            # 流式写入文件
            async with aiofiles.open(file_path, "wb") as f:
                downloaded = 0
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    downloaded += len(chunk)
                    if self._max_file_size > 0 and downloaded > self._max_file_size:
                        raise IOError("下载过程中超出文件大小限制")
                    await f.write(chunk)

            return file_path

    @staticmethod
    def _extract_filename(url: str, headers: httpx.Headers) -> str:
        """从 URL 或 Content-Disposition 头提取文件名。"""
        # 尝试 Content-Disposition
        cd = headers.get("content-disposition", "")
        if "filename=" in cd:
            # 提取 filename*=UTF-8''name 或 filename="name"
            for part in cd.split(";"):
                part = part.strip()
                if part.startswith("filename="):
                    name = part.split("=", 1)[1].strip("\"' ")
                    # 处理 RFC 5987 编码
                    if part.startswith("filename*="):
                        encoding, _, encoded_name = part.split("=", 1)[1].split("'", 2)
                        import urllib.parse
                        name = urllib.parse.unquote(encoded_name, encoding=encoding.lower())
                    if name:
                        return name

        # 从 URL 路径提取
        from urllib.parse import urlparse
        path = urlparse(url).path
        name = path.rstrip("/").split("/")[-1]
        if name:
            return name

        return "unknown_file"

    @staticmethod
    def _resolve_conflict(file_path: Path) -> Path:
        """处理文件名冲突，在文件名后添加序号。"""
        if not file_path.exists():
            return file_path

        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        counter = 1

        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
