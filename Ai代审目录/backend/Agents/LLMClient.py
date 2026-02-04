import os
import requests
import json
import time

class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    def chat(self, messages, tools=None, temperature=0.7):
        """
        Send a chat completion request.
        :param messages: List of message dicts (role, content)
        :param tools: List of tool definitions (optional)
        :param temperature: Sampling temperature
        :return: The response content or tool calls
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        max_retries = 10
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # For demonstration purposes, if we are using a mock key and standard URL, 
                # we might not want to actually hit OpenAI and fail.
                if self.api_key == "sk-mock-key":
                    return self._mock_response(messages)

                self._log_monitor("REQUEST", {"url": url, "model": self.model, "messages": messages, "tools": tools})
                # print(f"DEBUG: Sending request to {url} model={self.model}")
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                # print(f"DEBUG: Response status: {response.status_code}")
                
                if response.status_code == 429:
                    self._log_monitor("WARNING", "Rate limited. Retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                
                if response.status_code != 200:
                    self._log_monitor("ERROR", f"Response status: {response.status_code}, content: {response.text}")
                    
                response.raise_for_status()
                resp_json = response.json()
                self._log_monitor("RESPONSE", resp_json)
                return resp_json
            except Exception as e:
                self._log_monitor("EXCEPTION", str(e))
                print(f"[LLMClient] Error: {e}")
                if attempt < max_retries - 1:
                     time.sleep(retry_delay)
                     retry_delay *= 2
                else:
                     return None

    def _log_monitor(self, type, data):
        with open("llm_monitor.log", "a", encoding="utf-8") as f:
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": type,
                "data": data
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _mock_response(self, messages):
        """Generate a mock response for testing without a real API key."""
        last_msg = messages[-1]['content']
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"[MOCK LLM RESPONSE] I received your message: '{last_msg[:50]}...'. I am ready to help with vulnerability analysis."
                    }
                }
            ]
        }
