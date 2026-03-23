"""视频元信息提取"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """视频元信息"""
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float  # 秒
    codec: str
    format: str


def extract_video_metadata(file_path: Path | str) -> Optional[VideoMetadata]:
    """提取视频文件的元信息。

    Args:
        file_path: 视频文件路径

    Returns:
        VideoMetadata 或 None（提取失败时）
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return None

    try:
        import cv2

        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            logger.debug(f"无法打开视频文件: {file_path}")
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0.0
        codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = (
            "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
            if codec_int > 0
            else "unknown"
        )
        cap.release()

        suffix = file_path.suffix.lower().lstrip(".")
        return VideoMetadata(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration=duration,
            codec=codec,
            format=suffix,
        )
    except ImportError:
        logger.warning("opencv-python 未安装，无法提取视频元信息")
        return None
    except Exception as e:
        logger.debug(f"无法读取视频元信息 {file_path}: {e}")
        return None
