"""分辨率过滤器测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.filters.resolution import ResolutionFilter
from src.models import MediaType, Resolution


@pytest.fixture
def filter_enabled():
    return ResolutionFilter(
        enabled=True,
        min_width=640,
        min_height=480,
        min_dimension=0,
    )


@pytest.fixture
def filter_disabled():
    return ResolutionFilter(enabled=False)


@pytest.fixture
def filter_min_dim():
    return ResolutionFilter(
        enabled=True,
        min_width=0,
        min_height=0,
        min_dimension=800,
    )


class TestResolutionFilter:
    def test_disabled_filter_passes_all(self, filter_disabled):
        assert filter_disabled.check(MediaType.IMAGE, None) is True
        assert filter_disabled.check(MediaType.VIDEO, Resolution(width=1, height=1)) is True

    def test_audio_always_passes(self, filter_enabled):
        assert filter_enabled.check(MediaType.AUDIO, None) is True

    def test_no_resolution_with_filter_enabled(self, filter_enabled):
        assert filter_enabled.check(MediaType.IMAGE, None) is False

    def test_no_resolution_with_no_thresholds(self):
        f = ResolutionFilter(enabled=True, min_width=0, min_height=0, min_dimension=0)
        assert f.check(MediaType.IMAGE, None) is True

    def test_passes_sufficient_resolution(self, filter_enabled):
        res = Resolution(width=1920, height=1080)
        assert filter_enabled.check(MediaType.IMAGE, res) is True

    def test_fails_low_width(self, filter_enabled):
        res = Resolution(width=320, height=1080)
        assert filter_enabled.check(MediaType.IMAGE, res) is False

    def test_fails_low_height(self, filter_enabled):
        res = Resolution(width=1920, height=200)
        assert filter_enabled.check(MediaType.IMAGE, res) is False

    def test_passes_exact_resolution(self, filter_enabled):
        res = Resolution(width=640, height=480)
        assert filter_enabled.check(MediaType.IMAGE, res) is True

    def test_min_dimension_filter(self, filter_min_dim):
        # 1920x800 -> min dim = 800, passes
        assert filter_min_dim.check(MediaType.IMAGE, Resolution(width=1920, height=800)) is True
        # 1920x700 -> min dim = 700, fails
        assert filter_min_dim.check(MediaType.IMAGE, Resolution(width=1920, height=700)) is False

    def test_video_filtering(self, filter_enabled):
        res = Resolution(width=1920, height=1080)
        assert filter_enabled.check(MediaType.VIDEO, res) is True

    def test_check_file_nonexistent(self, filter_enabled):
        passed, res = filter_enabled.check_file(Path("/nonexistent/file.jpg"), MediaType.IMAGE)
        assert passed is False
        assert res is None
