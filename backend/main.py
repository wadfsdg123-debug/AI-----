"""
Cyber Audit 项目主文件
FastAPI 后端服务
"""

import os
import json
import uuid
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# 导入自定义模块
from sandbox import SecureSandbox
from llm_engine import LLMAuditEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化应用
app = FastAPI(
    title="Cyber Audit API",
    description="自动化代码安全审计系统",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化沙箱
sandbox = SecureSandbox()

# 内存中存储任务状态（生产环境中应使用数据库）
audit_tasks: Dict[str, Dict] = {}

# 创建上传目录
import os
from pathlib import Path

# 创建上传目录 - 使用绝对路径
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def run_audit(task_id: str, file_path: str, language: str):
    """
    运行完整的审计任务
    """
    try:
        logger.info(f"开始审计任务 {task_id}，文件: {file_path}，语言: {language}")
        
        # 添加调试：检查文件是否存在
        logger.info(f"文件绝对路径: {os.path.abspath(file_path)}")
        logger.info(f"文件是否存在: {os.path.exists(file_path)}")
        logger.info(f"当前工作目录: {os.getcwd()}")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            task = audit_tasks.get(task_id)
            if task:
                task["status"] = "failed"
                task["error"] = f"文件不存在: {file_path}"
            return
        
        # ... 其余代码保持不变 ...    """
    运行完整的审计任务
    1. 静态分析（Bandit/Semgrep）
    2. LLM 深度分析
    3. 合并结果
    """
    try:
        logger.info(f"开始审计任务 {task_id}，文件: {file_path}，语言: {language}")
        
        # 1. 复制文件到沙箱
        sandbox.copy_to_sandbox(task_id, file_path)
        sandbox_path = sandbox.get_sandbox_path(task_id)
        
        # 2. 运行静态分析工具
        static_output = ""
        static_issues = []
        
        if language.lower() == "python":
            # 运行 Bandit 进行 Python 代码分析
            try:
                logger.info(f"运行 Bandit 分析...")
                
                # 构建 bandit 命令
                bandit_cmd = [
                    "bandit",
                    "-r", str(sandbox_path),
                    "-f", "json",
                    "-ll",  # 输出级别：低
                    "-ii",  # 忽略 info 级别的问题
                ]
                
                # 执行命令
                bandit_result = subprocess.run(
                    bandit_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2分钟超时
                )
                
                logger.info(f"Bandit 返回码: {bandit_result.returncode}")
                
                # 处理结果
                if bandit_result.returncode in [0, 1]:  # 0=成功，1=发现问题
                    if bandit_result.stdout.strip():
                        try:
                            bandit_output = json.loads(bandit_result.stdout)
                            static_output = json.dumps(bandit_output, ensure_ascii=False, indent=2)
                            
                            # 解析 Bandit 结果
                            if "results" in bandit_output:
                                for issue in bandit_output["results"]:
                                    static_issues.append({
                                        "tool": "bandit",
                                        "severity": issue.get("issue_severity", "medium").lower(),
                                        "confidence": issue.get("issue_confidence", "medium"),
                                        "category": issue.get("test_name", "Unknown"),
                                        "line": issue.get("line_number", 0),
                                        "description": issue.get("issue_text", ""),
                                        "suggestion": issue.get("more_info", ""),
                                        "file": issue.get("filename", "").replace(str(sandbox_path), "").lstrip("/")
                                    })
                                logger.info(f"Bandit 发现 {len(static_issues)} 个问题")
                            else:
                                logger.info("Bandit 未发现安全问题")
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"解析 Bandit JSON 失败: {e}")
                            static_output = f"解析 Bandit 输出失败: {e}\n原始输出:\n{bandit_result.stdout}"
                    else:
                        logger.warning("Bandit 无输出")
                else:
                    error_msg = f"Bandit 执行失败: {bandit_result.stderr}"
                    logger.error(error_msg)
                    static_output = error_msg
                    
            except subprocess.TimeoutExpired:
                error_msg = "Bandit 分析超时（120秒）"
                logger.error(error_msg)
                static_output = error_msg
            except Exception as e:
                error_msg = f"Bandit 分析异常: {e}"
                logger.error(error_msg)
                static_output = error_msg
        
        # 3. 读取代码内容用于 LLM 分析
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            logger.info(f"读取代码内容成功，长度: {len(code_content)} 字符")
        except Exception as e:
            logger.error(f"读取代码文件失败: {e}")
            code_content = f"# 读取文件失败: {e}"
        
        # 4. LLM 深度分析
        logger.info("开始 LLM 深度分析...")
        
        # 准备静态分析结果供 LLM 参考
        static_results_summary = None
        if static_issues:
            static_results_summary = {
                "tool": "bandit",
                "issue_count": len(static_issues),
                "issues_preview": static_issues[:3],  # 只传前3个问题供参考
                "summary": f"静态分析发现 {len(static_issues)} 个问题"
            }
        
        # 创建 LLM 引擎实例
        llm_engine = LLMAuditEngine()
        
        # 运行 LLM 分析
        llm_result = llm_engine.analyze_code(
            code=code_content,
            language=language,
            static_analysis_results=static_results_summary
        )
        
        # 5. 合并结果
        all_issues = []
        
        # 添加静态分析问题
        for issue in static_issues:
            issue["source"] = "static_analysis"
            issue["analysis_tool"] = "bandit"def run_audit(task_id: str, code_path: str, language: str):
    """
    执行审计任务（后台运行）
    """
    try:
        task = audit_tasks[task_id]
        
        # 1. 读取代码内容
        code_content = ""
        for root, dirs, files in os.walk(code_path):
            for file in files:
                if file.endswith(('.py', '.java', '.php', '.js', '.ts')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            code_content += f.read() + "\n"
                    except:
                        pass
        
        # 2. 使用沙箱运行静态分析工具
        container = sandbox.create_sandbox(task_id, code_path)
        
        # 3. 静态分析
        static_results = {}
        
        # 运行 Bandit（Python）
        if language == "python" or language == "auto":
            exit_code, output = sandbox.execute_command(
                container, 
                "bandit -r /sandbox/code -f json 2>/dev/null || echo '[]'"
            )
            try:
                static_results["bandit"] = json.loads(output) if output.startswith('[') else []
            except:
                static_results["bandit"] = []
        
        # 运行 Semgrep
        exit_code, output = sandbox.execute_command(
            container,
            "semgrep /sandbox/code --json 2>/dev/null || echo '{}'"
        )
        try:
            static_results["semgrep"] = json.loads(output) if output.startswith('{') else {}
        except:
            static_results["semgrep"] = {}
        
        # 4. LLM 深度分析
        from llm_engine import LLMAuditEngine
        llm_engine = LLMAuditEngine()
        
        llm_result = llm_engine.analyze_code(
            code=code_content,
            language=language,
            static_analysis_results=static_results
        )
        
        # 5. 清理沙箱
        sandbox.cleanup(task_id)
        
        # 6. 更新任务状态
        task["status"] = "completed"
        task["issues"] = llm_result.get("issues", [])
        task["summary"] = llm_result.get("summary", "审计完成")
        
    except Exception as e:
        audit_tasks[task_id]["status"] = "failed"
        audit_tasks[task_id]["summary"] = str(e)
        # 确保清理沙箱
        try:
            sandbox.cleanup(task_id)
        except:
            pass
            all_issues.append(issue)
        
        # 添加 LLM 分析问题
        llm_issues_count = 0
        for issue in llm_result.get("issues", []):
            # 避免重复问题（基于行号和描述）
            is_duplicate = False
            for existing_issue in all_issues:
                if (existing_issue.get("line") == issue.get("line") and 
                    existing_issue.get("description", "")[:50] == issue.get("description", "")[:50]):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                issue["source"] = "llm_analysis"
                issue["analysis_tool"] = "openai"
                all_issues.append(issue)
                llm_issues_count += 1
        
        # 6. 按严重性排序（high > medium > low）
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        # 7. 生成统计信息
        severity_stats = {"high": 0, "medium": 0, "low": 0}
        for issue in all_issues:
            sev = issue.get("severity", "low").lower()
            if sev in severity_stats:
                severity_stats[sev] += 1
        
        total_issues = len(all_issues)
        
        # 8. 更新任务状态
        task = audit_tasks[task_id]
        task["status"] = "completed"
        task["static_analysis_output"] = static_output
        task["llm_result"] = llm_result
        task["issues"] = all_issues
        task["summary"] = llm_result.get("summary", f"审计完成，发现 {total_issues} 个安全问题")
        
        # 添加统计信息
        task["statistics"] = {
            "total_issues": total_issues,
            "severity_distribution": severity_stats,
            "static_issues": len(static_issues),
            "llm_issues": llm_issues_count,
            "unique_issues": total_issues  # 去重后的问题数
        }
        
        task["completion_time"] = datetime.now().isoformat()
        
        logger.info(f"""
        审计任务 {task_id} 完成!
        总计发现 {total_issues} 个安全问题:
          - 高危: {severity_stats['high']}
          - 中危: {severity_stats['medium']}
          - 低危: {severity_stats['low']}
          - 静态分析: {len(static_issues)} 个
          - LLM分析: {llm_issues_count} 个
        """)
        
        # 9. 清理沙箱
        try:
            sandbox.cleanup(task_id)
            logger.info(f"已清理沙箱 {task_id}")
        except Exception as e:
            logger.warning(f"清理沙箱时出错: {e}")
        
    except Exception as e:
        logger.error(f"审计任务 {task_id} 失败: {e}", exc_info=True)
        task = audit_tasks.get(task_id)
        if task:
            task["status"] = "failed"
            task["error"] = str(e)
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
    # 验证文件类型
    allowed_extensions = [".py", ".java", ".js", ".ts", ".c", ".cpp", ".go", ".php", ".rb", ".cs"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    # 验证语言参数
    supported_languages = ["python", "java", "javascript", "typescript", "c", "cpp", "go", "php", "ruby", "csharp"]
    if language.lower() not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的语言。支持的语言: {', '.join(supported_languages)}"
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
        logger.info(f"文件上传成功: {file.filename} ({file_size} 字节), 任务ID: {task_id}")
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
    
    # 初始化任务状态
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
    task = audit_tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    # 格式化返回结果
    response = {
        "task_id": task["task_id"],
        "filename": task["filename"],
        "language": task["language"],
        "status": task["status"],
        "upload_time": task["upload_time"],
        "completion_time": task.get("completion_time"),
        "summary": task.get("summary", "分析中..."),
        "statistics": task.get("statistics", {}),
        "issues": task.get("issues", []),
        "error": task.get("error")
    }
    
    # 如果任务失败，返回错误信息
    if task["status"] == "failed":
        return JSONResponse(
            status_code=500,
            content={
                **response,
                "error": task.get("error", "未知错误")
            }
        )
    
    # 如果任务还在进行中
    if task["status"] != "completed":
        return {
            **response,
            "message": "分析仍在进行中，请稍后刷新",
            "progress": "running"
        }
    
    return response


@app.get("/api/audit/tasks")
async def list_audit_tasks(limit: int = 10, status: Optional[str] = None):
    """
    列出所有审计任务
    """
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
            "summary": task.get("summary", "")[:100]  # 只取前100字符
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
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cyber-audit-api",
        "version": "1.0.0",
        "active_tasks": len([t for t in audit_tasks.values() if t.get("status") == "running"]),
        "total_tasks": len(audit_tasks)
    }


@app.get("/")
async def root():
    """
    根端点，提供 API 信息
    """
    return {
        "message": "Cyber Audit API 服务运行中",
        "version": "1.0.0",
        "endpoints": {
            "上传文件": "POST /api/audit/upload",
            "获取结果": "GET /api/audit/result/{task_id}",
            "列出任务": "GET /api/audit/tasks",
            "删除任务": "DELETE /api/audit/task/{task_id}",
            "健康检查": "GET /health"
        },
        "usage": "使用 curl 或 Postman 测试 API，或访问 /docs 查看交互式文档"
    }


@app.get("/docs")
async def get_docs():
    """
    重定向到 Swagger UI
    """
    return FileResponse("static/docs.html") if os.path.exists("static/docs.html") else {
        "message": "Swagger UI 可用: 访问 http://localhost:8000/docs 或 /redoc"
    }


# 应用启动时初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("Cyber Audit API 正在启动...")
    
    # 检查必要工具
    try:
        # 检查 bandit 是否安装
        subprocess.run(["bandit", "--version"], capture_output=True, check=True)
        logger.info("✓ Bandit 已安装")
    except Exception:
        logger.warning("⚠ Bandit 未安装，Python 代码的静态分析将不可用")
        logger.info("  安装命令: pip install bandit")
    
    # 检查 OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        logger.info("✓ OpenAI API Key 已配置")
    else:
        logger.warning("⚠ OpenAI API Key 未配置，LLM 分析将使用模拟数据")
        logger.info("  请在 .env 文件中配置 OPENAI_API_KEY")
    
    # 清理旧的临时文件
    cleanup_old_files()
    
    logger.info(f"上传目录: {UPLOAD_DIR.absolute()}")
    logger.info("服务已启动，等待请求...")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("正在关闭 Cyber Audit API...")
    
    # 清理所有沙箱
    sandbox.cleanup_all()
    
    # 清理临时文件
    cleanup_uploaded_files()
    
    logger.info("服务已关闭")


def cleanup_old_files(max_age_hours: int = 24):
    """清理旧的上传文件"""
    try:
        current_time = datetime.now().timestamp()
        for file_path in UPLOAD_DIR.glob("*"):
            # 获取文件修改时间
            mtime = file_path.stat().st_mtime
            age_hours = (current_time - mtime) / 3600
            
            if age_hours > max_age_hours:
                file_path.unlink()
                logger.debug(f"已清理旧文件: {file_path.name}")
    except Exception as e:
        logger.warning(f"清理旧文件时出错: {e}")


def cleanup_uploaded_files():
    """清理所有上传的文件"""
    try:
        for file_path in UPLOAD_DIR.glob("*"):
            file_path.unlink()
        logger.info(f"已清理上传目录: {UPLOAD_DIR}")
    except Exception as e:
        logger.warning(f"清理上传目录时出错: {e}")


# 运行应用
if __name__ == "__main__":
    import uvicorn
    
    # 创建 static 目录用于存放文档
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )