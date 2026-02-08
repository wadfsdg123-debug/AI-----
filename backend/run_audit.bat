@echo off
echo 停止可能存在的uvicorn进程...
taskkill /im uvicorn.exe /f 2>nul
taskkill /im python.exe /f 2>nul

echo 启动 Cyber Audit API...
python cyber_audit_final.py

pause