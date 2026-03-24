# Target Asset Builder

多模态军事目标数据采集系统，支持从 GitHub 等开源渠道自动采集军事目标的图片、视频和声音数据，按结构化分类存储到本地，并自动生成目录索引文件。

## 功能特性

- **多源数据采集**: 支持 GitHub 仓库、网页搜索、HuggingFace 数据集、直接 URL 等多种数据源
- **多源综合采集**: 可同时从多个数据源并行采集数据，提高采集效率
- **三级分类存储**: 按 国家 → 类型 → 型号 层级目录结构自动整理
- **多传感器类型**: 可见光、红外（IR）、SAR、遥感
- **分辨率过滤**: 按最小宽度/高度/维度过滤图片和视频
- **自动去重**: 基于 URL 快速去重 + SHA-256 文件哈希精确去重
- **目录索引**: 每次采集后自动生成/更新 JSON 格式目录文件
- **断点续采**: 增量采集，已下载文件自动跳过
- **批量采集**: 支持从 JSON 文件批量执行采集任务
- **采集限制**: 支持设置采集数量和时间限制，达到阈值自动停止
- **格式规范化**: 自动将非主流格式转换为主流格式（如 WebP→JPG、HEIC→JPG）
- **合法性校验**: 支持文件完整性、内容安全、媒体类型一致性、音频时长校验

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd Target_Asset_Builder

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 使用部署脚本

```bash
# Linux/macOS
chmod +x scripts/setup.sh
./scripts/setup.sh

# Windows
scripts\setup.bat
```

## 使用方法

### 1. 配置

编辑 `config.yaml` 配置文件：

```yaml
# GitHub Token（可选，提升 API 限额）
sources:
  github:
    token: "your_github_token_here"
    per_page: 30
    max_pages: 5

# 下载配置
download:
  concurrency: 5      # 并发下载数
  max_file_size_mb: 100

# 分辨率过滤
filters:
  resolution:
    enabled: true
    min_width: 640     # 最小宽度
    min_height: 480    # 最小高度

# 格式规范化配置
format:
  normalize: true       # 是否启用格式规范化
  image_format: "jpg"  # 图片目标格式 (jpg, png, webp)
  video_format: "mp4"  # 视频目标格式 (mp4, avi, mkv)
  audio_format: "mp3"  # 音频目标格式 (mp3, wav, flac)

# 合法性校验配置
validation:
  enabled: true        # 是否启用校验
  check_integrity: true  # 文件完整性校验
  check_safety: true    # 内容安全校验（检测恶意文件）
  check_mime_type: true # MIME类型一致性校验
  min_audio_duration: 0  # 最小音频时长（秒），0表示不限制
```

### 2. 单次采集

```bash
# 从 GitHub 采集 F-22 战斗机图片
tab collect \
  --country USA \
  --type airplane \
  --model F-22 \
  --sensor visible \
  --keywords "F-22 Raptor military aircraft dataset" \
  --source github

# 从 URL 直接下载
tab collect \
  --country USA \
  --type airplane \
  --model F-22 \
  --sensor visible \
  --source url \
  --keywords "https://example.com/f22_image.jpg"

# 从网页搜索采集（自动提取网页中的媒体链接）
tab collect \
  --country USA \
  --type airplane \
  --model F-22 \
  --source web \
  --keywords "https://example.com/f22-gallery.html"

# 从 HuggingFace 数据集采集
tab collect \
  --country USA \
  --type airplane \
  --model F-22 \
  --source huggingface \
  --keywords "username/f22-dataset"

# 多源综合采集（同时从 GitHub 和网页采集）
tab collect \
  --country USA \
  --type airplane \
  --model F-22 \
  --source multi \
  --keywords "F-22 Raptor" \
  --max-count 100
```

### 3. 带分辨率过滤

```bash
tab collect \
  --country China \
  --type ship \
  --model "Type-055" \
  --sensor sar \
  --keywords "Type-055 destroyer SAR imagery" \
  --min-width 1024 \
  --min-height 1024
```

### 4. 批量采集

创建 `tasks.json` 文件：

```json
[
  {
    "country": "USA",
    "type": "airplane",
    "model": "F-22",
    "sensor": "visible",
    "keywords": ["F-22 Raptor dataset"],
    "source": "github",
    "max_count": 100,
    "max_duration_seconds": 300
  },
  {
    "country": "China",
    "type": "airplane",
    "model": "J-20",
    "sensor": "ir",
    "keywords": ["J-20 stealth fighter infrared"],
    "source": "github",
    "max_count": 50
  }
]
```

执行批量采集：

```bash
tab collect-batch --file tasks.json
```

执行批量采集：

```bash
tab collect-batch --file tasks.json
```

### 5. 查询目录

```bash
# 查看全部
tab search

# 按条件过滤
tab search --country USA --type airplane

# JSON 格式输出
tab search --format json --model "F-22"
```

### 8. 查看统计

```bash
tab stats
tab info
```

## 目录结构

采集后的数据按以下结构存储：

```
data/
├── catalog.json                    # 全局目录索引
├── airplane/                       # 类型
│   ├── USA/                        # 国家
│   │   ├── F-22/                   # 型号
│   │   │   ├── visible/            # 传感器类型
│   │   │   │   ├── images/
│   │   │   │   ├── videos/
│   │   │   │   └── audio/
│   │   │   ├── ir/
│   │   │   ├── sar/
│   │   │   └── remote_sensing/
│   │   └── B-2/
│   └── China/
├── ship/
└── vehicle/
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `tab collect` | 执行单次采集任务 |
| `tab collect-batch` | 从 JSON 文件批量采集 |
| `tab search` | 查询已采集数据目录 |
| `tab stats` | 查看采集统计信息 |
| `tab info` | 显示系统配置信息 |
| `tab --version` | 显示版本号 |

## 技术栈

- **Python 3.10+**
- **httpx** - 异步 HTTP 客户端
- **PyGithub** - GitHub API
- **Pillow** - 图像处理
- **OpenCV** - 视频元信息提取
- **mutagen** - 音频元信息提取
- **pydantic** - 数据校验
- **click** - CLI 框架
- **rich** - 终端美化输出

## 参数说明

### 可选参数行为

以下参数均为可选，未指定时不会进行特定过滤：

- `--country / -n`: 国家/地区代码，默认 "ALL"
- `--type / -t`: 目标类型，默认 "ALL"
- `--model / -m`: 型号，默认 "ALL"
- `--sensor / -s`: 传感器类型，默认 "unknown"

### 必需参数

- `--keywords / -k`: 搜索关键词（可多次指定，至少需要 1 个）

### 可选限制参数

- `--max-count`: 最大采集数量
- `--max-duration`: 最大采集时长（秒）
- `--min-width`: 最小宽度（像素）
- `--min-height`: 最小高度（像素）
- `--min-dimension`: 最小维度（像素）

### 数据源说明

系统支持以下数据源：

1. **github**: GitHub 仓库搜索
   - 搜索 GitHub 仓库中的图片、视频、音频文件
   - 支持遍历仓库文件树和 Release 资源
   - 需要 GitHub Token 提升搜索限额

2. **url**: 直接 URL 下载
   - 从给定的 URL 列表直接下载文件
   - 适合已知具体下载链接的场景

3. **web**: 网页搜索
   - 从网页中自动提取媒体链接
   - 支持解析 `<img>`, `<video>`, `<audio>` 标签
   - 支持延迟加载（data-src）和 CSS 背景图

4. **huggingface**: HuggingFace 数据集
   - 从 HuggingFace 数据集下载文件
   - 支持数据集搜索和文件树遍历

5. **multi**: 多源综合采集
   - 同时从多个数据源并行采集
   - 通过配置文件设置启用的数据源
   - 提高采集效率和覆盖范围

### 格式规范化

系统支持自动将非主流格式转换为主流格式：

- **图片**: WebP→JPG、HEIC→JPG、TIFF→JPG、BMP→JPG、GIF→JPG、ICO→PNG
- **视频**: WebM→MP4、FLV→MP4、AVI→MP4、MKV→MP4
- **音频**: WAV→MP3、FLAC→MP3、M4A→MP3

转换需要在配置文件中启用：

```yaml
format:
  normalize: true
  image_format: "jpg"
  video_format: "mp4"
  audio_format: "mp3"
```

### 合法性校验

系统支持以下合法性校验：

1. **完整性校验**: 确保文件完整、未损坏
2. **内容安全校验**: 通过魔术字节检测恶意文件、可疑内容
3. **媒体类型一致性校验**: 验证文件内容与声明类型匹配
4. **音频时长校验**: 检查音频文件是否满足最低时长要求

```yaml
validation:
  enabled: true
  check_integrity: true
  check_safety: true
  check_mime_type: true
  min_audio_duration: 0  # 秒，0表示不限制
```

## License

MIT
