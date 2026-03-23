"""采集流程集成测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.models import (
    CollectionTask,
    MediaType,
    SearchResultItem,
    SensorType,
    TargetType,
)


class TestCollectionTask:
    def test_display_name(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.display_name == "USA/airplane/F-22"

    def test_sensor_default(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.sensor == SensorType.UNKNOWN

    def test_source_default(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.source == "github"

    def test_max_count_limit(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
            max_count=100,
        )
        assert task.max_count == 100
        assert task.max_duration_seconds is None

    def test_max_duration_limit(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
            max_duration_seconds=300,
        )
        assert task.max_count is None
        assert task.max_duration_seconds == 300

    def test_both_limits(self):
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
            max_count=50,
            max_duration_seconds=180,
        )
        assert task.max_count == 50
        assert task.max_duration_seconds == 180


class TestSearchResultItem:
    def test_defaults(self):
        item = SearchResultItem(url="https://example.com/img.jpg", filename="img.jpg")
        assert item.media_type == MediaType.IMAGE
        assert item.file_size is None
        assert item.extra == {}
