@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================================
REM Target Asset Builder - Windows 环境构建与运行脚本
REM ============================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="-h" goto help
if "%1"=="--help" goto help
if "%1"=="setup" goto setup
if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="test" goto test
if "%1"=="clean" goto clean

echo [ERROR] 未知命令: %1
goto help

:help
echo.
echo Target Asset Builder - 构建与运行脚本
echo.
echo 用法: setup.bat ^<command^> [options]
echo.
echo 命令:
echo   setup       初始化环境（创建虚拟环境、安装依赖）
echo   install     安装项目（editable mode）
echo   run         运行 CLI 工具（传递参数给 tab 命令）
echo   test        运行测试
echo   clean       清理临时文件和缓存
echo   help        显示帮助信息
echo.
echo 示例:
echo   setup.bat setup
echo   setup.bat run collect --country USA --type airplane --model F-22 --keywords F-22
echo   setup.bat run search --country USA
echo   setup.bat run stats
echo.
goto end

:setup
echo [INFO] 检查 Python...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 未找到 python，请先安装 Python 3.10+
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [INFO] Python 版本: %PYTHON_VERSION%

echo [INFO] 创建虚拟环境...
if not exist "%PROJECT_DIR%\.venv" (
    python -m venv "%PROJECT_DIR%\.venv"
    echo [OK] 虚拟环境已创建
) else (
    echo [WARN] 虚拟环境已存在，跳过创建
)

echo [INFO] 激活虚拟环境...
call "%PROJECT_DIR%\.venv\Scripts\activate.bat"

echo [INFO] 升级 pip...
python -m pip install --upgrade pip -q

call :install

echo [OK] 环境初始化完成！
echo [INFO] 使用前请先激活虚拟环境: call %PROJECT_DIR%\.venv\Scripts\activate.bat
goto end

:install
echo [INFO] 安装项目依赖...

if not exist "%PROJECT_DIR%\.venv" (
    echo [ERROR] 虚拟环境不存在，请先运行: setup.bat setup
    exit /b 1
)

call "%PROJECT_DIR%\.venv\Scripts\activate.bat"

pip install -e "%PROJECT_DIR%[dev]" -q
echo [OK] 项目安装完成
goto end

:run
if not exist "%PROJECT_DIR%\.venv" (
    echo [ERROR] 虚拟环境不存在，请先运行: setup.bat setup
    exit /b 1
)

call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
cd /d "%PROJECT_DIR%"

python -m src.cli %2 %3 %4 %5 %6 %7 %8 %9
goto end

:test
if not exist "%PROJECT_DIR%\.venv" (
    echo [ERROR] 虚拟环境不存在，请先运行: setup.bat setup
    exit /b 1
)

call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
cd /d "%PROJECT_DIR%"

echo [INFO] 运行测试...
python -m pytest tests/ -v --tb=short
echo [OK] 测试完成
goto end

:clean
echo [INFO] 清理临时文件...

cd /d "%PROJECT_DIR%"

if exist "data\.tmp_downloads" (
    rmdir /s /q "data\.tmp_downloads"
    echo [INFO] 已清理 data\.tmp_downloads
)

for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

if exist ".pytest_cache" (
    rmdir /s /q ".pytest_cache"
)

echo [OK] 清理完成
goto end

:end
endlocal
