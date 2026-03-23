"""分辨率过滤器 - 检查图片和视频是否满足分辨率要求"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.models import MediaType, Resolution

logger = logging.getLogger(__name__)


class ResolutionFilter:
    """分辨率过滤器。"""

    def __init__(
        self,
        enabled: bool = True,
        min_width: int = 0,
        min_height: int = 0,
        min_dimension: int = 0,
    ):
        self.enabled = enabled
        self.min_width = min_width
        self.min_height = min_height
        self.min_dimension = min_dimension

    def check(
        self,
        media_type: MediaType,
        resolution: Optional[Resolution],
    ) -> bool:
        """检查分辨率是否满足要求。

        Args:
            media_type: 媒体类型（仅检查 image 和 video）
            resolution: 分辨率信息

        Returns:
            True 表示通过过滤（保留），False 表示应跳过
        """
        if not self.enabled:
            return True

        # 音频文件不需要分辨率检查
        if media_type == MediaType.AUDIO:
            return True

        if resolution is None:
            # 无法获取分辨率时，如果启用了过滤则跳过
            if self.min_width > 0 or self.min_height > 0 or self.min_dimension > 0:
                logger.debug("无法获取分辨率，跳过文件")
                return False
            return True

        w, h = resolution.width, resolution.height

        if self.min_width > 0 and w < self.min_width:
            logger.debug(f"宽度过低: {w} < {self.min_width}")
            return False

        if self.min_height > 0 and h < self.min_height:
            logger.debug(f"高度过低: {h} < {self.min_height}")
            return False

        if self.min_dimension > 0:
            min_dim = min(w, h)
            if min_dim < self.min_dimension:
                logger.debug(f"最小维度过低: {min_dim} < {self.min_dimension}")
                return False

        return True

    def check_file(self, file_path: Path, media_type: MediaType) -> tuple[bool, Optional[Resolution]]:
        """检查文件分辨率。

        Args:
            file_path: 文件路径
            media_type: 媒体类型

        Returns:
            (是否通过, 分辨率信息)
        """
        resolution = self._extract_resolution(file_path, media_type)
        passed = self.check(media_type, resolution)
        return passed, resolution

    @staticmethod
    def _extract_resolution(file_path: Path, media_type: MediaType) -> Optional[Resolution]:
        """从文件中提取分辨率信息。"""
        try:
            if media_type == MediaType.IMAGE:
                from src.metadata.image_meta import extract_image_metadata
                meta = extract_image_metadata(file_path)
                if meta:
                    return Resolution(width=meta.width, height=meta.height)

            elif media_type == MediaType.VIDEO:
                from src.metadata.video_meta import extract_video_metadata
                meta = extract_video_metadata(file_path)
                if meta:
                    return Resolution(width=meta.width, height=meta.height)

        except Exception as e:
            logger.debug(f"提取分辨率失败 {file_path}: {e}")

        return None
