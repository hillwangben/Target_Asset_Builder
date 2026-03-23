---
name: multimodal-data-collector
overview: 构建一个多模态军事目标数据采集系统，支持从GitHub等开源渠道爬取图片、视频、声音数据，按国家/类型/型号分类存储，支持多传感器类型（可见光、红外、SAR、遥感）和分辨率过滤，自动生成目录文件。
design:
  architecture:
    framework: html
  styleKeywords:
    - CLI-Tool
    - Terminal-Aesthetic
  fontSystem:
    fontFamily: JetBrains-Mono
    heading:
      size: 16px
      weight: 700
    subheading:
      size: 14px
      weight: 600
    body:
      size: 13px
      weight: 400
  colorSystem:
    primary:
      - "#16C60C"
    background:
      - "#1E1E1E"
    text:
      - "#D4D4D4"
      - "#FFFFFF"
    functional:
      - "#F44747"
      - "#FFA500"
      - "#569CD6"
todos:
  - id: project-init
    content: 初始化项目结构，创建 pyproject.toml、config.yaml 和所有目录文件
    status: completed
  - id: core-models
    content: 实现核心数据模型（models.py）和配置管理（config.py）
    status: completed
    dependencies:
      - project-init
  - id: data-source-github
    content: 实现数据源抽象基类和 GitHub 数据源（sources/base.py + github_source.py）
    status: completed
    dependencies:
      - core-models
  - id: downloader-utils
    content: 实现异步下载器（downloader.py）、文件哈希（hashing.py）和元信息提取模块
    status: completed
    dependencies:
      - data-source-github
  - id: storage-catalog
    content: 实现存储管理（storage.py）、目录索引（catalog.py）和分辨率过滤器（resolution.py）
    status: completed
    dependencies:
      - downloader-utils
  - id: collector-cli
    content: 实现采集调度器（collector.py）、通用 URL 数据源和 CLI 入口（cli.py）
    status: completed
    dependencies:
      - storage-catalog
  - id: readme-docs
    content: 更新 ReadMe.md 项目文档，补充使用说明和配置示例
    status: completed
    dependencies:
      - collector-cli
  - id: "50576696"
    content: 生产部署脚本，支持在Windows和linux下构建和执行
    status: completed
---

## 用户需求

构建一个多模态军事目标数据采集系统（Target Asset Builder），从 GitHub 等开源渠道自动采集军事目标的多模态数据（图片、视频、声音），按结构化分类存储到本地，并同步生成目录索引文件。

## 产品概述

一个命令行数据采集工具，支持配置多个数据源（优先 GitHub），按国家 → 类型 → 型号的三级分类结构自动下载和整理军事目标的图片、视频和声音数据，同时生成结构化的目录文件供检索使用。

## 核心功能

- **多源数据采集**：支持从 GitHub 仓库、公开数据集 URL 等渠道抓取军事目标数据（图片、视频、声音）
- **三级分类存储**：按 国家/Country → 类型/Type（飞机/舰船/车辆等） → 型号/Model 的层级目录结构存储
- **多传感器类型支持**：图像和视频按传感器类型分类，包括可见光、红外（IR）、SAR、遥感（Remote Sensing）
- **分辨率过滤**：支持对图像和视频按最小分辨率（宽×高）进行过滤，低于阈值的文件自动跳过
- **本地持久化存储**：所有采集数据按标准化目录结构保存到本地磁盘
- **目录文件自动生成**：每次采集完成后自动生成/更新 JSON 格式的目录索引文件，记录所有已采集数据的元信息（路径、类型、分辨率、来源等）
- **断点续采与去重**：支持增量采集，避免重复下载已存在的文件

## 技术栈选择

- **语言**：Python 3.10+
- **HTTP 请求**：`httpx`（支持异步、HTTP/2、超时控制）
- **GitHub API**：`PyGithub`（GitHub 仓库搜索、文件下载）
- **图像元信息**：`Pillow`（读取图像分辨率）+ `opencv-python`（读取视频分辨率）
- **音频元信息**：`mutagen`（读取音频文件信息）
- **命令行框架**：`click`（提供清晰的 CLI 接口）
- **配置管理**：`pydantic`（配置校验与序列化）
- **进度展示**：`rich`（下载进度条、日志输出）
- **异步执行**：`asyncio` + `aiofiles`（并发下载、异步文件 IO）

## 实现方案

### 整体策略

采用插件化数据源架构，每个数据源（GitHub、通用 URL 等）实现统一接口。采集流程为：配置解析 → 数据源搜索 → 元信息提取 → 分辨率过滤 → 去重检查 → 并发下载 → 分类存储 → 目录文件更新。系统以 CLI 工具形式运行，支持子命令管理不同功能。

### 核心架构决策

1. **数据源抽象层**：定义 `DataSource` 基类，GitHub 和通用 URL 作为具体实现，方便后续扩展更多数据源（如 Kaggle、HuggingFace 等）
2. **元数据驱动**：每个文件下载后提取元信息（分辨率、传感器类型、格式等），作为过滤和索引的基础
3. **JSON Catalog 索引**：使用单一 JSON 文件记录全量采集元数据，支持快速查询和去重校验
4. **并发控制**：使用 asyncio 信号量限制并发下载数，避免对数据源造成过大压力
5. **分辨率过滤前置**：对于图片先下载到临时文件提取分辨率，不满足条件则删除临时文件；对于视频读取元数据头信息判断分辨率

### 性能与可靠性

- **时间复杂度**：搜索 O(N) N 为数据源返回结果数，去重检查 O(1)（基于文件哈希的 set 查找）
- **瓶颈识别**：网络 IO 是主要瓶颈，通过异步并发缓解
- **容错机制**：单文件下载失败不影响整体流程，记录失败日志供重试

### 目录存储结构

```
data/
├── catalog.json                    # 全局目录索引文件
├── airplane/                       # 类型：飞机
│   ├── USA/                        # 国家：美国
│   │   ├── F-22/                   # 型号
│   │   │   ├── visible/            # 传感器类型：可见光
│   │   │   │   ├── images/
│   │   │   │   └── videos/
│   │   │   ├── ir/                 # 传感器类型：红外
│   │   │   ├── sar/                # 传感器类型：SAR
│   │   │   └── remote_sensing/     # 传感器类型：遥感
│   │   └── B-2/
│   ├── China/
│   │   └── J-20/
│   └── Russia/
├── ship/                           # 类型：舰船
│   ├── USA/
│   │   └── Arleigh-Burke/
│   └── ...
└── vehicle/                        # 类型：车辆
    ├── USA/
    │   └── M1-Abrams/
    └── ...
```

### catalog.json 结构

```
{
  "version": "1.0",
  "last_updated": "2026-03-23T10:00:00Z",
  "assets": [
    {
      "id": "hash_sha256",
      "country": "USA",
      "type": "airplane",
      "model": "F-22",
      "sensor": "visible",
      "media_type": "image",
      "format": "jpg",
      "resolution": {"width": 1920, "height": 1080},
      "file_path": "data/airplane/USA/F-22/visible/images/f22_001.jpg",
      "file_size": 204800,
      "source": {"type": "github", "repo": "xxx/yyy", "url": "raw_url"},
      "collected_at": "2026-03-23T10:00:00Z"
    }
  ],
  "stats": {
    "total_files": 100,
    "by_country": {"USA": 50, "China": 30},
    "by_type": {"airplane": 40, "ship": 30, "vehicle": 30}
  }
}
```

## 目录结构

```
/mnt/d/code/Target_Asset_Builder/
├── ReadMe.md                        # [MODIFY] 更新项目说明文档
├── pyproject.toml                   # [NEW] 项目配置与依赖管理（Python 包管理）
├── config.yaml                      # [NEW] 全局配置文件（数据源、存储路径、过滤规则等）
├── src/
│   ├── __init__.py                  # [NEW] 包初始化
│   ├── cli.py                       # [NEW] CLI 入口，定义 collect/search/config 子命令
│   ├── config.py                    # [NEW] 配置加载与校验（Pydantic 模型定义）
│   ├── catalog.py                   # [NEW] 目录索引管理（JSON 读写、去重、统计）
│   ├── models.py                    # [NEW] 核心数据模型（Asset, AssetMeta, SensorType 等枚举与类）
│   ├── collector.py                 # [NEW] 采集调度器（编排搜索→过滤→下载→存储流程）
│   ├── storage.py                   # [NEW] 存储管理（目录创建、文件移动、路径规范化）
│   ├── filters/
│   │   ├── __init__.py              # [NEW] 过滤器包初始化
│   │   └── resolution.py            # [NEW] 分辨率过滤器（图片/视频分辨率检查与过滤）
│   ├── metadata/
│   │   ├── __init__.py              # [NEW] 元信息提取包初始化
│   │   ├── image_meta.py            # [NEW] 图像元信息提取（分辨率、格式、大小）
│   │   ├── video_meta.py            # [NEW] 视频元信息提取（分辨率、时长、编码）
│   │   └── audio_meta.py            # [NEW] 音频元信息提取（时长、采样率、格式）
│   ├── sources/
│   │   ├── __init__.py              # [NEW] 数据源包初始化 + DataSource 基类
│   │   ├── base.py                  # [NEW] 数据源抽象基类（定义统一接口）
│   │   ├── github_source.py         # [NEW] GitHub 数据源（仓库搜索、文件列举、下载）
│   │   └── url_source.py            # [NEW] 通用 URL 数据源（直接 URL 下载）
│   └── utils/
│       ├── __init__.py              # [NEW] 工具包初始化
│       ├── downloader.py            # [NEW] 异步下载器（并发控制、断点续传、重试）
│       └── hashing.py               # [NEW] 文件哈希计算（SHA-256，用于去重）
└── tests/
    ├── __init__.py                  # [NEW] 测试包初始化
    ├── test_catalog.py              # [NEW] 目录索引管理测试
    ├── test_collector.py            # [NEW] 采集流程集成测试
    ├── test_resolution_filter.py    # [NEW] 分辨率过滤器测试
    └── test_storage.py              # [NEW] 存储管理测试
```

## 实现注意事项

- **下载限速**：默认并发数限制为 5，避免触发 GitHub API rate limit（认证用户 5000 次/小时）
- **文件去重**：优先使用源 URL 去重（快速），下载完成后用 SHA-256 二次校验（精确）
- **分辨率提取**：图片用 Pillow 打开头部即可获取，无需完整解码；视频用 OpenCV 读取前几帧获取分辨率信息
- **目录文件原子更新**：先写入临时文件再重命名，防止采集中断导致目录文件损坏
- **日志规范**：使用 rich 的日志功能，按 INFO/WARNING/ERROR 分级输出，不记录敏感信息
- **配置热加载**：config.yaml 修改后无需重启即可生效（每次采集任务开始时重新加载）

## 设计风格

本项目为纯后端 CLI 工具，不需要 UI 界面。使用 Rich 库提供美观的终端输出体验，包括彩色日志、进度条、表格展示采集结果等。

## Agent 扩展

### Skill

- **browser-automation**
- 用途：在实现通用 URL 数据源时，可能需要访问需要浏览器渲染的网页来提取数据下载链接
- 预期结果：能够从动态网页中提取图片/视频/音频的下载地址

### SubAgent

- **code-explorer**
- 用途：在实现过程中探索 Python 依赖库的 API 接口和最佳实践
- 预期结果：快速获取第三方库的使用方法，确保代码实现正确