from BaseAgent import Agent
import uuid
import os
import json
import re

class AnalyzeAgent(Agent):
    def __init__(self, llm_client=None, max_vuln_count=5):
        super().__init__("AnalyzeCommonAgent", 
                         "This is a versatile code analysis assistant capable of performing vulnerability discovery and code analysis tasks, with support for multiple programming languages.",
                         llm_client)
        self.max_vuln_count = max_vuln_count
        self.gen_report = False
        self.report_queue = []
        self.found_vulns = []
        self.tech_stack = {}
        
        # Register tools
        self.register_tool("ListSourceCodeTreeTool")
        self.register_tool("ReadFileTool")
        self.register_tool("IssueVulnTool")
        self.register_tool("IdentifyTechStackTool")
        self.register_tool("StaticAnalysisTool")
        
        self.set_id(f"{self.name}-{uuid.uuid4()}")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "IdentifyTechStackTool",
                    "description": "Analyze project files to identify the technology stack (language, framework, version).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "The root directory to analyze."}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "StaticAnalysisTool",
                    "description": "Run basic static analysis (SAST) using regex patterns to find vulnerability candidates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "language": {"type": "string", "description": "The programming language (php, python, java, javascript)."},
                            "dir_path": {"type": "string", "description": "The directory to scan."}
                        },
                        "required": ["language", "dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ListSourceCodeTreeTool",
                    "description": "List all files in the project directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "The directory path to list. Use '.' for root."}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ReadFileTool",
                    "description": "Read the ENTIRE content of a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "The path to the file to read."}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "IssueVulnTool",
                    "description": "Report a discovered vulnerability in structured JSON format.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "Vulnerability type (e.g., SQL Injection, XSS, RCE)."},
                            "file_path": {"type": "string", "description": "Relative path to the file."},
                            "line_number": {"type": "integer", "description": "Line number where the vulnerability occurs."},
                            "severity": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"], "description": "Severity level."},
                            "description": {"type": "string", "description": "Detailed description of the vulnerability."}
                        },
                        "required": ["type", "file_path", "line_number", "severity", "description"]
                    }
                }
            }
        ]

    def identify_tech_stack(self, dir_path, root_path):
        target = root_path if dir_path == "." else os.path.join(root_path, dir_path)
        stack = {"language": "Unknown", "framework": "None", "version": "Unknown"}
        
        if not os.path.exists(target):
            return json.dumps(stack)

        # Check for key files
        files = os.listdir(target)
        
        # PHP
        if 'composer.json' in files or any(f.endswith('.php') for f in files):
            stack['language'] = "PHP"
            if 'composer.json' in files:
                try:
                    with open(os.path.join(target, 'composer.json'), 'r') as f:
                        data = json.load(f)
                        require = data.get('require', {})
                        if 'laravel/framework' in require:
                            stack['framework'] = "Laravel"
                            stack['version'] = require['laravel/framework']
                        elif 'symfony/symfony' in require:
                            stack['framework'] = "Symfony"
                            stack['version'] = require['symfony/symfony']
                except:
                    pass
        
        # Python
        elif 'requirements.txt' in files or 'setup.py' in files or any(f.endswith('.py') for f in files):
            stack['language'] = "Python"
            if 'django' in open(os.path.join(target, 'requirements.txt')).read().lower() if 'requirements.txt' in files else False:
                stack['framework'] = "Django"
            elif 'flask' in open(os.path.join(target, 'requirements.txt')).read().lower() if 'requirements.txt' in files else False:
                stack['framework'] = "Flask"

        # Java
        elif 'pom.xml' in files or any(f.endswith('.java') for f in files):
            stack['language'] = "Java"
            if 'pom.xml' in files:
                try:
                    content = open(os.path.join(target, 'pom.xml')).read()
                    if 'spring-boot' in content:
                        stack['framework'] = "Spring Boot"
                except:
                    pass

        # JavaScript/Node
        elif 'package.json' in files or any(f.endswith(('.js', '.ts', '.vue')) for f in files):
            stack['language'] = "JavaScript"
            if 'package.json' in files:
                try:
                    with open(os.path.join(target, 'package.json'), 'r') as f:
                        data = json.load(f)
                        deps = data.get('dependencies', {})
                        if 'vue' in deps:
                            stack['framework'] = "Vue"
                        elif 'react' in deps:
                            stack['framework'] = "React"
                        elif 'express' in deps:
                            stack['framework'] = "Express"
                except:
                    pass

        self.tech_stack = stack
        return json.dumps(stack)

    def static_analysis(self, language, dir_path, root_path):
        target = root_path if dir_path == "." else os.path.join(root_path, dir_path)
        findings = []
        
        # Enhanced patterns to find interesting files
        patterns = {
            "php": {
                "SQL Logic": r'(select|insert|update|delete|union|from|where)\s+',
                "Database Ops": r'(mysql_query|mysqli_query|pdo->query|pdo->prepare|db->query)',
                "User Input": r'\$_(POST|GET|REQUEST|COOKIE|SERVER)',
                "Command Exec": r'(system|exec|passthru|shell_exec|popen|proc_open|pcntl_exec)\s*\(',
                "Code Exec": r'(eval|assert|create_function)\s*\(',
                "Redirect": r'header\s*\(\s*["\']Location:',
                "File Ops": r'(file_get_contents|fopen|readfile|include|require)\s*\('
            },
            "python": {
                "SQL Logic": r'(execute|cursor|select|insert|update|delete)\s*\(',
                "Command Exec": r'os\.system|subprocess\.|popen',
                "Code Exec": r'eval\(|exec\(|yaml\.load|pickle\.load',
                "Web Framework": r'(django|flask|fastapi|bottle)'
            },
            "java": {
                "SQL Logic": r'executeQuery|executeUpdate|createNativeQuery',
                "Command Exec": r'Runtime\.getRuntime|ProcessBuilder',
                "Deserialization": r'readObject|ObjectInputStream'
            },
            "javascript": {
                "DOM XSS": r'(innerHTML|outerHTML|document\.write|v-html|dangerouslySetInnerHTML)',
                "Code Exec": r'(eval|setTimeout|setInterval|Function)\s*\(',
                "Command Exec": r'(child_process|exec|spawn)',
                "Sensitive Info": r'(token|password|secret|key)',
                "Hardcoded Config": r'(http://|https://)(localhost|127\.0\.0\.1)',
                "Missing CSRF": r'axios\.(post|put|delete|patch)'
            }
        }
        
        # Map JS variants
        if language.lower() in ['js', 'node', 'vue', 'typescript', 'javascript']:
            language = 'javascript'
        
        lang_patterns = patterns.get(language.lower(), {})
        if not lang_patterns:
            return "No static analysis patterns for this language."

        for root, dirs, files in os.walk(target):
            # Ignore common noise directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '.idea', '.vscode', 'dist', 'build', 'vendor']]
            
            for file in files:
                if not file.lower().endswith(tuple(['.php', '.py', '.java', '.js', '.ts', '.vue', '.sql'])):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        file_issues = []
                        # Check for presence of patterns in the whole file
                        for desc, pattern in lang_patterns.items():
                            if re.search(pattern, content, re.IGNORECASE):
                                file_issues.append(desc)
                        
                        if file_issues:
                            rel_path = os.path.relpath(file_path, root_path)
                            findings.append(f"File: {rel_path} | Potential Issues: {', '.join(file_issues)}")
                except Exception as e:
                    pass
        
        if not findings:
            return "No obvious hotspots found by static analysis. Please manually explore entry points."
        return "Static Analysis Findings (Candidates for Deep Analysis):\n" + "\n".join(findings)

    def list_source_code_tree(self, dir_path, root_path):
        if dir_path is None:
            dir_path = "."
        target = root_path if dir_path == "." else os.path.join(root_path, dir_path)
        if not os.path.exists(target):
            return f"Error: Path {target} does not exist."
        
        file_list = []
        for root, dirs, files in os.walk(target):
            # Ignore common noise directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '.idea', '.vscode', 'dist', 'build', 'vendor']]
            
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), root_path)
                file_list.append(rel_path)
            if len(file_list) > 100:
                file_list.append("... (too many files)")
                break
        return "\n".join(file_list)

    def read_file(self, file_path, root_path):
        if not file_path:
            return "Error: file_path argument is required."
        
        # Try direct path
        target = os.path.join(root_path, file_path)
        
        # If not found, try to strip first directory component (e.g. afy/login.php -> login.php)
        if not os.path.exists(target):
            parts = file_path.split(os.sep)
            if len(parts) > 1:
                 alt_target = os.path.join(root_path, parts[-1])
                 if os.path.exists(alt_target):
                     target = alt_target
            elif '/' in file_path: # Handle forward slashes on Windows if needed
                 parts = file_path.split('/')
                 if len(parts) > 1:
                     alt_target = os.path.join(root_path, parts[-1])
                     if os.path.exists(alt_target):
                         target = alt_target

        if not os.path.exists(target):
            return f"Error: File {target} does not exist. Available files in root: {os.listdir(root_path)}"
        
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Add line numbers
                lines = content.splitlines()
                numbered_content = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
                return numbered_content
        except Exception as e:
            return f"Error reading file: {e}"

    def log(self, message):
        print(f"[{self.name}] {message}", flush=True)

    def run(self, context):
        target_path = context.get("target_path", ".")
        self.log(f"Starting analysis task on {target_path}...")
        
        system_prompt = f"""You are an expert Vulnerability Analyst. 
Your job is to find and validate vulnerability candidates by reading code thoroughly.
The target code is located at: {target_path}

You have access to tools to list files, read file content, identify tech stack, and run static analysis.

CRITICAL VULNERABILITY CHECKS:
1. **SQL Injection**: Look for SQL queries constructed using string concatenation with user input (e.g., `$_POST`, `$_GET`). Check files that handle login or data retrieval.
2. **Execution After Redirect (EAR)**: Look for `header("Location: ...")` calls that are NOT followed immediately by `exit()` or `die()`. This allows code execution to continue.
   - If you see `header(...)` but no `exit/die` in the subsequent lines (even after `?>` closing tag if code ends there, check if sensitive HTML follows), it is a vulnerability.
3. **Auth Bypass**: Check if sensitive files properly verify session/login status at the very top.
4. **Information Leakage**: Check for exposed `.sql` files or backup files that might contain credentials.

WORKFLOW:
1. **Identify Tech Stack**: Call `IdentifyTechStackTool` first.
2. **Static Analysis**: Call `StaticAnalysisTool` to find potential hotspots.
3. **Deep Analysis**: Iterate through the findings from Static Analysis.
   - Use `ReadFileTool` to read the ENTIRE file content.
   - **SKIP** minified files (`.min.js`, `.min.css`), images, fonts, and library files (e.g., `jquery`).
   - Do NOT assume code is safe based on the first few lines.
   - If you see `//注入点` (Injection Point) or similar comments, FIND where those variables are used.
4. **Trace Data Flow**: Trace user input to SQL queries or sensitive functions.
5. **Report IMMEDIATELY**: When you confirm a vulnerability, call `IssueVulnTool`.
   - **CRITICAL**: You MUST use the **tool call** mechanism.
   - **DO NOT** write the JSON text in your response.
   - **DO NOT** just say "I found a vulnerability".
   - Invoke the function `IssueVulnTool(type=..., file_path=..., line_number=..., severity=..., description=...)`.
6. Be exhaustive. Do not stop at the first finding.

If you are done, say "Analysis complete".
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Start the analysis. Identify the tech stack first."}
        ]
        
        max_turns = 10
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
            
            # Handle API error response format if any
            if 'error' in response:
                 self.log(f"LLM API Error: {response['error']}")
                 break

            choice = response['choices'][0]
            message = choice['message']
            content = message.get('content')
            tool_calls = message.get('tool_calls')
            
            # Append assistant message (must be dict)
            messages.append(message)
            
            if content:
                self.log(f"LLM: {content}")
                
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    try:
                        arguments = json.loads(tool_call['function']['arguments'])
                        # Handle double-encoded JSON if applicable
                        if isinstance(arguments, str):
                             try:
                                 parsed = json.loads(arguments)
                                 if isinstance(parsed, dict):
                                     arguments = parsed
                             except json.JSONDecodeError:
                                 pass
                    except json.JSONDecodeError:
                        self.log(f"Error decoding arguments for {function_name}: {tool_call['function']['arguments']}")
                        # Attempt to fix common JSON errors (e.g. unescaped backslashes in Windows paths)
                        raw_args = tool_call['function']['arguments']
                        try:
                            # If it looks like a file path with single backslashes, try to escape them
                            if ':\\' in raw_args and '\\\\' not in raw_args:
                                fixed_args = raw_args.replace('\\', '\\\\')
                                arguments = json.loads(fixed_args)
                            else:
                                arguments = {}
                        except:
                            arguments = {}
                        
                    if not isinstance(arguments, dict):
                         self.log(f"Error: arguments is not a dict: {type(arguments)}")
                         arguments = {}

                    call_id = tool_call['id']
                    
                    self.log(f"Tool Call: {function_name}({arguments})")
                    
                    result = ""
                    if function_name == "ListSourceCodeTreeTool":
                        result = self.list_source_code_tree(arguments.get('dir_path', '.'), target_path)
                    elif function_name == "ReadFileTool":
                        result = self.read_file(
                            arguments.get('file_path'), 
                            target_path
                        )
                    elif function_name == "IdentifyTechStackTool":
                        result = self.identify_tech_stack(arguments.get('dir_path', '.'), target_path)
                    elif function_name == "StaticAnalysisTool":
                        result = self.static_analysis(
                            arguments.get('language', 'php'),
                            arguments.get('dir_path', '.'),
                            target_path
                        )
                    elif function_name == "IssueVulnTool":
                        self.found_vulns.append(arguments)
                        result = "Vulnerability recorded."
                        self.log(f"*** VULNERABILITY REPORTED: {arguments.get('type', 'Unknown')} in {arguments.get('file_path', 'Unknown')} ***")
                    else:
                        result = f"Error: Unknown tool {function_name}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result
                    })
            else:
                if content and "analysis complete" in content.lower():
                    break
        
        return {"status": "completed", "vulns": self.found_vulns, "tech_stack": self.tech_stack}
