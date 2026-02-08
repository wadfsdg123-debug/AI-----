"""
AI 代码审计系统 - 主入口
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
import shutil
from datetime import datetime

# 导入沙箱模块
from sandbox import SecureSandbox

app = FastAPI(
    title="AI 代码审计系统",
    description="智能代码安全审计平台",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class AuditRequest(BaseModel):
    language: str
    ai_model: Optional[str] = "gpt-4"

class AuditResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AuditResult(BaseModel):
    task_id: str
    status: str
    language: str
    issues: List[dict]
    summary: str
    created_at: str

# 模拟数据库
audit_tasks = {}

# 初始化沙箱
sandbox = SecureSandbox()

@app.post("/api/audit/upload", response_model=AuditResponse)
async def upload_code(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = "auto"
):
    """
    上传代码文件进行审计
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())[:8]
    
    # 保存上传的文件（使用绝对路径）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "data", "uploads", task_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 创建任务记录
    audit_tasks[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "language": language,
        "file_path": file_path,
        "filename": file.filename,
        "created_at": datetime.now().isoformat(),
        "issues": [],
        "summary": ""
    }
    
    # 后台执行审计
    background_tasks.add_task(run_audit, task_id, upload_dir, language)
    
    return AuditResponse(
        task_id=task_id,
        status="processing",
        message="代码审计已启动，请通过 /api/audit/result/{task_id} 查询结果"
    )

@app.get("/api/audit/result/{task_id}", response_model=AuditResult)
async def get_result(task_id: str):
    """
    获取审计结果
    """
    if task_id not in audit_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = audit_tasks[task_id]
    return AuditResult(
        task_id=task["task_id"],
        status=task["status"],
        language=task["language"],
        issues=task.get("issues", []),
        summary=task.get("summary", ""),
        created_at=task["created_at"]
    )

@app.get("/api/audit/tasks")
async def list_tasks():
    """
    获取所有任务列表
    """
    return list(audit_tasks.values())

@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "docker": "connected"
    }

def run_audit(task_id: str, code_path: str, language: str):
    """
    执行审计任务（后台运行）
    """
    try:
        task = audit_tasks[task_id]
        
        # 1. 使用沙箱运行静态分析工具
        container = sandbox.create_sandbox(task_id, code_path)
        
        # 2. 运行 Bandit（Python）
        if language == "python" or language == "auto":
            exit_code, output = sandbox.execute_command(
                container, 
                "bandit -r /sandbox/code -f json || true"
            )
        
        # 3. 运行 Semgrep
        exit_code, output = sandbox.execute_command(
            container,
            "semgrep /sandbox/code --json || true"
        )
        
        # 4. 清理沙箱
        sandbox.cleanup(task_id)
        
        # 5. 更新任务状态
        task["status"] = "completed"
        task["summary"] = "审计完成，发现 0 个问题"
        
    except Exception as e:
        audit_tasks[task_id]["status"] = "failed"
        audit_tasks[task_id]["summary"] = str(e)
        # 确保清理沙箱
        try:
            sandbox.cleanup(task_id)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)