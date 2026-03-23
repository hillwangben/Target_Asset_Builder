"""数据源模块"""

from src.sources.base import DataSource
from src.sources.github_source import GitHubSource
from src.sources.url_source import UrlSource
from src.sources.web_source import WebSearchSource
from src.sources.huggingface_source import HuggingFaceSource
from src.sources.multi_source import MultiSourceCollector

__all__ = [
    "DataSource",
    "GitHubSource",
    "UrlSource",
    "WebSearchSource",
    "HuggingFaceSource",
    "MultiSourceCollector",
]
