"""存储管理测试"""

import pytest
from pathlib import Path

from src.storage import StorageManager
from src.models import MediaType, SensorType


@pytest.fixture
def temp_root(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def storage(temp_root):
    return StorageManager(str(temp_root))


class TestStorageManager:
    def test_root_dir(self, storage, temp_root):
        assert storage.root == temp_root.resolve()

    def test_get_asset_dir(self, storage, temp_root):
        asset_dir = storage.get_asset_dir("USA", "airplane", "F-22", SensorType.VISIBLE)
        expected = temp_root.resolve() / "airplane" / "USA" / "F-22" / "visible"
        assert asset_dir == expected

    def test_get_asset_dir_unknown_sensor(self, storage, temp_root):
        asset_dir = storage.get_asset_dir("USA", "airplane", "F-22")
        expected = temp_root.resolve() / "airplane" / "USA" / "F-22" / "unknown"
        assert asset_dir == expected

    def test_get_media_subdir(self, storage):
        asset_dir = Path("/data/airplane/USA/F-22/visible")
        assert storage.get_media_subdir(asset_dir, MediaType.IMAGE) == asset_dir / "images"
        assert storage.get_media_subdir(asset_dir, MediaType.VIDEO) == asset_dir / "videos"
        assert storage.get_media_subdir(asset_dir, MediaType.AUDIO) == asset_dir / "audio"

    def test_prepare_dir(self, storage, temp_root):
        target = temp_root / "a" / "b" / "c"
        storage.prepare_dir(target)
        assert target.exists()
        assert target.is_dir()

    def test_store_file(self, storage, temp_root):
        # 创建源文件
        src_dir = tmp_path_bak = temp_root / "src"
        src_dir.mkdir(parents=True)
        src_file = src_dir / "test_image.jpg"
        src_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        stored = storage.store_file(
            src_file, "USA", "airplane", "F-22", SensorType.VISIBLE, MediaType.IMAGE
        )

        assert stored.exists()
        assert not src_file.exists()  # 源文件应被移动
        assert "images" in str(stored)

    def test_safe_filename(self):
        assert StorageManager._safe_filename('normal.jpg') == 'normal.jpg'
        assert StorageManager._safe_filename('file<with>bad:chars.jpg') == 'file_with_bad_chars.jpg'
        assert StorageManager._safe_filename('a' * 250 + '.jpg') is not None
        # 确保不会太长
        name = StorageManager._safe_filename('a' * 250 + '.jpg')
        assert len(name) <= 200

    def test_ensure_root(self, storage, temp_root):
        storage.ensure_root()
        assert temp_root.resolve().exists()

    def test_get_relative_path(self, storage, temp_root):
        rel = storage.get_relative_path(temp_root / "airplane" / "USA" / "F-22")
        assert rel == str(Path("airplane") / "USA" / "F-22")

    def test_remove_file(self, storage, tmp_path):
        f = tmp_path / "to_remove.txt"
        f.write_text("test")
        storage.remove_file(f)
        assert not f.exists()

    def test_remove_nonexistent(self, storage, tmp_path):
        f = tmp_path / "nonexistent.txt"
        storage.remove_file(f)  # 不应抛出异常
