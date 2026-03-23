#!/bin/bash
# 快速功能验证脚本

echo "=========================================="
echo "Target Asset Builder - 快速功能测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 测试函数
run_test() {
    local name="$1"
    local cmd="$2"
    
    echo "测试: $name"
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ 失败${NC}"
        ((FAILED++))
    fi
    echo ""
}

# 1. 检查 Python 版本
run_test "Python 3.10+" "python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'"

# 2. 检查依赖
run_test "click 已安装" "python3 -c 'import click'"
run_test "httpx 已安装" "python3 -c 'import httpx'"
run_test "pydantic 已安装" "python3 -c 'import pydantic'"
run_test "yaml 已安装" "python3 -c 'import yaml'"
run_test "rich 已安装" "python3 -c 'import rich'"

# 3. 检查核心模块
run_test "config.py 编译" "python3 -m py_compile src/config.py"
run_test "models.py 编译" "python3 -m py_compile src/models.py"
run_test "cli.py 编译" "python3 -m py_compile src/cli.py"
run_test "collector.py 编译" "python3 -m py_compile src/collector.py"
run_test "storage.py 编译" "python3 -m py_compile src/storage.py"
run_test "catalog.py 编译" "python3 -m py_compile src/catalog.py"

# 4. 检查子模块
run_test "sources 模块编译" "python3 -m py_compile src/sources/*.py"
run_test "filters 模块编译" "python3 -m py_compile src/filters/*.py"
run_test "metadata 模块编译" "python3 -m py_compile src/metadata/*.py"
run_test "utils 模块编译" "python3 -m py_compile src/utils/*.py"

# 5. 配置文件检查
run_test "config.yaml 存在" "test -f config.yaml"
run_test "config.yaml 格式正确" "python3 -c 'from src.config import load_config; load_config()'"

# 6. 测试文件检查
run_test "测试脚本存在" "test -f test_core.py"
run_test "单元测试存在" "test -f test_unit.py"

# 7. 运行核心测试
echo "运行核心功能测试..."
if python3 test_core.py > /tmp/test_core.log 2>&1; then
    echo -e "${GREEN}✓ 核心测试通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 核心测试失败${NC}"
    ((FAILED++))
fi
echo ""

# 8. 运行单元测试
echo "运行单元测试..."
if python3 test_unit.py > /tmp/test_unit.log 2>&1; then
    echo -e "${GREEN}✓ 单元测试通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 单元测试失败${NC}"
    ((FAILED++))
fi
echo ""

# 输出结果
echo "=========================================="
echo -e "测试结果: ${GREEN}$PASSED 通过${NC}, ${RED}$FAILED 失败${NC}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 所有测试通过！项目构建成功。${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  部分测试失败，请检查日志${NC}"
    exit 1
fi
