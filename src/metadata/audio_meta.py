"""音频元信息提取"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """音频元信息"""
    duration: float  # 秒
    sample_rate: int
    channels: int
    bitrate: int  # bps
    format: str


def extract_audio_metadata(file_path: Path | str) -> Optional[AudioMetadata]:
    """提取音频文件的元信息。

    Args:
        file_path: 音频文件路径

    Returns:
        AudioMetadata 或 None（提取失败时）
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return None

    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(str(file_path))

        if audio is None:
            logger.debug(f"无法解析音频文件: {file_path}")
            return None

        info = audio.info  # type: ignore

        duration = info.length if hasattr(info, "length") else 0.0
        sample_rate = info.sample_rate if hasattr(info, "sample_rate") else 0
        channels = info.channels if hasattr(info, "channels") else 0
        bitrate = info.bitrate if hasattr(info, "bitrate") else 0
        suffix = file_path.suffix.lower().lstrip(".")

        return AudioMetadata(
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            bitrate=bitrate,
            format=suffix,
        )
    except ImportError:
        logger.warning("mutagen 未安装，无法提取音频元信息")
        return None
    except Exception as e:
        logger.debug(f"无法读取音频元信息 {file_path}: {e}")
        return None
