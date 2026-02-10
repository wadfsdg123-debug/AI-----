
import os
import json
import logging
from agents.base_agent import BaseAgent
from core.prompts import Prompts

class OpsAgent(BaseAgent):
    def __init__(self):
        super().__init__("OpsAgent")

    def run(self, target_dir):
        """
        分析目标目录，识别环境。
        """
        print(f"[{self.name}] Scanning directory: {target_dir}")
        
        # 1. 收集文件列表
        file_list = []
        file_contents = ""
        
        # 处理单文件情况
        if os.path.isfile(target_dir):
            file = os.path.basename(target_dir)
            if file.endswith(('.py', '.php', '.java', '.js', '.ts', '.go', '.c', '.cpp', '.rb', '.rs', '.cs', 'package.json', 'requirements.txt', 'Dockerfile')):
                file_list.append(target_dir)
                try:
                    with open(target_dir, 'r', encoding='utf-8') as f:
                        content = f.read(2000)
                        file_contents += f"\n--- File: {file} ---\n{content}\n"
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        else:
            # 处理目录情况
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    if file.endswith(('.py', '.php', '.java', '.js', '.ts', '.go', '.c', '.cpp', '.rb', '.rs', '.cs', 'package.json', 'requirements.txt', 'Dockerfile')):
                        path = os.path.join(root, file)
                        file_list.append(path)
                        
                        # 读取关键文件内容 (前50行)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read(2000)
                                file_contents += f"\n--- File: {file} ---\n{content}\n"
                        except Exception as e:
                            print(f"Error reading {file}: {e}")

        if not file_list:
            print(f"[{self.name}] No relevant files found.")
            return {}

        # 2. 调用 LLM 分析
        user_prompt = Prompts.OPS_ANALYZE_TEMPLATE.format(
            file_list=file_list,
            file_contents=file_contents[:5000] # 截断以避免 Token 过长
        )
        
        response = self.llm.chat(Prompts.OPS_SYSTEM, user_prompt)
        
        # 清理 Markdown 标记
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        # 3. 解析结果
        try:
            env_data = json.loads(cleaned_response)
            print(f"[{self.name}] Environment identified: {env_data.get('language')} / {env_data.get('framework')}")
            return env_data
        except json.JSONDecodeError:
            print(f"[{self.name}] Failed to parse JSON response.")
            return {}
