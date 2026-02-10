
import os
import json
import time

class LLMClient:
    def __init__(self, api_key=None, provider="openai", base_url=None, model=None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.provider = provider
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL")
        
        # 初始化客户端
        self.client = None
        if self.api_key:
            self._init_client()

    def _init_client(self):
        if self.provider == "openai" or self.provider == "deepseek":
            try:
                from openai import OpenAI
                # 如果是 DeepSeek，默认 Base URL 为 https://api.deepseek.com
                if self.provider == "deepseek" and not self.base_url:
                    self.base_url = "https://api.deepseek.com"
                
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                if not self.model:
                    self.model = "deepseek-chat" if self.provider == "deepseek" else "gpt-3.5-turbo"
                print(f"[LLM Info] Client initialized for {self.provider} (Base URL: {self.base_url})")
            except ImportError:
                print("Error: 'openai' package not installed. Run 'pip install openai'.")

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                if not self.model:
                    self.model = "gemini-1.5-flash"
            except ImportError:
                print("Error: 'google-generativeai' package not installed. Run 'pip install google-generativeai'.")

    def chat(self, system_prompt, user_prompt, temperature=0.7):
        """
        调用 LLM 进行对话。
        """
        if not self.api_key or not self.client:
            print(f"[LLM Warning] No API Key or Client initialized. Using Mock. (Key length: {len(self.api_key) if self.api_key else 0})")
            raise RuntimeError("LLM Client not initialized! Check API Key and dependencies.")
            # return self._mock_response(system_prompt, user_prompt)
        
        try:
            # print(f"[LLM Info] Calling {self.provider} model: {self.model}...")
            if self.provider == "openai" or self.provider == "deepseek":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"} if "JSON" in system_prompt else None
                )
                return response.choices[0].message.content

            elif self.provider == "gemini":
                # Gemini 没有直接的 System Prompt 参数 (在旧版)，但在 1.5 中支持 system_instruction
                model = self.client.GenerativeModel(
                    model_name=self.model,
                    system_instruction=system_prompt
                )
                # 强制 JSON 模式提示
                if "JSON" in user_prompt or "JSON" in system_prompt:
                    generation_config = {"response_mime_type": "application/json"}
                else:
                    generation_config = {}
                
                response = model.generate_content(
                    user_prompt,
                    generation_config=generation_config
                )
                return response.text

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[LLM Error] {e}")
            raise e # 强制抛出异常，不回退到 Mock
            # print("Falling back to Mock response...")
            # return self._mock_response(system_prompt, user_prompt)

    def _mock_response(self, system_prompt, user_prompt):
        """
        根据 prompt 内容返回模拟的 JSON 响应，用于演示系统流程。
        """
        # print(f"[LLM Mock] System: {system_prompt[:50]}...")
        # print(f"[LLM Mock] User: {user_prompt[:50]}...")
        time.sleep(0.5) # 模拟网络延迟

        # 1. OpsAgent Mock
        if "应用指纹识别" in system_prompt:
            return json.dumps({
                "language": "python",
                "framework": "flask",
                "version": "3.8",
                "dependencies": ["flask", "requests"],
                "docker_config": {
                    "image": "python:3.8-slim",
                    "ports": ["5000"],
                    "start_command": "python app.py"
                }
            })

        # 2. AnalyzeAgent Mock
        if "代码审计专家" in system_prompt:
            return json.dumps({
                "vulnerabilities": [
                    {
                        "type": "SQL Injection",
                        "severity": "High",
                        "location": "app.py:25",
                        "code_snippet": "cursor.execute('SELECT * FROM users WHERE username = ' + username)",
                        "reason": "直接拼接用户输入 username 到 SQL 查询字符串中，未经过滤或参数化查询。",
                        "confidence": "Certain"
                    }
                ]
            })

        # 3. HackerAgent Mock
        if "渗透测试专家" in system_prompt:
            return json.dumps({
                "payloads": [
                    {
                        "payload": "' OR '1'='1",
                        "description": "基础永真式绕过",
                        "expected_response": "返回所有用户数据或登录成功"
                    },
                    {
                        "payload": "' UNION SELECT 1, database(), 3 -- ",
                        "description": "联合查询注入获取数据库名",
                        "expected_response": "页面显示数据库名称"
                    }
                ]
            })

        # 4. ReporterAgent Mock
        if "安全报告撰写专家" in system_prompt:
            return """# 安全审计报告

## 1. 执行摘要
本报告对目标应用进行了全面的自动化安全审计。共发现 **1** 个高危漏洞。

## 2. 环境信息
- **语言**: Python 3.8
- **框架**: Flask
- **部署方式**: Docker (python:3.8-slim)

## 3. 漏洞详情

### [High] SQL Injection
- **位置**: app.py:25
- **描述**: 用户输入未经过滤直接拼接到 SQL 查询中。
- **危害**: 攻击者可获取数据库敏感信息或绕过认证。
- **修复建议**: 使用参数化查询 (Prepared Statements)。

## 4. 验证证据
已生成 Payload `' OR '1'='1` 可成功绕过验证。
"""

        return "Error: No mock response match found."
