@echo off
echo ===================================
echo   AI 代码审计系统 - 初始化脚本
echo ===================================
echo.

echo [1/6] 检查必要依赖...

echo   - 检查 Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Docker 未安装或未运行
    echo   请先安装 Docker Desktop 并启动
    pause
    exit /b 1
)
echo   [OK] Docker 已安装

echo   - 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Python 未安装
    pause
    exit /b 1
)
echo   [OK] Python 已安装

echo   - 检查 Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Git 未安装
    pause
    exit /b 1
)
echo   [OK] Git 已安装

echo.
echo [2/6] 创建必要目录...
if not exist ..\data mkdir ..\data
if not exist ..\data\uploads mkdir ..\data\uploads
if not exist ..\data\reports mkdir ..\data\reports
if not exist ..\logs mkdir ..\logs
echo   [OK] 目录创建完成

echo.
echo [3/6] 生成 .env 配置文件...
if not exist ..\.env (
    (
        echo # ===================================
        echo # AI 代码审计系统 - 环境配置
        echo # ===================================
        echo.
        echo # OpenAI API 配置
        echo # 请替换为你的实际 API Key
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # 数据库配置
        echo DATABASE_URL=sqlite+aiosqlite:///./data/audit.db
        echo.
        echo # Docker 镜像配置
        echo DOCKER_AUDIT_BASE_IMAGE=cyber-audit-base
        echo.
        echo # 沙箱安全配置
        echo SANDBOX_MEMORY_LIMIT=2g
        echo SANDBOX_CPU_LIMIT=0.5
        echo SANDBOX_TIMEOUT=600
        echo.
        echo # 日志配置
        echo LOG_LEVEL=INFO
        echo LOG_FILE=logs/audit.log
    ) > ..\.env
    echo   [OK] 已生成 .env 文件
    echo   [!] 请编辑 .env 文件填入你的 API Key
) else (
    echo   [OK] .env 文件已存在，跳过生成
)

echo.
echo [4/6] 安装 Python 依赖...
cd ..\backend
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo   [X] Python 依赖安装失败
    pause
    exit /b 1
)
echo   [OK] Python 依赖安装完成

echo.
echo [5/6] 构建 Docker 基础镜像...
cd ..\docker_env
echo   这可能需要 5-10 分钟，请耐心等待...
docker build -t cyber-audit-base -f Dockerfile.base .
if %errorlevel% neq 0 (
    echo   [X] Docker 镜像构建失败
    pause
    exit /b 1
)
echo   [OK] Docker 镜像构建成功

echo.
echo [6/6] 运行健康检查...
echo   - 测试 Python...
docker run --rm cyber-audit-base python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Python 测试失败
    pause
    exit /b 1
)
echo   [OK] Python 正常

echo   - 测试 Bandit...
docker run --rm cyber-audit-base bandit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Bandit 测试失败
    pause
    exit /b 1
)
echo   [OK] Bandit 正常

echo   - 测试 Semgrep...
docker run --rm cyber-audit-base semgrep --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Semgrep 测试失败
    pause
    exit /b 1
)
echo   [OK] Semgrep 正常

echo.
echo ===================================
echo   初始化完成！
echo ===================================
echo.
echo 下一步操作：
echo   1. 编辑 .env 文件填入你的 OpenAI API Key
echo   2. 运行测试：pytest backend/tests/
echo   3. 启动服务：cd backend ^&^& uvicorn main:app --reload
echo.
pause