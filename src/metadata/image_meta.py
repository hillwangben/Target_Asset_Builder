"""图像元信息提取"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """图像元信息"""
    width: int
    height: int
    format: str
    mode: str  # 色彩模式，如 RGB, L, RGBA


def extract_image_metadata(file_path: Path | str) -> Optional[ImageMetadata]:
    """提取图像文件的元信息。

    Args:
        file_path: 图像文件路径

    Returns:
        ImageMetadata 或 None（提取失败时）
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return None

    try:
        with Image.open(file_path) as img:
            return ImageMetadata(
                width=img.width,
                height=img.height,
                format=img.format or "unknown",
                mode=img.mode,
            )
    except Exception as e:
        logger.debug(f"无法读取图像元信息 {file_path}: {e}")
        return None
