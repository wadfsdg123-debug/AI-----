"""
Cyber Audit 最终修复版�?
解决所有已知问�?
"""

import os
import json
import uuid
import logging
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cyber Audit API",
    description="自动化代码安全审计系�?,
    version="2.0.0-final"
)

# 使用绝对路径
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 导入沙箱模块
try:
    from sandbox import SecureSandbox
    sandbox = SecureSandbox()
    logger.info("�?Sandbox 模块加载成功")
except Exception as e:
    logger.error(f"�?Sandbox 模块加载失败: {e}")
    raise

# 导入 LLM 引擎
try:
    from llm_engine import LLMAuditEngine
    logger.info("�?LLM Engine 模块加载成功")
except Exception as e:
    logger.error(f"�?LLM Engine 模块加载失败: {e}")
    raise

# 内存存储 - 使用线程安全的方�?
audit_tasks: Dict[str, Dict] = {}
tasks_lock = threading.Lock()

def run_audit(task_id: str, file_path: str, language: str):
    """运行审计任务"""
    logger.info(f"[{task_id}] 开始审计任�?)
    
    try:
        # 1. 验证文件存在
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"文件不存�? {file_path}"
            logger.error(f"[{task_id}] {error_msg}")
            with tasks_lock:
                if task_id in audit_tasks:
                    audit_tasks[task_id].update({
                        "status": "failed",
                        "error": error_msg,
                        "completion_time": datetime.now().isoformat()
                    })
            return
        
        # 2. 更新状�?
        with tasks_lock:
            if task_id in audit_tasks:
                audit_tasks[task_id]["status"] = "running"
        
        # 3. 复制到沙�?
        try:
            sandbox_file = sandbox.copy_to_sandbox(task_id, file_path)
            logger.info(f"[{task_id}] 文件已复制到沙箱: {sandbox_file}")
        except Exception as e:
            error_msg = f"沙箱操作失败: {e}"
            logger.error(f"[{task_id}] {error_msg}")
            with tasks_lock:
                if task_id in audit_tasks:
                    audit_tasks[task_id].update({
                        "status": "failed",
                        "error": error_msg,
                        "completion_time": datetime.now().isoformat()
                    })
            return
        
        # 4. 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # 5. 静态分�?
        issues = []
        if language.lower() == "python":
            try:
                logger.info(f"[{task_id}] 运行 Bandit 分析...")
                
                # 使用临时文件运行 bandit
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(code_content)
                    tmp_path = tmp.name
                
                result = subprocess.run(
                    ["bandit", "-f", "json", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                os.unlink(tmp_path)
                
                if result.returncode in [0, 1]:
                    if result.stdout.strip():
                        try:
                            data = json.loads(result.stdout)
                            if "results" in data:
                                for issue in data["results"]:
                                    issues.append({
                                        "tool": "bandit",
                                        "severity": issue.get("issue_severity", "medium").lower(),
                                        "category": issue.get("test_name", "Unknown"),
                                        "line": issue.get("line_number", 0),
                                        "description": issue.get("issue_text", ""),
                                        "source": "static_analysis"
                                    })
                                logger.info(f"[{task_id}] Bandit 发现 {len(issues)} 个问�?)
                        except json.JSONDecodeError as e:
                            logger.warning(f"[{task_id}] 解析 Bandit JSON 失败: {e}")
            except Exception as e:
                logger.warning(f"[{task_id}] Bandit 分析失败: {e}")
        
        # 6. LLM 分析
        try:
            logger.info(f"[{task_id}] 开�?LLM 分析...")
            llm_engine = LLMAuditEngine()
            llm_result = llm_engine.analyze_code(
                code=code_content,
                language=language,
                static_analysis_results={"issues": issues[:3]} if issues else None
            )
            
            llm_issues = llm_result.get("issues", [])
            for issue in llm_issues:
                issue["source"] = "llm_analysis"
                issues.append(issue)
                
            logger.info(f"[{task_id}] LLM 分析完成，发�?{len(llm_issues)} 个问�?)
                
        except Exception as e:
            logger.error(f"[{task_id}] LLM 分析失败: {e}")
            llm_result = {"summary": f"LLM 分析失败: {e}", "issues": []}
        
        # 7. 统计严重�?
        severity_stats = {"high": 0, "medium": 0, "low": 0}
        for issue in issues:
            sev = issue.get("severity", "low").lower()
            if sev in severity_stats:
                severity_stats[sev] += 1
        
        # 8. 更新结果
        with tasks_lock:
            if task_id in audit_tasks:
                audit_tasks[task_id].update({
                    "status": "completed",
                    "issues": issues,
                    "summary": llm_result.get("summary", f"分析完成，发�?{len(issues)} 个问�?),
                    "completion_time": datetime.now().isoformat(),
                    "statistics": {
                        "total_issues": len(issues),
                        "severity_distribution": severity_stats,
                        "static_issues": len([i for i in issues if i.get("source") == "static_analysis"]),
                        "llm_issues": len([i for i in issues if i.get("source") == "llm_analysis"])
                    }
                })
        
        logger.info(f"[{task_id}] 审计完成，发�?{len(issues)} 个问�?)
        
        # 9. 清理沙箱
        try:
            sandbox.cleanup(task_id)
            logger.info(f"[{task_id}] 已清理沙�?)
        except Exception as e:
            logger.warning(f"[{task_id}] 清理沙箱失败: {e}")
        
    except Exception as e:
        logger.error(f"[{task_id}] 审计任务异常: {e}")
        logger.error(traceback.format_exc())
        
        with tasks_lock:
            if task_id in audit_tasks:
                audit_tasks[task_id].update({
                    "status": "failed",
                    "error": f"{str(e)}\n{traceback.format_exc()[:500]}",
                    "completion_time": datetime.now().isoformat()
                })

@app.post("/api/audit/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("python")
):
    """上传文件"""
    logger.info(f"收到上传请求: {file.filename}, 语言: {language}")
    
    # 验证文件类型
    allowed_extensions = [".py", ".java", ".js", ".ts", ".c", ".cpp", ".go", ".php"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())[:8]
    
    # 保存文件
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建任务
    with tasks_lock:
        audit_tasks[task_id] = {
            "task_id": task_id,
            "filename": file.filename,
            "language": language,
            "status": "pending",
            "upload_time": datetime.now().isoformat(),
            "file_path": str(file_path),
            "issues": [],
            "summary": "等待分析"
        }
    
    logger.info(f"任务创建成功: {task_id}")
    
    # 启动后台任务
    background_tasks.add_task(run_audit, task_id, str(file_path), language)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "文件上传成功，开始安全审�?,
        "estimated_time": "�?-2分钟",
        "result_url": f"/api/audit/result/{task_id}"
    }

@app.get("/api/audit/result/{task_id}")
async def get_result(task_id: str):
    """获取结果"""
    with tasks_lock:
        task = audit_tasks.get(task_id)
    
    if not task:
        logger.warning(f"请求不存在的任务: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在或已过�?)
    
    return task

@app.get("/api/audit/tasks")
async def list_tasks(limit: int = 10, status: Optional[str] = None):
    """列出所有任�?""
    with tasks_lock:
        tasks_list = list(audit_tasks.values())
    
    # 按上传时间排�?
    tasks_list.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
    
    # 筛选状�?
    if status:
        tasks_list = [t for t in tasks_list if t.get("status") == status]
    
    # 限制数量
    tasks_list = tasks_list[:limit]
    
    # 简化响�?
    simplified_tasks = []
    for task in tasks_list:
        simplified_tasks.append({
            "task_id": task["task_id"],
            "filename": task["filename"],
            "language": task["language"],
            "status": task["status"],
            "upload_time": task["upload_time"],
            "completion_time": task.get("completion_time"),
            "issue_count": len(task.get("issues", [])),
            "summary": task.get("summary", "")[:100]
        })
    
    return {
        "total_tasks": len(audit_tasks),
        "returned_tasks": len(simplified_tasks),
        "tasks": simplified_tasks
    }

@app.delete("/api/audit/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    with tasks_lock:
        task = audit_tasks.get(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存�?)
        
        # 清理文件
        file_path = task.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"已删除文�? {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        # 清理沙箱
        try:
            sandbox.cleanup(task_id)
        except:
            pass
        
        # 从内存中移除
        del audit_tasks[task_id]
    
    return {
        "message": f"任务 {task_id} 已删�?,
        "deleted": True
    }

@app.get("/health")
async def health():
    """健康检�?""
    with tasks_lock:
        active_tasks = len([t for t in audit_tasks.values() if t.get("status") == "running"])
        total_tasks = len(audit_tasks)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cyber-audit-api",
        "version": "2.0.0-final",
        "active_tasks": active_tasks,
        "total_tasks": total_tasks
    }

@app.get("/")
async def root():
    """根端�?""
    return {
        "message": "Cyber Audit API 服务运行�?(最终版�?",
        "version": "2.0.0-final",
        "endpoints": {
            "上传文件": "POST /api/audit/upload",
            "获取结果": "GET /api/audit/result/{task_id}",
            "列出任务": "GET /api/audit/tasks",
            "删除任务": "DELETE /api/audit/task/{task_id}",
            "健康检�?: "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # 启动信息
    logger.info("=" * 60)
    logger.info("Cyber Audit API 2.0.0-final 正在启动...")
    logger.info(f"上传目录: {UPLOAD_DIR}")
    logger.info(f"基础目录: {BASE_DIR}")
    logger.info("=" * 60)
    
    # 检�?Bandit
    try:
        subprocess.run(["bandit", "--version"], capture_output=True, check=True)
        logger.info("�?Bandit 已安�?)
    except:
        logger.warning("�?Bandit 未安装，Python 静态分析将不可�?)
    
    # 启动服务�?
       uvicorn.run(
        app,
        host="127.0.0.1",
        port=8004,  # 改为8003
        log_level="info"
    )
    )
