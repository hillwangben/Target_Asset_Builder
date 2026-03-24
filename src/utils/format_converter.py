"""格式转换器 - 将非主流格式转换为主流格式"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from src.models import MediaType

logger = logging.getLogger(__name__)

# 主流格式定义
MAIN_STREAM_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp", "gif"}
MAIN_STREAM_VIDEO_FORMATS = {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"}
MAIN_STREAM_AUDIO_FORMATS = {"mp3", "wav", "flac", "aac", "ogg", "m4a"}

# 格式映射：需要转换的格式 -> 目标格式
IMAGE_CONVERSION_MAP = {
    "heic": "jpg",
    "heif": "jpg",
    "tiff": "jpg",
    "tif": "jpg",
    "jfif": "jpg",
    "bmp": "jpg",
    "gif": "jpg",  # 转为jpg会丢失动画
    "ico": "png",
    "svg": "png",  # SVG是矢量图，转为png
    "raw": "jpg",
    "cr2": "jpg",
    "nef": "jpg",
    "arw": "jpg",
}

VIDEO_CONVERSION_MAP = {
    "webm": "mp4",
    "flv": "mp4",
    "avi": "mp4",
    "mkv": "mp4",
    "mov": "mp4",
    "wmv": "mp4",
    "3gp": "mp4",
    "m4v": "mp4",
}

AUDIO_CONVERSION_MAP = {
    "wav": "mp3",
    "flac": "mp3",
    "aac": "ogg",
    "m4a": "mp3",
    "wma": "mp3",
    "aiff": "mp3",
    "opus": "mp3",
}


def get_media_type_from_extension(ext: str) -> Optional[MediaType]:
    """根据文件扩展名判断媒体类型。"""
    ext = ext.lower().lstrip(".")
    if ext in MAIN_STREAM_IMAGE_FORMATS or ext in IMAGE_CONVERSION_MAP:
        return MediaType.IMAGE
    if ext in MAIN_STREAM_VIDEO_FORMATS or ext in VIDEO_CONVERSION_MAP:
        return MediaType.VIDEO
    if ext in MAIN_STREAM_AUDIO_FORMATS or ext in AUDIO_CONVERSION_MAP:
        return MediaType.AUDIO
    return None


def is_main_stream_format(filename: str, media_type: MediaType) -> bool:
    """检查文件格式是否为主流格式。"""
    ext = Path(filename).suffix.lower().lstrip(".")

    if media_type == MediaType.IMAGE:
        return ext in MAIN_STREAM_IMAGE_FORMATS
    elif media_type == MediaType.VIDEO:
        return ext in MAIN_STREAM_VIDEO_FORMATS
    elif media_type == MediaType.AUDIO:
        return ext in MAIN_STREAM_AUDIO_FORMATS

    return False


def get_target_format(media_type: MediaType, target_format: str) -> str:
    """获取目标格式。"""
    return target_format.lower().lstrip(".")


class FormatConverter:
    """格式转换器。"""

    def __init__(
        self,
        normalize: bool = True,
        image_format: str = "jpg",
        video_format: str = "mp4",
        audio_format: str = "mp3",
    ):
        self.normalize = normalize
        self.image_format = image_format.lower()
        self.video_format = video_format.lower()
        self.audio_format = audio_format.lower()

    def should_convert(self, file_path: Path, media_type: MediaType) -> bool:
        """检查文件是否需要转换格式。"""
        if not self.normalize:
            return False

        ext = file_path.suffix.lower().lstrip(".")

        if media_type == MediaType.IMAGE:
            return ext not in MAIN_STREAM_IMAGE_FORMATS
        elif media_type == MediaType.VIDEO:
            return ext not in MAIN_STREAM_VIDEO_FORMATS
        elif media_type == MediaType.AUDIO:
            return ext not in MAIN_STREAM_AUDIO_FORMATS

        return False

    def convert(self, file_path: Path, media_type: MediaType) -> Optional[Path]:
        """转换文件格式。

        Args:
            file_path: 源文件路径
            media_type: 媒体类型

        Returns:
            转换后的文件路径，失败返回 None
        """
        if not self.should_convert(file_path, media_type):
            return file_path

        try:
            if media_type == MediaType.IMAGE:
                return self._convert_image(file_path)
            elif media_type == MediaType.VIDEO:
                return self._convert_video(file_path)
            elif media_type == MediaType.AUDIO:
                return self._convert_audio(file_path)
        except Exception as e:
            logger.error(f"格式转换失败 {file_path}: {e}")
            return None

        return None

    def _convert_image(self, file_path: Path) -> Optional[Path]:
        """转换图片格式。"""
        from PIL import Image

        target_ext = f".{self.image_format}"
        output_path = file_path.with_suffix(target_ext)

        # 如果输出文件已存在，先删除
        if output_path.exists():
            output_path.unlink()

        try:
            with Image.open(file_path) as img:
                # 处理 RGBA 模式转为 JPG
                if self.image_format in ("jpg", "jpeg") and img.mode in ("RGBA", "LA", "P"):
                    # 转为 RGB
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = rgb_img

                # 保存为目标格式
                save_format = "JPEG" if self.image_format in ("jpg", "jpeg") else self.image_format.upper()
                img.save(output_path, format=save_format)

            # 删除原文件
            file_path.unlink()
            logger.info(f"图片格式转换成功: {file_path.name} -> {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"图片格式转换失败: {e}")
            # 转换失败时保留原文件
            if output_path.exists():
                output_path.unlink()
            return None

    def _convert_video(self, file_path: Path) -> Optional[Path]:
        """转换视频格式（需要 ffmpeg）。"""
        output_path = file_path.with_suffix(f".{self.video_format}")

        # 如果输出文件已存在，先删除
        if output_path.exists():
            output_path.unlink()

        try:
            # 使用 ffmpeg 转换
            cmd = [
                "ffmpeg",
                "-y",  # 覆盖输出文件
                "-i", str(file_path),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                str(output_path),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg 转换失败: {result.stderr}")
                return None

            # 删除原文件
            file_path.unlink()
            logger.info(f"视频格式转换成功: {file_path.name} -> {output_path.name}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error("视频转换超时")
            return None
        except FileNotFoundError:
            logger.warning("ffmpeg 未安装，跳过视频格式转换")
            return file_path
        except Exception as e:
            logger.error(f"视频格式转换失败: {e}")
            return None

    def _convert_audio(self, file_path: Path) -> Optional[Path]:
        """转换音频格式（需要 ffmpeg）。"""
        output_path = file_path.with_suffix(f".{self.audio_format}")

        # 如果输出文件已存在，先删除
        if output_path.exists():
            output_path.unlink()

        try:
            # 使用 ffmpeg 转换
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(file_path),
                "-codec:a", "libmp3lame" if self.audio_format == "mp3" else "copy",
                str(output_path),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3分钟超时
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg 转换失败: {result.stderr}")
                return None

            # 删除原文件
            file_path.unlink()
            logger.info(f"音频格式转换成功: {file_path.name} -> {output_path.name}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error("音频转换超时")
            return None
        except FileNotFoundError:
            logger.warning("ffmpeg 未安装，跳过音频格式转换")
            return file_path
        except Exception as e:
            logger.error(f"音频格式转换失败: {e}")
            return None
