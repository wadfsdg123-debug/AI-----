
import sys
import os

# 将项目根目录添加到 sys.path，以便导入 core 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import LLMClient

class BaseAgent:
    def __init__(self, name):
        self.name = name
        # 默认使用 DeepSeek，因为它性价比最高且能力强
        self.llm = LLMClient(provider="deepseek")
        print(f"[{self.name}] Initialized.")

    def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement run method.")
