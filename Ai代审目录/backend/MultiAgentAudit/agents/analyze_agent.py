
import os
import json
import logging
from agents.base_agent import BaseAgent
from core.prompts import Prompts

class AnalyzeAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnalyzeAgent")

    def run(self, target_dir, env_data):
        """
        根据环境信息，审计目标目录下的代码。
        """
        print(f"[{self.name}] Starting code audit...")
        
        results = {
            "vulnerabilities": []
        }

        # 支持的文件扩展名映射
        extension_map = {
            ".py": "python",
            ".php": "php",
            ".java": "java",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
            ".rb": "ruby",
            ".rs": "rust",
            ".cs": "csharp"
        }
        
        # 处理单文件
        if os.path.isfile(target_dir):
            ext = os.path.splitext(target_dir)[1].lower()
            if ext in extension_map:
                language = extension_map[ext]
                self._audit_file(target_dir, language, results)
        else:
            # 处理目录
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extension_map:
                        path = os.path.join(root, file)
                        language = extension_map[ext]
                        self._audit_file(path, language, results)

        return results

    def _audit_file(self, file_path, language, results):
        print(f"[{self.name}] Auditing file: {os.path.basename(file_path)}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            user_prompt = Prompts.ANALYZE_TASK_TEMPLATE.format(
                language=language,
                file_path=file_path,
                code_content=content
            )
            
            response = self.llm.chat(Prompts.ANALYZE_SYSTEM, user_prompt)
            logging.info(f"Raw LLM response for {os.path.basename(file_path)}: {response}")
            
            # 清理 Markdown 标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            data = json.loads(cleaned_response)
            if data.get("vulnerabilities"):
                for vuln in data["vulnerabilities"]:
                    vuln["file"] = file_path # 添加文件路径信息
                    results["vulnerabilities"].append(vuln)
                    print(f"  [!] Found {vuln['type']} in {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Error auditing {file_path}: {e}")
