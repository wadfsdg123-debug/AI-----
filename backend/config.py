"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 端口配置
    PORT = int(os.getenv("PORT", 8000))
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./audit_results.db")
    
    @classmethod
    def print_config(cls):
        """打印配置信息"""
        print("=" * 50)
        print("Cyber Audit 配置")
        print("=" * 50)
        print(f"端口: {cls.PORT}")
        print(f"OpenAI API Key: {'已设置' if cls.OPENAI_API_KEY else '未设置'}")
        print(f"模型: {cls.OPENAI_MODEL}")
        print(f"上传目录: {cls.UPLOAD_DIR}")
        print(f"最大文件大小: {cls.MAX_FILE_SIZE / 1024 / 1024} MB")
        print("=" * 50)

if __name__ == "__main__":
    Config.print_config()