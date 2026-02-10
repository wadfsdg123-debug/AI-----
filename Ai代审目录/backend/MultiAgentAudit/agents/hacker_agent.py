
import json
import os
import logging
from agents.base_agent import BaseAgent
from core.prompts import Prompts

class HackerAgent(BaseAgent):
    def __init__(self):
        super().__init__("HackerAgent")

    def run(self, analyze_results, env_data):
        """
        基于审计结果生成 Payload 并（模拟）验证。
        """
        print(f"[{self.name}] Generating payloads for identified vulnerabilities...")
        
        verification_results = {
            "verified_vulnerabilities": []
        }
        
        # 扩展名映射，用于自动判断语言
        extension_map = {
            ".py": "python",
            ".php": "php",
            ".java": "java",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp"
        }
        
        for vuln in analyze_results.get("vulnerabilities", []):
            print(f"[{self.name}] Processing {vuln['type']} in {vuln.get('file')}...")
            
            # 根据文件后缀推断语言，如果无法推断则使用环境默认语言
            file_path = vuln.get('file', '')
            ext = os.path.splitext(file_path)[1].lower() if file_path else ""
            language = extension_map.get(ext, env_data.get("language", "unknown"))

            user_prompt = Prompts.HACKER_GEN_PAYLOAD_TEMPLATE.format(
                vuln_type=vuln['type'],
                code_snippet=vuln['code_snippet'],
                language=language
            )
            
            response = self.llm.chat(Prompts.HACKER_SYSTEM, user_prompt)
            
            try:
                # 清理 Markdown 标记
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]

                payload_data = json.loads(cleaned_response)
                
                # 记录验证结果
                verified_vuln = vuln.copy()
                verified_vuln["payloads"] = payload_data.get("payloads", [])
                
                # 这里可以添加实际的 HTTP 请求验证逻辑
                # if self._verify(vuln, payload_data): ...
                
                verification_results["verified_vulnerabilities"].append(verified_vuln)
                print(f"  [+] Generated {len(payload_data.get('payloads', []))} payloads.")
                
            except json.JSONDecodeError:
                print(f"[{self.name}] Failed to parse payload data.")

        return verification_results
