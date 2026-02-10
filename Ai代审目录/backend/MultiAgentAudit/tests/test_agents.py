
import unittest
import os
import sys
import json
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ops_agent import OpsAgent
from agents.analyze_agent import AnalyzeAgent
from agents.hacker_agent import HackerAgent

class TestAgents(unittest.TestCase):
    
    @patch('core.llm_client.LLMClient.chat')
    def test_ops_agent(self, mock_chat):
        # 模拟 LLM 返回
        mock_response = json.dumps({
            "language": "python",
            "framework": "flask"
        })
        mock_chat.return_value = mock_response
        
        agent = OpsAgent()
        # 创建一个临时目录用于测试
        test_dir = os.path.join(os.getcwd(), "tests", "temp_app")
        os.makedirs(test_dir, exist_ok=True)
        with open(os.path.join(test_dir, "app.py"), "w") as f:
            f.write("print('hello')")
            
        result = agent.run(test_dir)
        
        self.assertEqual(result["language"], "python")
        
        # 清理
        import shutil
        shutil.rmtree(test_dir)

    @patch('core.llm_client.LLMClient.chat')
    def test_analyze_agent(self, mock_chat):
        mock_response = json.dumps({
            "vulnerabilities": [{
                "type": "XSS",
                "severity": "Medium",
                "code_snippet": "echo $_GET['a']"
            }]
        })
        mock_chat.return_value = mock_response
        
        agent = AnalyzeAgent()
        env_data = {"language": "php"}
        
        # 模拟文件
        test_dir = os.path.join(os.getcwd(), "tests", "temp_php")
        os.makedirs(test_dir, exist_ok=True)
        with open(os.path.join(test_dir, "vuln.php"), "w") as f:
            f.write("<?php echo $_GET['a']; ?>")
            
        result = agent.run(test_dir, env_data)
        
        self.assertEqual(len(result["vulnerabilities"]), 1)
        self.assertEqual(result["vulnerabilities"][0]["type"], "XSS")
        
        import shutil
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()
