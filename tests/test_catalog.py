"""目录索引管理测试"""

import json
import tempfile
from pathlib import Path

import pytest

from src.catalog import CatalogManager
from src.models import AssetMeta, MediaType, Resolution, SensorType, SourceInfo, SourceType, TargetType


@pytest.fixture
def temp_dir(tmp_path):
    """创建临时目录。"""
    return tmp_path


@pytest.fixture
def catalog(temp_dir):
    """创建 CatalogManager 实例。"""
    return CatalogManager(str(temp_dir), "catalog.json")


@pytest.fixture
def sample_asset():
    """创建示例资产数据。"""
    return AssetMeta(
        id="abc123def456",
        country="USA",
        type=TargetType.AIRPLANE,
        model="F-22",
        sensor=SensorType.VISIBLE,
        media_type=MediaType.IMAGE,
        format="jpg",
        resolution=Resolution(width=1920, height=1080),
        file_path="airplane/USA/F-22/visible/images/f22_001.jpg",
        file_size=204800,
        source=SourceInfo(type=SourceType.GITHUB, url="https://example.com/f22.jpg", repo="test/repo"),
    )


class TestCatalogManager:
    def test_load_empty(self, catalog, temp_dir):
        catalog.load()
        assert catalog.assets == []

    def test_add_asset(self, catalog, sample_asset):
        catalog.load()
        result = catalog.add_asset(sample_asset)
        assert result is True
        assert len(catalog.assets) == 1

    def test_add_duplicate(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)
        result = catalog.add_asset(sample_asset)
        assert result is False
        assert len(catalog.assets) == 1

    def test_exists(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)
        assert catalog.exists("abc123def456") is True
        assert catalog.exists("nonexistent") is False

    def test_exists_url(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)
        assert catalog.exists_url("https://example.com/f22.jpg") is True
        assert catalog.exists_url("https://example.com/other.jpg") is False

    def test_save_and_reload(self, catalog, sample_asset, temp_dir):
        catalog.load()
        catalog.add_asset(sample_asset)
        catalog.save()

        # 重新加载
        catalog2 = CatalogManager(str(temp_dir), "catalog.json")
        catalog2.load()
        assert len(catalog2.assets) == 1
        assert catalog2.assets[0]["id"] == "abc123def456"

    def test_save_creates_file(self, catalog, sample_asset, temp_dir):
        catalog.load()
        catalog.add_asset(sample_asset)
        catalog.save()

        catalog_file = temp_dir / "catalog.json"
        assert catalog_file.exists()

        data = json.loads(catalog_file.read_text())
        assert data["version"] == "1.0"
        assert len(data["assets"]) == 1
        assert data["stats"]["total_files"] == 1

    def test_get_stats(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)
        stats = catalog.get_stats()

        assert stats.total_files == 1
        assert stats.total_size == 204800
        assert stats.by_country["USA"] == 1
        assert stats.by_type["airplane"] == 1
        assert stats.by_media["image"] == 1

    def test_get_assets_by_filter(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)

        # 按国家过滤
        results = catalog.get_assets_by_filter(country="USA")
        assert len(results) == 1

        results = catalog.get_assets_by_filter(country="China")
        assert len(results) == 0

        # 按类型过滤
        results = catalog.get_assets_by_filter(target_type="airplane")
        assert len(results) == 1

    def test_remove_asset(self, catalog, sample_asset):
        catalog.load()
        catalog.add_asset(sample_asset)
        assert len(catalog.assets) == 1

        result = catalog.remove_asset("abc123def456")
        assert result is True
        assert len(catalog.assets) == 0

    def test_atomic_write(self, catalog, sample_asset, temp_dir):
        catalog.load()
        catalog.add_asset(sample_asset)
        catalog.save()

        # 确保没有残留的临时文件
        tmp_files = list(temp_dir.glob("catalog_*.tmp"))
        assert len(tmp_files) == 0
