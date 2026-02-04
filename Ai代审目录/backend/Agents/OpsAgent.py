from BaseAgent import Agent
import uuid

class OpsAgent(Agent):
    def __init__(self, llm_client=None):
        super().__init__("OpsCommonAgent", 
                         "This is a general-purpose ops intelligent agent capable of setting up environments and performing operational tasks in multiple languages.",
                         llm_client)
        
        # Register tools
        self.register_tool("RunCommandTool")
        self.register_tool("DetectLanguageTool")
        self.register_tool("DockerRunTool")
        self.register_tool("DockerLogsTool")
        self.register_tool("DockerRemoveTool")
        self.register_tool("DockerExecTool")
        self.register_tool("EnvSaveTool")
        self.register_tool("RunSQLTool")
        self.register_tool("JavaEnvTool")
        self.register_tool("PHPEnvTool")
        self.register_tool("NodeEnvTool")
        self.register_tool("PythonEnvTool")
        self.register_tool("GolangEnvTool")
        self.register_tool("MySQLEnvTool")
        self.register_tool("RedisEnvTool")
        self.register_tool("ListSourceCodeTreeTool")
        self.register_tool("SearchFileContentsByRegexTool")
        self.register_tool("ReadLinesFromFileTool")
        self.register_tool("TaskListTool")
        self.register_tool("IssueTool")
        
        self.set_id(f"{self.name}-{uuid.uuid4()}")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "DetectLanguageTool",
                    "description": "Detect the programming language of the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "The directory to analyze."}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RunCommandTool",
                    "description": "Run a shell command on the host.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command to run."}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "DockerRunTool",
                    "description": "Run a docker container.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image": {"type": "string", "description": "The docker image to run."},
                            "ports": {"type": "string", "description": "Port mapping (e.g. '80:80')."},
                            "volumes": {"type": "string", "description": "Volume mapping (e.g. '/host:/container')."},
                            "env": {"type": "string", "description": "Environment variables (e.g. 'KEY=VALUE')."}
                        },
                        "required": ["image"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "DockerExecTool",
                    "description": "Execute a command in a running container.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "container_id": {"type": "string", "description": "The container ID."},
                            "command": {"type": "string", "description": "The command to execute."}
                        },
                        "required": ["container_id", "command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "EnvSaveTool",
                    "description": "Save the environment information (URL, etc.) to the global context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The base URL of the deployed service."},
                            "container_id": {"type": "string", "description": "The container ID."}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ListSourceCodeTreeTool",
                    "description": "List files in directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "Directory path."}
                        },
                        "required": ["dir_path"]
                    }
                }
            }
        ]

    def detect_language(self, dir_path, root_path):
        import os, json
        target = root_path if dir_path == "." else os.path.join(root_path, dir_path)
        if not os.path.exists(target):
            return "Directory not found."
        
        files = os.listdir(target)
        lang = "Unknown"
        if any(f.endswith('.php') for f in files) or 'composer.json' in files:
            lang = "PHP"
        elif any(f.endswith('.py') for f in files) or 'requirements.txt' in files:
            lang = "Python"
        elif any(f.endswith('.java') for f in files) or 'pom.xml' in files:
            lang = "Java"
        elif any(f.endswith('.js') for f in files) or 'package.json' in files:
            lang = "NodeJS"
            
        return json.dumps({"language": lang, "files": files[:10]})

    def docker_run(self, image, ports, volumes, env, root_path):
        import subprocess
        import os
        cmd = ["docker", "run", "-d"]
        if ports:
            # Ensure proper port mapping format (Host:Container)
            # If LLM provides 80:8080 but container is 80, it might be wrong.
            # But we trust LLM for now.
            cmd.extend(["-p", ports])
        if volumes:
            # Handle Windows paths which contain ':'
            # Split only on the last colon
            parts = volumes.rsplit(':', 1)
            if len(parts) == 2:
                host_path, container_path = parts
                if not os.path.isabs(host_path):
                    host_path = os.path.join(root_path, host_path)
                cmd.extend(["-v", f"{host_path}:{container_path}"])
        if env:
            cmd.extend(["-e", env])
        cmd.append(image)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    def docker_exec(self, container_id, command):
        import subprocess
        cmd = ["docker", "exec", container_id, "sh", "-c", command]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    def list_source_code_tree(self, dir_path, root_path):
        import os
        if dir_path is None: dir_path = "."
        target = root_path if dir_path == "." else os.path.join(root_path, dir_path)
        if not os.path.exists(target): return "Path not found."
        files = []
        for f in os.listdir(target):
            files.append(f)
        return "\n".join(files)

    def run(self, context):
        import json
        import os
        target_path = context.get("target_path", ".")
        self.log(f"Starting ops task on {target_path}...")
        
        system_prompt = f"""You are an Ops Agent. Your goal is to set up the environment for the target code located at: {target_path}
1. Detect the language.
2. Start a Docker container for that language.
   - For PHP, use 'php:7.4-apache'. Map a local port (e.g. 8080) to container port 80. Format: `8080:80`. Map the code to /var/www/html.
   - For Python, use 'python:3.9'.
   - IF DOCKER RUN FAILS due to port conflict, TRY A DIFFERENT PORT (e.g., 8081, 8082).
3. Verify the service is running.
4. Call `EnvSaveTool` with the URL and container ID.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Initialize environment."}
        ]
        
        max_turns = 10
        tools = self.get_tool_definitions()
        
        env_info = {}

        for i in range(max_turns):
            self.log(f"Turn {i+1}/{max_turns}")
            
            if self.llm:
                response = self.llm.chat(messages, tools=tools)
            else:
                return {"status": "skipped"}
            
            if not response:
                break
                
            message = response['choices'][0]['message']
            tool_calls = message.get('tool_calls')
            messages.append(message)
            
            if message.get('content'):
                self.log(f"LLM: {message.get('content')}")
            
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    
                    # Robust JSON parsing
                    raw_args = tool_call['function']['arguments']
                    try:
                        args = json.loads(raw_args)
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                pass
                    except json.JSONDecodeError:
                        self.log(f"Error decoding arguments: {raw_args}")
                        args = {}
                    
                    if not isinstance(args, dict):
                         self.log(f"Error: arguments is not a dict: {type(args)}")
                         args = {}

                    self.log(f"Tool Call: {function_name}({args})")
                    
                    result = ""
                    if function_name == "DetectLanguageTool":
                        result = self.detect_language(args.get('dir_path', '.'), target_path)
                    elif function_name == "RunCommandTool":
                        import subprocess
                        try:
                            res = subprocess.run(args.get('command'), shell=True, capture_output=True, text=True)
                            result = res.stdout + res.stderr
                        except Exception as e:
                            result = str(e)
                    elif function_name == "DockerRunTool":
                        result = self.docker_run(
                            args.get('image'), 
                            args.get('ports'), 
                            args.get('volumes'), 
                            args.get('env'),
                            target_path
                        )
                    elif function_name == "DockerExecTool":
                        result = self.docker_exec(args.get('container_id'), args.get('command'))
                    elif function_name == "ListSourceCodeTreeTool":
                        result = self.list_source_code_tree(args.get('dir_path', '.'), target_path)
                    elif function_name == "EnvSaveTool":
                        env_info = args
                        result = "Environment saved."
                        self.log(f"Environment saved: {env_info}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": result
                    })
                    
                    if function_name == "EnvSaveTool":
                        return {"status": "completed", "env": env_info}

        return {"status": "completed", "env": env_info}
