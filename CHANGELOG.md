# 更新日志

## [1.4.0] - 2026-03-24

### 新增功能

- 🛡️ **格式规范化**: 自动将非主流格式转换为主流格式
  - **图片**: WebP→JPG、HEIC→JPG、TIFF→JPG、BMP→JPG、GIF→JPG、ICO→PNG
  - **视频**: WebM→MP4、FLV→MP4、AVI→MP4、MKV→MP4
  - **音频**: WAV→MP3、FLAC→MP3、M4A→MP3

- 🔍 **合法性校验**: 多层次文件安全检查
  - **完整性校验**: 确保文件完整、未损坏
  - **内容安全校验**: 通过魔术字节检测恶意文件、可疑内容（JavaScript注入、PHP脚本、PE/ELF可执行文件等）
  - **媒体类型一致性校验**: 验证文件内容与声明类型匹配（如图片实际是视频则报错）
  - **音频时长校验**: 检查音频文件是否满足最低时长要求

### 配置更新

```yaml
# 格式规范化配置
format:
  normalize: true        # 是否启用格式规范化
  image_format: "jpg"   # 图片目标格式
  video_format: "mp4"   # 视频目标格式
  audio_format: "mp3"   # 音频目标格式

# 合法性校验配置
validation:
  enabled: true         # 是否启用校验
  check_integrity: true # 文件完整性校验
  check_safety: true    # 内容安全校验
  check_mime_type: true # MIME类型一致性校验
  min_audio_duration: 0 # 最小音频时长（秒）
```

### 文件变更

- `src/config.py`: 新增 FormatConfig、ValidationConfig 配置类
- `config.yaml`: 添加 format 和 validation 配置节
- `src/utils/format_converter.py`: 新增格式转换模块
- `src/utils/validator.py`: 新增合法性校验模块
- `src/collector.py`: 集成格式转换和校验流程
- `ReadMe.md`: 更新文档添加格式规范化和校验说明
- `CHANGELOG.md`: 本文件

---

## [1.3.0] - 2026-03-23

### 新增功能

- 🚀 **多源数据采集**: 扩展搜索范围，支持多种数据源
  - **Web 网页搜索**: 自动从网页中提取图片、视频、音频链接
  - **HuggingFace 数据集**: 从 HuggingFace 数据集下载资源
  - **多源综合采集**: 同时从多个数据源并行采集，提高效率

- 📊 **数据源类型**:
  - `github`: GitHub 仓库搜索（原有）
  - `url`: 直接 URL 下载（原有）
  - `web`: 网页搜索（新增）
  - `huggingface`: HuggingFace 数据集（新增）
  - `multi`: 多源综合采集（新增）

### 使用示例

```bash
# 从网页搜索采集
tab collect --source web --keywords "https://example.com/gallery.html"

# 从 HuggingFace 数据集采集
tab collect --source huggingface --keywords "username/dataset-name"

# 多源综合采集（同时从 GitHub 和网页采集）
tab collect --source multi --keywords "F-22 Raptor" --max-count 100
```

### 配置更新

- `config.yaml`: 添加 web、huggingface、multi 数据源配置
- `src/config.py`: 新增 WebSourceConfig、HuggingFaceSourceConfig、MultiSourceConfig

### 文件变更

- `src/sources/web_source.py`: 新增网页搜索数据源
- `src/sources/huggingface_source.py`: 新增 HuggingFace 数据源
- `src/sources/multi_source.py`: 新增多源综合采集器
- `src/collector.py`: 支持新数据源创建
- `src/cli.py`: 更新数据源选项
- `ReadMe.md`: 更新文档添加多源采集说明
- `CHANGELOG.md`: 本文件

---

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
