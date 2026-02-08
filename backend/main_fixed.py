"""
修复版本的 Cyber Audit API
添加了详细的错误处理和调试信息
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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# 配置日志 - 更详细
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化应用
app = FastAPI(
    title="Cyber Audit API",
    description="自动化代码安全审计系统",
    version="1.1.0-fixed"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 尝试导入自定义模块，如果失败则创建简单版本
try:
    from sandbox import SecureSandbox
    sandbox = SecureSandbox()
    logger.info("✓ Sandbox 模块加载成功")
    
    # 测试沙箱功能
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("test")')
        test_file = f.name
    
    try:
        sandbox.copy_to_sandbox("test_init", test_file)
        logger.info("✓ Sandbox 功能测试通过")
    finally:
        os.unlink(test_file)
        
except Exception as e:
    logger.error(f"✗ Sandbox 模块加载失败: {e}")
    logger.error("需要修复 sandbox.py 文件")
    raise
try:
    from llm_engine import LLMAuditEngine
    logger.info("✓ LLM Engine 模块加载成功")
except Exception as e:
    logger.warning(f"⚠ LLM Engine 模块加载失败: {e}")
    
    class SimpleLLMAuditEngine:
        def analyze_code(self, code, language, static_analysis_results=None):
            return {
                "issues": [
                    {
                        "severity": "medium",
                        "category": "模块加载失败",
                        "line": 1,
                        "description": f"LLM 引擎加载失败: {e}",
                        "suggestion": "检查 llm_engine.py 文件"
                    }
                ],
                "summary": "LLM 分析模块加载失败，使用模拟数据",
                "confidence": "low"
            }
    
    LLMAuditEngine = SimpleLLMAuditEngine

# 内存中存储任务状态 - 使用线程安全的方式
import threading
audit_tasks: Dict[str, Dict] = {}
tasks_lock = threading.Lock()

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def run_audit(task_id: str, file_path: str, language: str):
    """
    运行完整的审计任务 - 修复版本
    """
    logger.info(f"========== 开始审计任务 {task_id} ==========")
    logger.info(f"文件: {file_path}")
    logger.info(f"语言: {language}")
    
    try:
        # 0. 确保任务在字典中
        with tasks_lock:
            if task_id not in audit_tasks:
                logger.error(f"任务 {task_id} 不存在于 audit_tasks 中!")
                return
            task = audit_tasks[task_id]
            task["status"] = "running"
        
        logger.debug(f"任务状态已更新为 running")
        
        # 1. 验证文件存在
        if not os.path.exists(file_path):
            error_msg = f"文件不存在: {file_path}"
            logger.error(error_msg)
            with tasks_lock:
                task["status"] = "failed"
                task["error"] = error_msg
            return
        
        logger.debug(f"文件存在，大小: {os.path.getsize(file_path)} 字节")
        
        # 2. 复制文件到沙箱
        try:
            logger.debug("复制文件到沙箱...")
            sandbox.copy_to_sandbox(task_id, file_path)
            sandbox_path = sandbox.get_sandbox_path(task_id)
            logger.debug(f"沙箱路径: {sandbox_path}")
        except Exception as e:
            error_msg = f"沙箱操作失败: {e}"
            logger.error(error_msg)
            with tasks_lock:
                task["status"] = "failed"
                task["error"] = error_msg
            return
        
        # 3. 运行静态分析工具
        static_output = ""
        static_issues = []
        
        if language.lower() == "python":
            try:
                logger.info("运行 Bandit 分析...")
                
                # 检查 bandit 是否可用
                try:
                    subprocess.run(["bandit", "--version"], capture_output=True, check=True)
                except:
                    logger.warning("Bandit 不可用，跳过静态分析")
                    static_output = "Bandit 未安装或不可用"
                else:
                    # 运行 bandit
                    bandit_cmd = [
                        "bandit",
                        "-r", str(sandbox_path),
                        "-f", "json",
                        "-ll",  # 输出级别：低
                    ]
                    
                    logger.debug(f"执行命令: {' '.join(bandit_cmd)}")
                    
                    result = subprocess.run(
                        bandit_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    logger.debug(f"Bandit 返回码: {result.returncode}")
                    logger.debug(f"Bandit stdout 长度: {len(result.stdout)}")
                    logger.debug(f"Bandit stderr: {result.stderr[:200] if result.stderr else '无'}")
                    
                    if result.stdout.strip():
                        try:
                            bandit_data = json.loads(result.stdout)
                            static_output = json.dumps(bandit_data, indent=2, ensure_ascii=False)
                            
                            if "results" in bandit_data:
                                for issue in bandit_data["results"]:
                                    static_issues.append({
                                        "tool": "bandit",
                                        "severity": issue.get("issue_severity", "medium").lower(),
                                        "confidence": issue.get("issue_confidence", "medium"),
                                        "category": issue.get("test_name", "Unknown"),
                                        "line": issue.get("line_number", 0),
                                        "description": issue.get("issue_text", ""),
                                        "suggestion": issue.get("more_info", "")
                                    })
                                logger.info(f"Bandit 发现 {len(static_issues)} 个问题")
                        except json.JSONDecodeError as e:
                            logger.error(f"解析 Bandit JSON 失败: {e}")
                            static_output = f"JSON解析失败: {e}\n原始输出:\n{result.stdout[:500]}"
                    else:
                        logger.info("Bandit 无输出")
                        
            except subprocess.TimeoutExpired:
                logger.warning("Bandit 分析超时")
                static_output = "Bandit 分析超时（60秒）"
            except Exception as e:
                logger.error(f"Bandit 分析异常: {e}")
                static_output = f"Bandit 异常: {e}"
        
        # 4. 读取代码内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            logger.debug(f"读取代码成功，长度: {len(code_content)} 字符")
        except Exception as e:
            logger.error(f"读取代码失败: {e}")
            code_content = "# 读取文件失败"
        
        # 5. LLM 分析
        logger.info("开始 LLM 分析...")
        try:
            llm_engine = LLMAuditEngine()
            llm_result = llm_engine.analyze_code(
                code=code_content,
                language=language,
                static_analysis_results={"issues": static_issues[:3]} if static_issues else None
            )
            logger.info(f"LLM 分析完成，返回 {len(llm_result.get('issues', []))} 个问题")
        except Exception as e:
            logger.error(f"LLM 分析失败: {e}")
            llm_result = {
                "issues": [],
                "summary": f"LLM 分析失败: {e}",
                "error": str(e)
            }
        
        # 6. 合并结果
        all_issues = []
        
        # 添加静态分析问题
        for issue in static_issues:
            issue["source"] = "static_analysis"
            all_issues.append(issue)
        
        # 添加 LLM 分析问题
        llm_issues = llm_result.get("issues", [])
        for issue in llm_issues:
            issue["source"] = "llm_analysis"
            all_issues.append(issue)
        
        # 7. 更新任务状态
        with tasks_lock:
            task["status"] = "completed"
            task["static_analysis_output"] = static_output
            task["llm_result"] = llm_result
            task["issues"] = all_issues
            task["summary"] = llm_result.get("summary", f"审计完成，发现 {len(all_issues)} 个问题")
            task["completion_time"] = datetime.now().isoformat()
            task["statistics"] = {
                "total_issues": len(all_issues),
                "static_issues": len(static_issues),
                "llm_issues": len(llm_issues),
                "severity_distribution": {
                    "high": len([i for i in all_issues if i.get("severity") == "high"]),
                    "medium": len([i for i in all_issues if i.get("severity") == "medium"]),
                    "low": len([i for i in all_issues if i.get("severity") == "low"])
                }
            }
        
        logger.info(f"========== 审计任务 {task_id} 完成 ==========")
        logger.info(f"总计发现 {len(all_issues)} 个安全问题")
        
        # 8. 清理沙箱
        try:
            sandbox.cleanup(task_id)
            logger.debug(f"已清理沙箱 {task_id}")
        except Exception as e:
            logger.warning(f"清理沙箱失败: {e}")
            
    except Exception as e:
        logger.error(f"审计任务 {task_id} 发生未捕获的异常:")
        logger.error(traceback.format_exc())
        
        with tasks_lock:
            if task_id in audit_tasks:
                task = audit_tasks[task_id]
                task["status"] = "failed"
                task["error"] = f"{str(e)}\n\n{traceback.format_exc()}"
                task["completion_time"] = datetime.now().isoformat()


@app.post("/api/audit/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("python")
):
    """
    上传代码文件进行安全审计
    """
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
    
    # 保存上传的文件
    upload_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    try:
        content = await file.read()
        with open(upload_path, "wb") as f:
            f.write(content)
        
        file_size = len(content)
        logger.info(f"文件保存成功: {upload_path} ({file_size} 字节)")
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
    
    # 初始化任务状态
    with tasks_lock:
        audit_tasks[task_id] = {
            "task_id": task_id,
            "filename": file.filename,
            "language": language,
            "status": "pending",
            "upload_time": datetime.now().isoformat(),
            "file_size": file_size,
            "file_path": str(upload_path),
            "issues": [],
            "summary": "等待分析",
            "error": None
        }
    
    logger.info(f"任务创建成功: {task_id}")
    
    # 在后台运行审计任务
    background_tasks.add_task(run_audit, task_id, str(upload_path), language)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "文件上传成功，开始安全审计",
        "estimated_time": "约1-3分钟",
        "result_url": f"/api/audit/result/{task_id}"
    }


@app.get("/api/audit/result/{task_id}")
async def get_audit_result(task_id: str):
    """
    获取审计结果
    """
    with tasks_lock:
        task = audit_tasks.get(task_id)
    
    if not task:
        logger.warning(f"请求不存在的任务: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    return task


@app.get("/api/audit/tasks")
async def list_audit_tasks(limit: int = 10, status: Optional[str] = None):
    """
    列出所有审计任务
    """
    with tasks_lock:
        tasks = list(audit_tasks.values())
    
    # 按上传时间排序（最新的在前）
    tasks.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
    
    # 筛选状态
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    
    # 限制数量
    tasks = tasks[:limit]
    
    # 简化响应
    simplified_tasks = []
    for task in tasks:
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
async def delete_audit_task(task_id: str):
    """
    删除审计任务
    """
    with tasks_lock:
        task = audit_tasks.get(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 清理文件
        file_path = task.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        # 从内存中移除
        del audit_tasks[task_id]
    
    return {
        "message": f"任务 {task_id} 已删除",
        "deleted": True
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    with tasks_lock:
        active_tasks = len([t for t in audit_tasks.values() if t.get("status") == "running"])
        total_tasks = len(audit_tasks)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cyber-audit-api",
        "version": "1.1.0-fixed",
        "active_tasks": active_tasks,
        "total_tasks": total_tasks
    }


@app.get("/")
async def root():
    """
    根端点，提供 API 信息
    """
    return {
        "message": "Cyber Audit API 服务运行中 (修复版本)",
        "version": "1.1.0-fixed",
        "endpoints": {
            "上传文件": "POST /api/audit/upload",
            "获取结果": "GET /api/audit/result/{task_id}",
            "列出任务": "GET /api/audit/tasks",
            "删除任务": "DELETE /api/audit/task/{task_id}",
            "健康检查": "GET /health"
        },
        "usage": "使用 curl 或 Postman 测试 API，或访问 /docs 查看交互式文档"
    }


# 应用启动时初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("=" * 50)
    logger.info("Cyber Audit API (修复版本) 正在启动...")
    logger.info("=" * 50)
    
    # 检查必要工具
    try:
        subprocess.run(["bandit", "--version"], capture_output=True, check=True)
        logger.info("✓ Bandit 已安装")
    except Exception:
        logger.warning("⚠ Bandit 未安装，Python 代码的静态分析将不可用")
    
    # 检查上传目录
    logger.info(f"上传目录: {UPLOAD_DIR.absolute()}")
    
    # 清理旧的日志文件
    if os.path.exists("audit_debug.log"):
        try:
            with open("audit_debug.log", "w") as f:
                f.write("")  # 清空日志文件
            logger.info("✓ 已清理旧日志文件")
        except:
            pass
    
    logger.info("服务已启动，等待请求...")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("正在关闭 Cyber Audit API...")
    
    # 清理沙箱
    try:
        sandbox.cleanup_all()
    except:
        pass
    
    logger.info("服务已关闭")


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        "main_fixed:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )