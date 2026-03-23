#!/usr/bin/env python3
"""测试脚本 - 验证核心功能"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import AppConfig, load_config
from src.models import (
    CollectionTask,
    TargetType,
    SensorType,
    MediaType,
    CollectionStats,
)
from src.storage import StorageManager
from src.catalog import CatalogManager
from src.filters.resolution import ResolutionFilter


def test_config():
    """测试配置加载"""
    print("✓ 测试配置加载...")
    cfg = load_config()
    print(f"  存储目录: {cfg.storage.root_dir}")
    print(f"  下载数: {cfg.download.concurrency}")
    print(f"  默认最大数量: {cfg.limits.default_max_count}")
    print(f"  默认最大时长: {cfg.limits.default_max_duration}")
    return True


def test_models():
    """测试数据模型"""
    print("\n✓ 测试数据模型...")
    
    # 完整参数任务
    task1 = CollectionTask(
        country="USA",
        type=TargetType.AIRPLANE,
        model="F-22",
        sensor=SensorType.VISIBLE,
        keywords=["test"],
        max_count=100,
        max_duration_seconds=300,
    )
    print(f"  完整任务: {task1.display_name}")
    print(f"    最大数量: {task1.max_count}")
    print(f"    最大时长: {task1.max_duration_seconds}")
    
    # 可选参数任务
    task2 = CollectionTask(
        keywords=["military dataset"],
    )
    print(f"  可选任务: {task2.display_name}")
    print(f"    国家: {task2.country}")
    print(f"    类型: {task2.type}")
    print(f"    型号: {task2.model}")
    
    # 部分参数任务
    task3 = CollectionTask(
        country="China",
        type=TargetType.SHIP,
        keywords=["naval"],
    )
    print(f"  部分任务: {task3.display_name}")
    
    # 统计对象
    stats = CollectionStats(
        total_files=100,
        total_size=1024000,
        skipped=10,
        failed=2,
        stop_reason="已达到最大采集数量 100",
    )
    print(f"  统计: {stats.total_files} 文件, 停止原因: {stats.stop_reason}")
    
    return True


def test_storage():
    """测试存储管理"""
    print("\n✓ 测试存储管理...")
    cfg = load_config()
    storage = StorageManager(cfg.storage.root_dir)
    print(f"  存储管理器创建成功")
    print(f"  根目录: {storage.root}")
    return True


def test_catalog():
    """测试目录管理"""
    print("\n✓ 测试目录管理...")
    cfg = load_config()
    catalog = CatalogManager(cfg.storage.root_dir, cfg.storage.catalog_file)
    print(f"  目录管理器创建成功")
    
    # 测试统计
    stats = catalog.get_stats()
    print(f"  统计: {stats.total_files} 文件")
    return True


def test_resolution_filter():
    """测试分辨率过滤器"""
    print("\n✓ 测试分辨率过滤器...")
    filter_config = ResolutionFilter(
        enabled=True,
        min_width=640,
        min_height=480,
    )
    res_filter = ResolutionFilter(
        enabled=True,
        min_width=640,
        min_height=480,
        min_dimension=0,
    )
    
    # 测试分辨率检查（模拟）
    print(f"  过滤器: 最小宽度 {res_filter.min_width}, 最小高度 {res_filter.min_height}")
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Target Asset Builder - 功能测试")
    print("=" * 60)
    
    tests = [
        ("配置加载", test_config),
        ("数据模型", test_models),
        ("存储管理", test_storage),
        ("目录管理", test_catalog),
        ("分辨率过滤", test_resolution_filter),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ 测试失败: {name}")
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
