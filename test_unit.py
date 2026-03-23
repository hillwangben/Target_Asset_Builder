#!/usr/bin/env python3
"""单元测试 - 不依赖 pytest"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    CollectionTask,
    MediaType,
    SearchResultItem,
    SensorType,
    TargetType,
)


class TestCollectionTask:
    """测试采集任务模型"""
    
    @staticmethod
    def test_display_name():
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.display_name == "USA/airplane/F-22", f"Expected USA/airplane/F-22, got {task.display_name}"
        return True
    
    @staticmethod
    def test_optional_parameters():
        """测试可选参数"""
        # 不指定国家、类型、型号
        task = CollectionTask(keywords=["test"])
        assert task.country == "ALL"
        assert task.type == TargetType.AIRPLANE
        assert task.model == "ALL"
        return True
    
    @staticmethod
    def test_sensor_default():
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.sensor == SensorType.UNKNOWN
        return True
    
    @staticmethod
    def test_source_default():
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
        )
        assert task.source == "github"
        return True
    
    @staticmethod
    def test_max_count_limit():
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
            max_count=100,
        )
        assert task.max_count == 100
        assert task.max_duration_seconds is None
        return True
    
    @staticmethod
    def test_max_duration_limit():
        task = CollectionTask(
            country="USA",
            type=TargetType.AIRPLANE,
            model="F-22",
            keywords=["F-22"],
            max_duration_seconds=300,
        )
        assert task.max_count is None
        assert task.max_duration_seconds == 300
        return True
    
    @staticmethod
    def test_both_limits():
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
        return True
    
    @staticmethod
    def test_partial_parameters():
        """测试部分参数"""
        # 仅指定国家
        task1 = CollectionTask(country="China", keywords=["naval"])
        assert task1.country == "China"
        assert task1.type == TargetType.AIRPLANE
        assert task1.model == "ALL"
        
        # 仅指定类型
        task2 = CollectionTask(type=TargetType.SHIP, keywords=["ship"])
        assert task2.country == "ALL"
        assert task2.type == TargetType.SHIP
        assert task2.model == "ALL"
        
        # 仅指定型号
        task3 = CollectionTask(model="F-22", keywords=["raptor"])
        assert task3.country == "ALL"
        assert task3.type == TargetType.AIRPLANE
        assert task3.model == "F-22"
        
        return True


class TestSearchResultItem:
    """测试搜索结果条目"""
    
    @staticmethod
    def test_defaults():
        item = SearchResultItem(url="https://example.com/img.jpg", filename="img.jpg")
        assert item.media_type == MediaType.IMAGE
        assert item.file_size is None
        assert item.extra == {}
        return True


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Target Asset Builder - 单元测试")
    print("=" * 60)
    
    tests = [
        ("CollectionTask.display_name", TestCollectionTask.test_display_name),
        ("CollectionTask.optional_parameters", TestCollectionTask.test_optional_parameters),
        ("CollectionTask.sensor_default", TestCollectionTask.test_sensor_default),
        ("CollectionTask.source_default", TestCollectionTask.test_source_default),
        ("CollectionTask.max_count_limit", TestCollectionTask.test_max_count_limit),
        ("CollectionTask.max_duration_limit", TestCollectionTask.test_max_duration_limit),
        ("CollectionTask.both_limits", TestCollectionTask.test_both_limits),
        ("CollectionTask.partial_parameters", TestCollectionTask.test_partial_parameters),
        ("SearchResultItem.defaults", TestSearchResultItem.test_defaults),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                print(f"✓ {name}")
                passed += 1
        except AssertionError as e:
            print(f"✗ {name}")
            print(f"  断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}")
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
