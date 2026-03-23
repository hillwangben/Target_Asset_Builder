# 更新日志

## [1.2.0] - 2026-03-23

### 新增功能

- ✨ **灵活参数配置**: 所有分类参数（country、type、model）变为可选
  - 未指定 `--country` 时使用 "ALL" 占位符，不限制国家
  - 未指定 `--type` 时使用 "ALL" 占位符，不限制目标类型
  - 未指定 `--model` 时使用 "ALL" 占位符，不限制型号
  - 支持仅使用关键词进行广泛数据采集

### 使用示例

```bash
# 使用关键词通用采集（不指定国家、类型、型号）
tab collect --keywords "military aircraft dataset" --source github

# 仅指定国家，其他参数留空
tab collect --country USA --keywords "fighter jet" --source github

# 完全不限制，使用关键词广泛采集
tab collect --keywords "military dataset" --source github
```

### 文件变更

- `src/cli.py`: 更新 collect 和 collect_batch 函数支持可选参数
- `tasks.example.json`: 更新示例包含可选参数任务
- `ReadMe.md`: 更新文档说明可选参数行为
- `CHANGELOG.md`: 本文件

---

## [1.1.0] - 2026-03-23

### 新增功能

- ✨ **采集限制**: 支持按数量或时间限制采集任务
  - `--max-count`: 达到指定文件数量后自动停止
  - `--max-duration`: 达到指定时长（秒）后自动停止
  - 两个限制可单独使用或组合使用
  - 采集完成后显示停止原因

### 文件变更

- `src/models.py`: 添加 max_count、max_duration_seconds、stop_reason 字段
- `src/collector.py`: 实现采集过程中的数量和时间检查
- `src/config.py`: 添加 LimitsConfig 配置类
- `config.yaml`: 添加 limits 配置节
- `src/cli.py`: 添加 --max-count 和 --max-duration 命令行参数
- `ReadMe.md`: 更新文档添加限制功能说明

---

## [1.0.0] - 2026-03-23

### 初始版本

- 🎉 多模态军事目标数据采集系统首次发布
- 支持 GitHub 仓库搜索和通用 URL 下载
- 三级分类存储（国家/类型/型号）
- 多传感器类型支持（可见光、红外、SAR、遥感）
- 分辨率过滤功能
- 自动去重（URL + SHA-256）
- 目录索引生成
- 批量采集支持
