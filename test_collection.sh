#!/bin/bash
# 测试采集功能（模拟）

echo "=========================================="
echo "Target Asset Builder - 采集测试"
echo "=========================================="
echo ""

cd /mnt/d/code/Target_Asset_Builder

# 测试 1: 显示任务信息
echo "测试 1: 创建采集任务"
python3 -c "
from src.models import CollectionTask, TargetType
task = CollectionTask(
    country='USA',
    type=TargetType.AIRPLANE,
    model='F-22',
    keywords=['F-22 Raptor'],
    max_count=10,
)
print(f'  任务: {task.display_name}')
print(f'  关键词: {task.keywords}')
print(f'  最大数量: {task.max_count}')
print(f'  数据源: {task.source}')
"

echo ""
echo "测试 2: 检查采集器"
python3 -c "
from src.config import load_config
from src.collector import Collector
cfg = load_config()
collector = Collector(cfg)
print('  采集器初始化成功')
print(f'  存储根目录: {collector._storage.root}')
print(f'  分辨率过滤器: {collector._resolution_filter.enabled}')
"

echo ""
echo "测试 3: 检查存储管理器"
python3 -c "
from src.config import load_config
from src.storage import StorageManager
cfg = load_config()
storage = StorageManager(cfg.storage.root_dir)
print('  存储管理器初始化成功')
storage.ensure_root()
import os
if os.path.exists(storage.root):
    print(f'  存储目录已创建: {storage.root}')
else:
    print('  存储目录创建失败')
"

echo ""
echo "测试 4: 检查目录管理器"
python3 -c "
from src.config import load_config
from src.catalog import CatalogManager
cfg = load_config()
catalog = CatalogManager(cfg.storage.root_dir, cfg.storage.catalog_file)
catalog.load()
stats = catalog.get_stats()
print('  目录管理器初始化成功')
print(f'  总文件数: {stats.total_files}')
print(f'  总大小: {stats.total_size} 字节')
print(f'  跳过: {stats.skipped}')
print(f'  失败: {stats.failed}')
"

echo ""
echo "=========================================="
echo "所有测试完成！"
echo "=========================================="
