"""文件合法性校验器"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.models import MediaType

logger = logging.getLogger(__name__)


# 魔术字节映射：媒体类型 -> [(magic_bytes, description)]
MAGIC_BYTES_MAP = {
    MediaType.IMAGE: [
        (b"\xff\xd8\xff", "JPEG"),
        (b"\x89PNG\r\n\x1a\n", "PNG"),
        (b"GIF87a", "GIF"),
        (b"GIF89a", "GIF"),
        (b"RIFF", "WEBP/WAV/AVI"),  # 需要进一步检查
        (b"BM", "BMP"),
        (b"\x00\x00\x01\x00", "ICO"),
        (b"\x00\x00\x02\x00", "CUR"),
    ],
    MediaType.VIDEO: [
        (b"\x00\x00\x00\x18ftypmp4", "MP4"),
        (b"\x00\x00\x00\x1cftypisom", "MP4"),
        (b"\x00\x00\x00\x20ftypMSNV", "MP4"),
        (b"RIFF", "AVI/WAV/WEBP"),
        (b"\x1aE\xdf\xa3", "MKV"),
        (b"FLV", "FLV"),
        (b"\x00\x00\x00\x14ftyp", "MOV/MP4"),
    ],
    MediaType.AUDIO: [
        (b"ID3", "MP3"),
        (b"\xff\xfb", "MP3"),
        (b"\xff\xf3", "MP3"),
        (b"\xff\xf2", "MP3"),
        (b"RIFF", "WAV/AVI/WEBP"),
        (b"fLaC", "FLAC"),
        (b"OggS", "OGG"),
        (b"ftypM4A", "M4A/AAC"),
    ],
}

# 可疑文件头（恶意文件常见特征）
SUSPICIOUS_PATTERNS = [
    b"<script",  # JavaScript 注入
    b"<?php",  # PHP 脚本
    b"<!DOCTYPE html",  # HTML 注入
    b"<html",  # HTML 注入
    b"eval(",  # JavaScript eval
    b"base64",  # base64 编码内容
    b"MZ",  # PE 可执行文件
    b"\x4d\x5a",  # EXE/DLL (Windows)
    b"\x7fELF",  # ELF 可执行文件 (Linux)
    b"\xca\xfe\xba\xbe",  # Java class
    b"PK\x03\x04",  # ZIP 压缩包（可能是恶意软件）
]


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool
    detected_type: Optional[str] = None
    detected_media_type: Optional[MediaType] = None
    error: Optional[str] = None


class FileValidator:
    """文件合法性校验器。"""

    def __init__(
        self,
        enabled: bool = True,
        check_integrity: bool = True,
        check_safety: bool = True,
        check_mime_type: bool = True,
        min_audio_duration: int = 0,
    ):
        self.enabled = enabled
        self.check_integrity = check_integrity
        self.check_safety = check_safety
        self.check_mime_type = check_mime_type
        self.min_audio_duration = min_audio_duration

    def validate(
        self,
        file_path: Path,
        media_type: MediaType,
        expected_mime_type: Optional[str] = None,
    ) -> ValidationResult:
        """校验文件合法性。

        Args:
            file_path: 文件路径
            media_type: 声明的媒体类型
            expected_mime_type: 期望的 MIME 类型

        Returns:
            ValidationResult
        """
        if not self.enabled:
            return ValidationResult(valid=True)

        # 完整性校验
        if self.check_integrity:
            result = self._check_integrity(file_path)
            if not result.valid:
                return result

        # 内容安全校验
        if self.check_safety:
            result = self._check_safety(file_path, media_type)
            if not result.valid:
                return result

        # MIME 类型一致性校验
        if self.check_mime_type and expected_mime_type:
            result = self._check_mime_consistency(file_path, media_type, expected_mime_type)
            if not result.valid:
                return result

        # 媒体类型一致性校验（文件内容是否匹配声明的类型）
        result = self._check_media_type_match(file_path, media_type)
        if not result.valid:
            return result

        return ValidationResult(valid=True)

    def _check_integrity(self, file_path: Path) -> ValidationResult:
        """检查文件完整性。"""
        if not file_path.exists():
            return ValidationResult(valid=False, error="文件不存在")

        if file_path.stat().st_size == 0:
            return ValidationResult(valid=False, error="文件为空")

        # 检查文件是否完整（尝试读取前几个字节）
        try:
            with open(file_path, "rb") as f:
                f.read(1)
        except IOError as e:
            return ValidationResult(valid=False, error=f"文件读取失败: {e}")

        return ValidationResult(valid=True)

    def _check_safety(self, file_path: Path, media_type: MediaType) -> ValidationResult:
        """检查文件内容安全（检测恶意文件）。"""
        try:
            # 读取文件头
            with open(file_path, "rb") as f:
                header = f.read(8192)  # 读取前 8KB

            # 检查可疑模式
            for pattern in SUSPICIOUS_PATTERNS:
                if pattern in header:
                    logger.warning(f"检测到可疑内容: {file_path}")
                    return ValidationResult(
                        valid=False,
                        error=f"检测到可疑内容模式",
                    )

            return ValidationResult(valid=True)

        except IOError as e:
            return ValidationResult(valid=False, error=f"安全检查失败: {e}")

    def _check_mime_consistency(
        self,
        file_path: Path,
        media_type: MediaType,
        expected_mime_type: str,
    ) -> ValidationResult:
        """检查 MIME 类型一致性。"""
        # 简单检查：文件扩展名与 MIME 类型是否匹配
        ext = file_path.suffix.lower().lstrip(".")

        mime_to_ext = {
            "image/jpeg": ["jpg", "jpeg"],
            "image/png": ["png"],
            "image/gif": ["gif"],
            "image/webp": ["webp"],
            "image/bmp": ["bmp"],
            "video/mp4": ["mp4"],
            "video/mpeg": ["mpg", "mpeg"],
            "video/webm": ["webm"],
            "audio/mpeg": ["mp3"],
            "audio/wav": ["wav"],
            "audio/flac": ["flac"],
        }

        expected_exts = mime_to_ext.get(expected_mime_type.lower(), [])
        if expected_exts and ext not in expected_exts:
            logger.warning(
                f"MIME类型不匹配: 期望 {expected_mime_type}, 文件扩展名为 {ext}"
            )
            # 不直接拒绝，仅记录警告

        return ValidationResult(valid=True)

    def _check_media_type_match(
        self,
        file_path: Path,
        media_type: MediaType,
    ) -> ValidationResult:
        """检查文件内容是否与声明的媒体类型匹配。"""
        try:
            detected_type, detected_media = self._detect_file_type(file_path)

            if detected_media is None:
                # 无法检测到类型，可能不是有效的媒体文件
                return ValidationResult(
                    valid=False,
                    error="无法识别文件类型",
                )

            # 检查是否匹配
            if detected_media != media_type:
                logger.warning(
                    f"媒体类型不匹配: 声明为 {media_type.value}, 实际检测为 {detected_media.value}"
                )
                return ValidationResult(
                    valid=False,
                    detected_type=detected_type,
                    detected_media_type=detected_media,
                    error=f"文件类型不匹配: 期望 {media_type.value}, 实际为 {detected_media.value}",
                )

            return ValidationResult(
                valid=True,
                detected_type=detected_type,
                detected_media_type=detected_media,
            )

        except Exception as e:
            logger.debug(f"媒体类型检测失败: {e}")
            return ValidationResult(valid=True)  # 检测失败不阻断

    def _detect_file_type(
        self,
        file_path: Path,
    ) -> tuple[Optional[str], Optional[MediaType]]:
        """通过魔术字节检测文件类型。

        Returns:
            (类型描述, 媒体类型)
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(32)

            if len(header) < 4:
                return None, None

            # 检查图片
            for magic, desc in MAGIC_BYTES_MAP.get(MediaType.IMAGE, []):
                if header.startswith(magic):
                    # 特殊处理 RIFF
                    if magic == b"RIFF":
                        if header[8:12] == b"WEBP":
                            return "WEBP", MediaType.IMAGE
                        continue
                    return desc, MediaType.IMAGE

            # 检查视频
            for magic, desc in MAGIC_BYTES_MAP.get(MediaType.VIDEO, []):
                if header.startswith(magic):
                    if magic == b"RIFF":
                        if header[8:12] == b"AVI ":
                            return "AVI", MediaType.VIDEO
                        continue
                    return desc, MediaType.VIDEO

            # 检查音频
            for magic, desc in MAGIC_BYTES_MAP.get(MediaType.AUDIO, []):
                if header.startswith(magic):
                    if magic == b"RIFF":
                        if header[8:12] == b"WAVE":
                            return "WAV", MediaType.AUDIO
                        continue
                    return desc, MediaType.AUDIO

            # 尝试通过扩展名判断
            ext = file_path.suffix.lower().lstrip(".")
            from src.utils.format_converter import get_media_type_from_extension
            media_type = get_media_type_from_extension(ext)
            if media_type:
                return ext.upper(), media_type

            return None, None

        except Exception as e:
            logger.debug(f"文件类型检测失败: {e}")
            return None, None


def check_audio_duration(file_path: Path, min_duration: int) -> bool:
    """检查音频文件时长是否满足要求。

    Args:
        file_path: 音频文件路径
        min_duration: 最小时长（秒）

    Returns:
        True 表示通过，False 表示不满足
    """
    if min_duration <= 0:
        return True

    try:
        # 尝试使用 mutagen 获取时长
        import mutagen
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        from mutagen.oggvorbis import OggVorbis
        from mutagen.wave import WAVE
        from mutagen.m4a import M4A

        ext = file_path.suffix.lower()

        audio = None
        if ext in (".mp3",):
            audio = MP3(file_path)
        elif ext in (".flac",):
            audio = FLAC(file_path)
        elif ext in (".ogg",):
            audio = OggVorbis(file_path)
        elif ext in (".wav",):
            audio = WAVE(file_path)
        elif ext in (".m4a", ".aac"):
            audio = M4A(file_path)

        if audio and hasattr(audio.info, "length"):
            duration = audio.info.length
            return duration >= min_duration

    except ImportError:
        logger.debug("mutagen 未安装，跳过音频时长检查")
    except Exception as e:
        logger.debug(f"音频时长检查失败: {e}")

    return True  # 检查失败时默认通过
