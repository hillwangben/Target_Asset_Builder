#!/usr/bin/env bash
# ============================================================
# Target Asset Builder - Linux/macOS 环境构建与运行脚本
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================
# 命令处理
# ============================================================

cmd_help() {
    echo ""
    echo "Target Asset Builder - 构建与运行脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  setup       初始化环境（创建虚拟环境、安装依赖）"
    echo "  install     安装项目（editable mode）"
    echo "  run         运行 CLI 工具（传递参数给 tab 命令）"
    echo "  test        运行测试"
    echo "  clean       清理临时文件和缓存"
    echo "  help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 setup"
    echo "  $0 run collect --country USA --type airplane --model F-22 --keywords F-22"
    echo "  $0 run search --country USA"
    echo "  $0 run stats"
    echo ""
}

cmd_setup() {
    print_info "检查 Python 版本..."

    if ! command -v python3 &>/dev/null; then
        print_error "未找到 python3，请先安装 Python 3.10+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    print_info "Python 版本: $PYTHON_VERSION"

    if [ "$(echo "$PYTHON_VERSION < 3.10" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        print_error "需要 Python 3.10 或更高版本"
        exit 1
    fi

    print_info "创建虚拟环境..."
    if [ ! -d "$PROJECT_DIR/.venv" ]; then
        python3 -m venv "$PROJECT_DIR/.venv"
        print_success "虚拟环境已创建"
    else
        print_warn "虚拟环境已存在，跳过创建"
    fi

    print_info "激活虚拟环境..."
    source "$PROJECT_DIR/.venv/bin/activate"

    print_info "升级 pip..."
    pip install --upgrade pip -q

    cmd_install

    print_success "环境初始化完成！"
    print_info "使用前请先激活虚拟环境: source $PROJECT_DIR/.venv/bin/activate"
}

cmd_install() {
    print_info "安装项目依赖..."

    if [ ! -d "$PROJECT_DIR/.venv" ]; then
        print_error "虚拟环境不存在，请先运行: $0 setup"
        exit 1
    fi

    source "$PROJECT_DIR/.venv/bin/activate"

    pip install -e "$PROJECT_DIR[dev]" -q
    print_success "项目安装完成"
}

cmd_run() {
    if [ ! -d "$PROJECT_DIR/.venv" ]; then
        print_error "虚拟环境不存在，请先运行: $0 setup"
        exit 1
    fi

    source "$PROJECT_DIR/.venv/bin/activate"
    cd "$PROJECT_DIR"

    python -m src.cli "$@"
}

cmd_test() {
    if [ ! -d "$PROJECT_DIR/.venv" ]; then
        print_error "虚拟环境不存在，请先运行: $0 setup"
        exit 1
    fi

    source "$PROJECT_DIR/.venv/bin/activate"
    cd "$PROJECT_DIR"

    print_info "运行测试..."
    python -m pytest tests/ -v --tb=short
    print_success "测试完成"
}

cmd_clean() {
    print_info "清理临时文件..."

    cd "$PROJECT_DIR"

    # 清理临时下载目录
    if [ -d "data/.tmp_downloads" ]; then
        rm -rf "data/.tmp_downloads"
        print_info "已清理 data/.tmp_downloads"
    fi

    # 清理 Python 缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # 清理 pytest 缓存
    if [ -d ".pytest_cache" ]; then
        rm -rf ".pytest_cache"
    fi

    print_success "清理完成"
}

# ============================================================
# 入口
# ============================================================

case "${1:-help}" in
    setup)   cmd_setup ;;
    install) cmd_install ;;
    run)     shift; cmd_run "$@" ;;
    test)    cmd_test ;;
    clean)   cmd_clean ;;
    help|-h|--help) cmd_help ;;
    *)       print_error "未知命令: $1"; cmd_help; exit 1 ;;
esac
