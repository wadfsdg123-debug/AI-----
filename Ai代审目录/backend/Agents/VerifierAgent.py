
from BaseAgent import Agent
import uuid
import json
import subprocess
import sys
import os
import ast
import shutil
import re

class VerifierAgent(Agent):
    def __init__(self, llm_client=None):
        super().__init__("VerifierCommonAgent", 
                         "This is a versatile vulnerability verification assistant capable of performing vulnerability verification tasks.",
                         llm_client)
        self.verified_vulns = []
        
        # Register tools
        self.register_tool("RunPythonCodeTool")
        self.register_tool("SubmitVulnTool")
        self.register_tool("RunCommandTool")
        self.register_tool("ReadLinesFromFileTool")
        self.register_tool("ListFilesTool")
        self.register_tool("VerifyPHPSQLInjectionTool")
        self.target_path = None
        
        self.set_id(f"{self.name}-{uuid.uuid4()}")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "VerifyPHPSQLInjectionTool",
                    "description": "Verify SQL injection in PHP files by mocking the database connection. NOTE: If the target has input length restrictions (e.g. strlen < 6), use very compact payloads like \"'||1#\" or \"'or 1#\".",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_file": {"type": "string", "description": "The PHP file to verify (relative path, e.g. 'checklogin.php')."},
                            "input_params": {"type": "object", "description": "Dictionary of GET/POST parameters to set. E.g. {'userid': 'test', 'userpwd': '123'}"},
                            "injection_param": {"type": "string", "description": "The specific parameter name to inject the payload into (e.g. 'userid')."},
                            "payload": {"type": "string", "description": "The injection payload (e.g. \"' OR 1#\")."},
                            "method": {"type": "string", "enum": ["POST", "GET"], "description": "HTTP method to simulate."}
                        },
                        "required": ["target_file", "input_params", "injection_param", "payload"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ReadLinesFromFileTool",
                    "description": "Read specific lines from a file to understand the code logic.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "The path to the file to read."},
                            "line_start": {"type": "integer", "description": "Start line number (1-based)."},
                            "line_end": {"type": "integer", "description": "End line number (1-based)."}
                        },
                        "required": ["file_path", "line_start", "line_end"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ListFilesTool",
                    "description": "List files in the directory to find configuration or database files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "The directory to list."}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RunPythonCodeTool",
                    "description": "Run Python code to verify a vulnerability. The code should print 'VULNERABILITY_CONFIRMED' if successful.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "The Python code to run."}
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "SubmitVulnTool",
                    "description": "Submit a verified vulnerability.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["success", "failed"]},
                            "proof": {"type": "string", "description": "Proof of the vulnerability (logs, output)."},
                            "poc": {"type": "string", "description": "The final working PoC script."}
                        },
                        "required": ["status", "proof"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RunCommandTool",
                    "description": "Run a shell command.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    def verify_php_sqli(self, target_file, input_params, injection_param, payload, method="POST"):
        self.log(f"Verifying SQLi in {target_file} with payload: {payload}")
        
        root_path = self.target_path if self.target_path else "."
        # Determine paths
        target_path = os.path.join(root_path, target_file)
        
        if not os.path.exists(target_path):
             # Try simple filename match if relative path fails
             filename = os.path.basename(target_file)
             for root, dirs, files in os.walk(root_path):
                 if filename in files:
                     target_path = os.path.join(root, filename)
                     break
        
        if not os.path.exists(target_path):
            return f"Error: Target file {target_file} not found."

        work_dir = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        
        conn_php = os.path.join(work_dir, "conn.php")
        conn_bak = os.path.join(work_dir, "conn.php.bak")
        sql_log = os.path.join(work_dir, "sql_log.txt")
        wrapper_path = os.path.join(work_dir, f"wrapper_{uuid.uuid4().hex[:8]}.php")
        
        # Prepare Mock conn.php
        # Use forward slashes for PHP compatibility
        sql_log_php = sql_log.replace("\\", "/")
        
        mock_conn_content = f"""<?php
class MockResult {{
    public $num_rows = 1; 
    public function fetch_array($mode) {{ return null; }}
    public function free() {{}}
}}
class MockMysqli {{
    public function __construct() {{}}
    public function query($sql) {{
        file_put_contents("{sql_log_php}", $sql . "\\n", FILE_APPEND);
        return new MockResult();
    }}
    public function close() {{}}
}}
$mysqli = new MockMysqli();
?>"""

        try:
            # 1. Backup conn.php
            if os.path.exists(conn_php):
                if not os.path.exists(conn_bak):
                    shutil.copy(conn_php, conn_bak)
            
            # 2. Write Mock conn.php
            with open(conn_php, "w", encoding='utf-8') as f:
                f.write(mock_conn_content)
                
            # 3. Clean log
            if os.path.exists(sql_log):
                os.remove(sql_log)
                
            # 4. Create Wrapper
            # Inject payload into params
            if injection_param in input_params:
                input_params[injection_param] = payload
            
            php_setup = "error_reporting(E_ERROR | E_PARSE);\n"
            php_setup += "session_start();\n"
            
            for k, v in input_params.items():
                # Escape quotes in value for PHP string
                val = str(v).replace('"', '\\"')
                if method == "POST":
                    php_setup += f"$_POST['{k}'] = \"{val}\";\n"
                else:
                    php_setup += f"$_GET['{k}'] = \"{val}\";\n"
            
            php_setup += f"require '{filename}';\n"
            
            with open(wrapper_path, "w", encoding='utf-8') as f:
                f.write(f"<?php\n{php_setup}\n?>")
                
            # 5. Run Wrapper
            cmd = ["php", wrapper_path]
            try:
                run_result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
            except Exception as e:
                self.log(f"PHP execution error: {e}")
                return f"Error executing PHP: {e}"

            # 6. Check Log
            if os.path.exists(sql_log):
                with open(sql_log, "r", encoding='utf-8') as f:
                    logs = f.read()
                
                # Simple verification: check if payload exists in the log
                # For more complex verification, we might check syntax, but existence is a strong signal here
                if payload in logs:
                    return f"VULNERABILITY_CONFIRMED: Payload found in generated SQL. Captured SQL:\n{logs}"
                else:
                    return f"Failure: Payload NOT found in generated SQL. Captured SQL:\n{logs}\nPHP Output:\n{run_result.stdout}\n{run_result.stderr}"
            else:
                return f"Failure: No SQL generated (conn.php might not be included or reached). PHP Output:\n{run_result.stdout}\n{run_result.stderr}"

        except Exception as e:
            return f"Error during verification: {e}"
        finally:
            # Restore
            if os.path.exists(conn_bak):
                shutil.copy(conn_bak, conn_php)
                os.remove(conn_bak)
            
            if os.path.exists(wrapper_path):
                os.remove(wrapper_path)
            
            if os.path.exists(sql_log):
                os.remove(sql_log)

    def read_lines_from_file(self, file_path, line_start, line_end):
        # Use target_path if available
        root_path = self.target_path if self.target_path else "."
        
        # Try direct path
        target = os.path.join(root_path, file_path)
        
        # If not found, try to strip first directory component or join with target_path
        if not os.path.exists(target):
             # Try assuming file_path is relative to root_path but might have leading slash or different separator
             # Or maybe file_path is just filename
             parts = file_path.split(os.sep)
             if len(parts) > 1:
                 alt_target = os.path.join(root_path, parts[-1])
                 if os.path.exists(alt_target):
                     target = alt_target
             elif '/' in file_path:
                 parts = file_path.split('/')
                 if len(parts) > 1:
                     alt_target = os.path.join(root_path, parts[-1])
                     if os.path.exists(alt_target):
                         target = alt_target

        if not os.path.exists(target):
            return f"Error: File {target} does not exist. Please check the file path."

        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                total_lines = len(lines)
                start = max(0, line_start - 1)
                end = min(total_lines, line_end)
                
                content = "".join([f"{i+1}: {line}" for i, line in enumerate(lines[start:end], start=start)])
                return content
        except Exception as e:
            return f"Error reading file: {e}"

    def run_python_code(self, code):
        self.log(f"Executing Python Code with {sys.executable}...")
        try:
            # Write code to a temporary file
            with open("temp_poc.py", "w", encoding='utf-8') as f:
                f.write(code)
            
            # Execute
            result = subprocess.run([sys.executable, "temp_poc.py"], capture_output=True, text=True, timeout=30)
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            self.log(f"Execution Result: {output[:200]}...")
            
            # Cleanup
            if os.path.exists("temp_poc.py"):
                os.remove("temp_poc.py")
                
            return output
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out."
        except Exception as e:
            return f"Error executing code: {e}"

    def run_command(self, command):
        self.log(f"Executing Command: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Error executing command: {e}"

    def log(self, message):
        print(f"[{self.name}] {message}", flush=True)

    def run(self, context):
        vuln_info = context.get("vuln", {})
        target_url = context.get("target_url", "http://127.0.0.1:8000")
        self.target_path = context.get("target_path")
        
        # Support both new 'type' and old 'title'
        vuln_title = vuln_info.get('type') or vuln_info.get('title') or 'Unknown'
        
        self.log(f"Starting verification for: {vuln_title}")
        self.log(f"Target URL: {target_url}")
        
        system_prompt = f"""You are a Vulnerability Verifier.
Your task is to verify the following vulnerability:
Type/Title: {vuln_title}
Description: {vuln_info.get('description')}
File: {vuln_info.get('file_path')}
Line: {vuln_info.get('line_number')}
Severity: {vuln_info.get('severity', 'Unknown')}

The target application is running at: {target_url}
NOTE: You are running in a Windows environment. The source code is available locally.
Use ListFilesTool with relative paths (e.g., "." or "admin") to explore the codebase.
DO NOT use absolute paths like "/var/www/html".
DO NOT assume standard Linux paths.

STRICT TOOL USAGE RULES:
1. VerifyPHPSQLInjectionTool:
   - USE ONLY for "SQL Injection" vulnerabilities in PHP files.
   - DO NOT use this for File Inclusion, XSS, RCE, or any other type.
   - It mocks database connections; it cannot verify file system operations.

2. RunPythonCodeTool:
   - USE THIS for all other vulnerability types (File Inclusion, RCE, XSS, etc.).
   - Write a Python script using 'requests' to exploit the vulnerability against {target_url}.
   - For File Inclusion: Try to include a known file (e.g., ../index.php or config.php) and check the response content.
   - For RCE: Try to execute a simple command (e.g., echo "test") and check the output.

You have access to:
1. VerifyPHPSQLInjectionTool: (See Strict Rules above)
2. RunPythonCodeTool: (See Strict Rules above)
3. ListFilesTool: Check for files.
4. ReadLinesFromFileTool: Read content of files.
5. SubmitVulnTool: Report the result.

Verification Steps:
1. Analyze the vulnerability description and file path.
2. Read the target file code using ReadLinesFromFileTool to understand the logic. START FROM LINE 1 to catch validation checks!
3. DECIDE VALIDATION STRATEGY BASED ON VULNERABILITY TYPE:
   - IF SQL Injection: Use VerifyPHPSQLInjectionTool immediately.
   - IF File Inclusion / RCE / Other: Use RunPythonCodeTool to write a PoC script.
4. Execute the chosen tool.
5. If the tool confirms the vulnerability (returns CONFIRMED or successful output), call SubmitVulnTool with status='success'.
6. If it fails, analyze why (read more code) and try a different payload/method.
7. If all attempts fail, call SubmitVulnTool with status='failed'.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Start verification."}
        ]
        
        max_turns = 15
        tools = self.get_tool_definitions()
        
        for i in range(max_turns):
            self.log(f"Turn {i+1}/{max_turns}")
            
            if self.llm:
                response = self.llm.chat(messages, tools=tools)
            else:
                self.log("No LLM Client provided.")
                return {"status": "skipped"}
            
            if not response:
                self.log("LLM request failed.")
                break
                
            choice = response['choices'][0]
            message = choice['message']
            content = message.get('content')
            tool_calls = message.get('tool_calls')
            
            messages.append(message)
            
            if content:
                self.log(f"LLM: {content}")
                
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    # Parse arguments (handle double/triple encoding)
                    try:
                        arguments = json.loads(tool_call['function']['arguments'])
                    except json.JSONDecodeError:
                        # Sometimes arguments is just a python dict string
                        try:
                            arguments = ast.literal_eval(tool_call['function']['arguments'])
                        except:
                            arguments = tool_call['function']['arguments']
                    
                    if isinstance(arguments, str):
                        for _ in range(3):
                            try:
                                parsed = json.loads(arguments)
                                arguments = parsed
                                if not isinstance(arguments, str):
                                    break
                            except json.JSONDecodeError:
                                try:
                                    parsed = ast.literal_eval(arguments)
                                    arguments = parsed
                                    if not isinstance(arguments, str):
                                        break
                                except:
                                    break
                    
                    # Generic fallback: try to find JSON-like structure
                    if isinstance(arguments, str) and not isinstance(arguments, dict):
                        import re
                        # Look for { ... } that might be valid JSON
                        match = re.search(r'(\{.*\})', arguments, re.DOTALL)
                        if match:
                            try:
                                arguments = json.loads(match.group(1))
                            except:
                                pass

                    # Fallback for RunPythonCodeTool with newlines in string (regex extraction)
                    if isinstance(arguments, str) and function_name == 'RunPythonCodeTool':
                         import re
                         match = re.search(r'"code":\s*"(.*)"\s*}', arguments, re.DOTALL)
                         if match:
                             code_content = match.group(1)
                             code_content = code_content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                             arguments = {"code": code_content}

                    if not isinstance(arguments, dict):
                         # Fallback for RunPythonCodeTool if arguments is a string
                         if function_name == 'RunPythonCodeTool' and isinstance(arguments, str):
                              import re
                              match = re.search(r'"code":\s*"(.*)"\s*}', arguments, re.DOTALL)
                              if match:
                                  code_content = match.group(1)
                                  # Unescape common JSON escapes from the raw regex match
                                  code_content = code_content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                  arguments = {"code": code_content}
                              else:
                                  self.log("Error: Regex failed to extract code from arguments")
                                  arguments = {}
                         elif function_name == 'SubmitVulnTool' and isinstance(arguments, str):
                              import re
                              # Try to extract status manually
                              status_match = re.search(r'"status":\s*"(.*?)"', arguments)
                              status = status_match.group(1) if status_match else "completed"
                              # Use the whole string as proof if parsing failed
                              arguments = {"status": status, "proof": arguments}
                         else:
                              self.log(f"Error: arguments for {function_name} is not a dictionary: {arguments}")
                              # Ensure arguments is preserved as string so we can debug or try other parsing if needed
                              # But for now, empty dict is safer to avoid loops
                              arguments = {}

                    self.log(f"Tool Call: {function_name}")
                    
                    result = ""
                    if function_name == "RunPythonCodeTool":
                        code = arguments.get('code', '')
                        # Fix double-escaped newlines if the code is a single line
                        if '\n' not in code and '\\n' in code:
                            code = code.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"')
                        result = self.run_python_code(code)
                    elif function_name == "RunCommandTool":
                        result = self.run_command(arguments.get('command', ''))
                    elif function_name == "ReadLinesFromFileTool":
                        result = self.read_lines_from_file(
                            arguments.get('file_path', ''), 
                            arguments.get('line_start', 1), 
                            arguments.get('line_end', 100)
                        )
                    elif function_name == "ListFilesTool":
                        dir_path = arguments.get('dir_path', '.')
                        # Clean up path to avoid absolute path issues on Windows
                        if dir_path.startswith('/') or dir_path.startswith('\\'):
                            dir_path = dir_path.lstrip('/\\')
                        
                        target = os.path.join(self.target_path if self.target_path else ".", dir_path)
                        
                        if os.path.exists(target):
                            if os.path.isdir(target):
                                try:
                                    items = os.listdir(target)
                                    result = "\n".join(items) if items else "(empty directory)"
                                except Exception as e:
                                    result = f"Error listing directory: {e}"
                            else:
                                result = f"Error: {target} is not a directory."
                        else:
                            # Try searching for the directory if it's a relative path that might be nested
                            result = f"Error: Path {target} does not exist."
                    elif function_name == "VerifyPHPSQLInjectionTool":
                        result = self.verify_php_sqli(
                            arguments.get('target_file', ''),
                            arguments.get('input_params', {}),
                            arguments.get('injection_param', ''),
                            arguments.get('payload', ''),
                            arguments.get('method', 'POST')
                        )
                    elif function_name == "SubmitVulnTool":
                        self.verified_vulns.append(arguments)
                        result = "Submission received."
                        self.log(f"*** VERIFICATION RESULT: {arguments.get('status', 'unknown')} ***")
                        return {"status": "completed", "result": arguments}
                    else:
                        result = f"Error: Unknown tool {function_name}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": result
                    })
        
        return {"status": "completed", "result": self.verified_vulns}
