"""配置加载与校验"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """存储配置"""
    root_dir: str = "./data"
    catalog_file: str = "catalog.json"


class GitHubSourceConfig(BaseModel):
    """GitHub 数据源配置"""
    token: str = ""
    per_page: int = 30
    max_pages: int = 5


class UrlSourceConfig(BaseModel):
    """URL 数据源配置"""
    timeout: int = 30
    max_retries: int = 3


class WebSourceConfig(BaseModel):
    """网页搜索数据源配置"""
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = ""


class HuggingFaceSourceConfig(BaseModel):
    """HuggingFace 数据源配置"""
    timeout: int = 30
    max_retries: int = 3


class MultiSourceConfig(BaseModel):
    """多源采集配置"""
    enabled_sources: list[str] = Field(
        default_factory=lambda: ["github", "web"],
        description="启用的数据源列表"
    )
    parallel_search: bool = Field(
        default=True,
        description="是否并行搜索多个数据源"
    )


class SourcesConfig(BaseModel):
    """数据源配置"""
    github: GitHubSourceConfig = Field(default_factory=GitHubSourceConfig)
    url: UrlSourceConfig = Field(default_factory=UrlSourceConfig)
    web: WebSourceConfig = Field(default_factory=WebSourceConfig)
    huggingface: HuggingFaceSourceConfig = Field(default_factory=HuggingFaceSourceConfig)
    multi: MultiSourceConfig = Field(default_factory=MultiSourceConfig)


class DownloadConfig(BaseModel):
    """下载配置"""
    concurrency: int = 5
    max_file_size_mb: int = 100
    timeout: int = 120
    max_retries: int = 3


class ResolutionFilterConfig(BaseModel):
    """分辨率过滤配置"""
    enabled: bool = True
    min_width: int = 0
    min_height: int = 0
    min_dimension: int = 0


class FiltersConfig(BaseModel):
    """过滤配置"""
    resolution: ResolutionFilterConfig = Field(default_factory=ResolutionFilterConfig)


class LimitsConfig(BaseModel):
    """采集限制配置"""
    default_max_count: Optional[int] = Field(default=None, description="默认最大采集数量")
    default_max_duration: Optional[int] = Field(default=None, description="默认最大采集时长（秒）")


class CategoriesConfig(BaseModel):
    """分类规则配置"""
    types: list[str] = Field(default_factory=lambda: [
        "airplane", "ship", "vehicle", "satellite", "missile", "radar"
    ])
    sensors: list[str] = Field(default_factory=lambda: [
        "visible", "ir", "sar", "remote_sensing"
    ])
    media_types: list[str] = Field(default_factory=lambda: [
        "image", "video", "audio"
    ])


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = ""


class FormatConfig(BaseModel):
    """格式规范化配置"""
    normalize: bool = Field(default=True, description="是否启用格式规范化")
    image_format: str = Field(default="jpg", description="图片目标格式")
    video_format: str = Field(default="mp4", description="视频目标格式")
    audio_format: str = Field(default="mp3", description="音频目标格式")


class ValidationConfig(BaseModel):
    """合法性校验配置"""
    enabled: bool = Field(default=True, description="是否启用校验")
    check_integrity: bool = Field(default=True, description="文件完整性校验")
    check_safety: bool = Field(default=True, description="内容安全校验（魔术字节）")
    check_mime_type: bool = Field(default=True, description="MIME类型一致性校验")
    min_audio_duration: int = Field(default=0, description="最小音频时长（秒）")


class AppConfig(BaseModel):
    """全局应用配置"""
    storage: StorageConfig = Field(default_factory=StorageConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    categories: CategoriesConfig = Field(default_factory=CategoriesConfig)
    format: FormatConfig = Field(default_factory=FormatConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


_DEFAULT_CONFIG_PATHS = [
    Path("config.yaml"),
    Path("~/.config/target-asset-builder/config.yaml").expanduser(),
]


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载配置文件，返回校验后的 AppConfig 实例。

    Args:
        config_path: 配置文件路径。为 None 时按默认路径列表依次查找。

    Returns:
        AppConfig 实例
    """
    path: Optional[Path] = None

    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
    else:
        for candidate in _DEFAULT_CONFIG_PATHS:
            if candidate.exists():
                path = candidate
                break

    if path is None:
        return AppConfig()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return AppConfig.model_validate(raw)
