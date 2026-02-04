"""
FastAPI 应用入口
主控后端 - 负责路由、中间件、全局配置
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from api import upload, websocket, report, task, health
from database import init_db

# 提前创建必需的目录（在导入时就创建）
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.report_dir, exist_ok=True)
os.makedirs("./data", exist_ok=True)
logger.info("✅ 数据目录初始化完成")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动 AI 代码审计系统...")
    
    # 初始化数据库
    await init_db()
    
    logger.info(f"✅ 系统启动完成 - 监听 {settings.backend_host}:{settings.backend_port}")
    
    yield
    
    # 关闭时执行
    logger.info("⏹️  关闭系统...")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 代码审计系统",
    description="基于 LLM 多 Agent 协同的自动化代码审计平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["文件上传"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(report.router, prefix="/api", tags=["报告管理"])
app.include_router(task.router, prefix="/api", tags=["任务管理"])
app.include_router(health.router, prefix="/api", tags=["健康检查"])

# 静态文件服务（报告下载）
app.mount("/reports", StaticFiles(directory=settings.report_dir), name="reports")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI 代码审计系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

