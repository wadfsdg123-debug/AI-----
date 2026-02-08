"""
LLM 审计引擎
调用 OpenAI API 进行代码安全分析
"""

import os
import json
import logging
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMAuditEngine:
    """LLM 代码审计引擎"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
    def analyze_code(self, code: str, language: str, static_results: dict = None) -> Dict:
        """
        使用 LLM 分析代码安全问题
        """
        if not self.client:
            logger.error("OpenAI API Key 未配置")
            return {
                "error": "API Key 未配置",
                "issues": [],
                "summary": "请在 .env 文件中配置 OPENAI_API_KEY"
            }
        
        prompt = self._build_prompt(code, language, static_results)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的代码安全审计专家。请分析代码中的安全漏洞，并以 JSON 格式返回结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"LLM 分析完成，发现 {len(result.get('issues', []))} 个问题")
            return
"""
if static_results:
prompt += f"""
静态分析工具发现的问题：
{json.dumps(static_results, indent=2, ensure_ascii=False)}
请结合以上结果，进行深度分析。
"""
    prompt += """
请以 JSON 格式返回结果，格式如下：
{
"issues": [
{
"severity": "high/medium/low",
"category": "漏洞类型（如：SQL注入、XSS、命令注入等）",
"line": 行号,
"description": "问题描述",
"suggestion": "修复建议"
}
],
"summary": "整体安全评估摘要"
}
"""
return prompt
测试代码
if name == "main":
test_code = """
import os
user_input = input("Enter command: ")
os.system(user_input)
"""
engine = LLMAuditEngine()
result = engine.analyze_code(test_code, "python")
print(json.dumps(result, indent=2, ensure_ascii=False))