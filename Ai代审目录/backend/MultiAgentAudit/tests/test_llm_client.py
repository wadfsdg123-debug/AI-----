
import unittest
import os
import sys

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import LLMClient

class TestLLMClient(unittest.TestCase):
    def setUp(self):
        # 确保不使用真实 Key 进行 Mock 测试
        self.original_key = os.environ.get("LLM_API_KEY")
        if "LLM_API_KEY" in os.environ:
            del os.environ["LLM_API_KEY"]
        
    def tearDown(self):
        if self.original_key:
            os.environ["LLM_API_KEY"] = self.original_key

    def test_mock_response_ops(self):
        client = LLMClient(api_key=None) # Force mock
        response = client.chat("你是一个DevOps专家...应用指纹识别", "分析文件列表")
        self.assertIn("docker_config", response)
        self.assertIn("python", response)

    def test_mock_response_analyze(self):
        client = LLMClient(api_key=None)
        response = client.chat("你是一个高级代码审计专家", "审计代码")
        self.assertIn("vulnerabilities", response)
        self.assertIn("SQL Injection", response)

if __name__ == '__main__':
    unittest.main()
