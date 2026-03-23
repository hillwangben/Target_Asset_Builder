"""存储管理 - 按国家/类型/型号/传感器组织目录结构"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Optional

from src.models import MediaType, SensorType

logger = logging.getLogger(__name__)

# 文件名清理正则：移除不安全字符
_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class StorageManager:
    """存储管理器，负责目录创建和文件存储。"""

    def __init__(self, root_dir: str = "./data"):
        self._root = Path(root_dir).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def get_asset_dir(
        self,
        country: str,
        target_type: str,
        model: str,
        sensor: SensorType = SensorType.UNKNOWN,
    ) -> Path:
        """获取资产的存储目录。

        目录结构: {root}/{type}/{country}/{model}/{sensor}/
        """
        sensor_dir = sensor.value if sensor != SensorType.UNKNOWN else "unknown"
        return self._root / target_type / country / model / sensor_dir

    def get_media_subdir(
        self,
        asset_dir: Path,
        media_type: MediaType,
    ) -> Path:
        """获取媒体子目录（images/videos/audio）。"""
        subdir_map = {
            MediaType.IMAGE: "images",
            MediaType.VIDEO: "videos",
            MediaType.AUDIO: "audio",
        }
        return asset_dir / subdir_map.get(media_type, "other")

    def prepare_dir(self, dir_path: Path) -> None:
        """创建目录（如果不存在）。"""
        dir_path.mkdir(parents=True, exist_ok=True)

    def store_file(
        self,
        src_file: Path,
        country: str,
        target_type: str,
        model: str,
        sensor: SensorType,
        media_type: MediaType,
    ) -> Path:
        """将文件存储到分类目录中。

        Args:
            src_file: 源文件路径
            country: 国家
            target_type: 目标类型
            model: 型号
            sensor: 传感器类型
            media_type: 媒体类型

        Returns:
            存储后的文件路径
        """
        asset_dir = self.get_asset_dir(country, target_type, model, sensor)
        media_dir = self.get_media_subdir(asset_dir, media_type)
        self.prepare_dir(media_dir)

        # 清理文件名
        safe_name = self._safe_filename(src_file.name)
        dest = media_dir / safe_name

        # 处理文件名冲突
        dest = self._resolve_conflict(dest)

        shutil.move(str(src_file), str(dest))
        logger.debug(f"文件已存储: {dest}")
        return dest

    def remove_file(self, file_path: Path) -> None:
        """删除文件（用于分辨率过滤后清理不符合条件的文件）。"""
        try:
            file_path.unlink(missing_ok=True)
            logger.debug(f"已删除文件: {file_path}")
        except OSError as e:
            logger.warning(f"删除文件失败 {file_path}: {e}")

    def get_relative_path(self, file_path: Path) -> str:
        """获取相对于根目录的路径。"""
        try:
            return str(file_path.relative_to(self._root))
        except ValueError:
            return str(file_path)

    def ensure_root(self) -> None:
        """确保根目录存在。"""
        self._root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_filename(name: str) -> str:
        """清理文件名中的不安全字符。"""
        name = _UNSAFE_CHARS.sub("_", name)
        # 限制文件名长度
        if len(name) > 200:
            stem = Path(name).stem[:190]
            suffix = Path(name).suffix
            name = f"{stem}{suffix}"
        return name

    @staticmethod
    def _resolve_conflict(file_path: Path) -> Path:
        """处理文件名冲突。"""
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
