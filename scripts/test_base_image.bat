@echo off
echo 测试基础镜像...

echo.
echo [1/7] 构建镜像...
cd ..\docker_env
docker build -t cyber-audit-base -f Dockerfile.base .
if %errorlevel% neq 0 (
    echo 镜像构建失败
    pause
    exit /b 1
)
echo 镜像构建成功

echo.
echo [2/7] 测试 Python...
docker run --rm cyber-audit-base python --version

echo.
echo [3/7] 测试 Bandit...
docker run --rm cyber-audit-base bandit --version

echo.
echo [4/7] 测试 Semgrep...
docker run --rm cyber-audit-base semgrep --version

echo.
echo [5/7] 测试 Java...
docker run --rm cyber-audit-base java -version

echo.
echo [6/7] 测试 PHP...
docker run --rm cyber-audit-base php --version

echo.
echo [7/7] 测试 Node.js...
docker run --rm cyber-audit-base node --version

echo.
echo 所有工具测试完成！
pause