# start_audit_system.ps1 - 启动 Cyber Audit 系统

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Cyber Audit 系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. 停止所有相关进程
Write-Host "1. 停止相关进程..." -ForegroundColor Yellow
$processes = @("uvicorn", "python")
foreach ($proc in $processes) {
    $running = Get-Process $proc -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "  停止 $proc 进程..." -ForegroundColor Yellow
        Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
    }
}

# 2. 检查端口占用情况
Write-Host "`n2. 检查端口..." -ForegroundColor Yellow
$ports = @(8000, 8001, 8002, 8003, 8004, 8005)
$availablePort = $null

foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if (-not $connection.TcpTestSucceeded) {
        $availablePort = $port
        Write-Host "  ✓ 端口 $port 可用" -ForegroundColor Green
        break
    } else {
        Write-Host "  ✗ 端口 $port 被占用" -ForegroundColor Red
        
        # 尝试结束占用该端口的进程
        $netstat = netstat -ano | findstr ":$port"
        if ($netstat) {
            $pidMatch = $netstat | Select-String '\s+(\d+)$'
            if ($pidMatch.Matches.Groups[1].Value) {
                $pid = $pidMatch.Matches.Groups[1].Value
                Write-Host "    进程PID: $pid" -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "    已停止进程 $pid" -ForegroundColor Green
            }
        }
    }
}

if (-not $availablePort) {
    Write-Host "  ✗ 没有找到可用端口，尝试使用8006" -ForegroundColor Red
    $availablePort = 8006
}

Write-Host "`n3. 修改配置文件使用端口 $availablePort ..." -ForegroundColor Yellow

# 3. 修改 cyber_audit_final.py 中的端口
$pythonFile = "cyber_audit_final.py"
$content = Get-Content $pythonFile -Raw

# 查找并替换端口号
if ($content -match 'port=8000') {
    $content = $content -replace 'port=8000', "port=$availablePort"
    Set-Content $pythonFile $content -Encoding UTF8
    Write-Host "  ✓ 已更新端口为 $availablePort" -ForegroundColor Green
} elseif ($content -match 'port=8003') {
    $content = $content -replace 'port=8003', "port=$availablePort"
    Set-Content $pythonFile $content -Encoding UTF8
    Write-Host "  ✓ 已更新端口为 $availablePort" -ForegroundColor Green
} else {
    # 如果没找到port=xxxx，就在uvicorn.run调用中添加端口
    $uvicornPattern = 'uvicorn\.run\s*\(\s*app\s*,'
    if ($content -match $uvicornPattern) {
        $newUvicornCall = "uvicorn.run(app, host=`"127.0.0.1`", port=$availablePort, log_level=`"info`")"
        $content = $content -replace 'uvicorn\.run\s*\(.*?\)', $newUvicornCall
        Set-Content $pythonFile $content -Encoding UTF8
        Write-Host "  ✓ 已添加端口 $availablePort" -ForegroundColor Green
    }
}

# 4. 启动应用
Write-Host "`n4. 启动 Cyber Audit 系统..." -ForegroundColor Yellow
Write-Host "  端口: $availablePort" -ForegroundColor Cyan
Write-Host "  URL: http://127.0.0.1:$availablePort" -ForegroundColor Cyan
Write-Host "  API文档: http://127.0.0.1:$availablePort/docs" -ForegroundColor Cyan

# 启动Python应用
$pythonProcess = Start-Process python -ArgumentList "cyber_audit_final.py" -NoNewWindow -PassThru

# 等待应用启动
Write-Host "`n5. 等待应用启动（10秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 6. 测试连接
Write-Host "`n6. 测试连接..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-RestMethod -Uri "http://127.0.0.1:$availablePort/health" -Method Get -TimeoutSec 5
    Write-Host "  ✓ 服务运行正常" -ForegroundColor Green
    Write-Host "    状态: $($healthCheck.status)" -ForegroundColor Green
    Write-Host "    版本: $($healthCheck.version)" -ForegroundColor Green
    
    # 创建测试脚本
    $testScript = @"
import requests
import json

print('服务信息:')
try:
    resp = requests.get('http://127.0.0.1:$availablePort/health')
    print(f'状态码: {resp.status_code}')
    print(f'响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}')
except Exception as e:
    print(f'错误: {e}')
"@
    
    $testScript | Out-File "test_connection.py" -Encoding UTF8
    
} catch {
    Write-Host "  ✗ 连接失败: $_" -ForegroundColor Red
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "启动完成!" -ForegroundColor Cyan
Write-Host "请保持此窗口运行..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

# 等待用户按Ctrl+C
try {
    Wait-Process -Id $pythonProcess.Id
} catch {
    Write-Host "服务已停止" -ForegroundColor Yellow
}