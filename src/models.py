"""核心数据模型定义"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────── 枚举定义 ────────────────────


class TargetType(str, enum.Enum):
    """目标类型"""
    AIRPLANE = "airplane"
    SHIP = "ship"
    VEHICLE = "vehicle"
    SATELLITE = "satellite"
    MISSILE = "missile"
    RADAR = "radar"


class SensorType(str, enum.Enum):
    """传感器类型"""
    VISIBLE = "visible"
    IR = "ir"
    SAR = "sar"
    REMOTE_SENSING = "remote_sensing"
    UNKNOWN = "unknown"


class MediaType(str, enum.Enum):
    """媒体类型"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class SourceType(str, enum.Enum):
    """数据源类型"""
    GITHUB = "github"
    URL = "url"


# ──────────────────── 数据模型 ────────────────────


class Resolution(BaseModel):
    """分辨率信息"""
    width: int = Field(description="宽度（像素）")
    height: int = Field(description="高度（像素）")


class SourceInfo(BaseModel):
    """数据来源信息"""
    type: SourceType
    repo: Optional[str] = None
    url: str


class AssetMeta(BaseModel):
    """资产元信息"""
    id: str = Field(description="文件 SHA-256 哈希值")
    country: str = Field(description="国家/地区")
    type: TargetType = Field(description="目标类型")
    model: str = Field(description="型号")
    sensor: SensorType = Field(default=SensorType.UNKNOWN, description="传感器类型")
    media_type: MediaType = Field(description="媒体类型")
    format: str = Field(description="文件格式（如 jpg, mp4, wav）")
    resolution: Optional[Resolution] = Field(default=None, description="分辨率（图片/视频）")
    file_path: str = Field(description="本地存储路径")
    file_size: int = Field(description="文件大小（字节）")
    source: SourceInfo = Field(description="数据来源")
    collected_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="采集时间 (ISO 8601)",
    )

    @property
    def min_dimension(self) -> Optional[int]:
        """返回宽高中较小的一个维度"""
        if self.resolution:
            return min(self.resolution.width, self.resolution.height)
        return None


class SearchResultItem(BaseModel):
    """搜索结果条目"""
    url: str = Field(description="资源下载 URL")
    filename: str = Field(description="文件名")
    media_type: MediaType = Field(default=MediaType.IMAGE, description="媒体类型")
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    preview_url: Optional[str] = Field(default=None, description="预览 URL")
    extra: dict = Field(default_factory=dict, description="额外信息")


class CollectionTask(BaseModel):
    """采集任务"""
    country: str = Field(default="ALL", description="国家/地区")
    type: TargetType = Field(default=TargetType.AIRPLANE, description="目标类型")
    model: str = Field(default="ALL", description="型号")
    sensor: SensorType = Field(default=SensorType.UNKNOWN, description="传感器类型")
    keywords: list[str] = Field(description="搜索关键词列表")
    source: str = Field(default="github", description="数据源名称")
    max_count: Optional[int] = Field(default=None, description="最大采集数量，None表示不限制")
    max_duration_seconds: Optional[int] = Field(default=None, description="最大采集时长（秒），None表示不限制")

    @property
    def display_name(self) -> str:
        return f"{self.country}/{self.type.value}/{self.model}"


class CollectionStats(BaseModel):
    """采集统计"""
    total_files: int = 0
    total_size: int = 0
    by_country: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_media: dict[str, int] = Field(default_factory=dict)
    skipped: int = 0
    failed: int = 0
    stop_reason: Optional[str] = Field(default=None, description="停止原因（如达到数量或时间限制）")
