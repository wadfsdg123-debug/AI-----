"""
最小工作版本 - 去掉所有复杂功能
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 最简单的任务存储
tasks = {}

def simple_task(task_id: str, file_path: str, language: str):
    """最简单的后台任务"""
    logger.info(f"后台任务开始: {task_id}")
    
    try:
        # 模拟工作
        import time
        time.sleep(2)
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新任务状态
        tasks[task_id].update({
            "status": "completed",
            "summary": f"分析完成，文件大小: {len(content)} 字节",
            "issues": [{"test": "success"}],
            "completion_time": datetime.now().isoformat()
        })
        
        logger.info(f"后台任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"后台任务失败: {e}")
        tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completion_time": datetime.now().isoformat()
        })

@app.post("/api/audit/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("python")
):
    """上传文件"""
    task_id = str(uuid.uuid4())[:8]
    
    # 保存文件
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{task_id}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建任务
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "language": language,
        "status": "pending",
        "upload_time": datetime.now().isoformat(),
        "file_path": file_path
    }
    
    logger.info(f"任务创建: {task_id}")
    
    # 启动后台任务
    background_tasks.add_task(simple_task, task_id, file_path, language)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "文件上传成功"
    }

@app.get("/api/audit/result/{task_id}")
async def get_result(task_id: str):
    """获取结果"""
    if task_id not in tasks:
        return JSONResponse(
            status_code=404,
            content={"error": "任务不存在"}
        )
    
    return tasks[task_id]

@app.get("/health")
async def health():
    return {"status": "healthy", "total_tasks": len(tasks)}

if __name__ == "__main__":
    import uvicorn
    print("启动最小工作版本...")
    uvicorn.run(app, host="127.0.0.1", port=8001)  # 使用不同端口