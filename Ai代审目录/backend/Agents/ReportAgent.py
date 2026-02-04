from BaseAgent import Agent
import uuid

class ReportAgent(Agent):
    def __init__(self, llm_client=None, report_type="verifier"):
        super().__init__("ReportCommonAgent", 
                         "This is an AI assistant designed for writing vulnerability reports.",
                         llm_client)
        self.report_type = report_type
        
        # Register tools
        self.register_tool("ReportVulnTool") # Implied from Go code
        self.register_tool("IssueTool") # Likely needed
        
        self.set_id(f"{self.name}-{uuid.uuid4()}")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "ReportVulnTool",
                    "description": "Save the final vulnerability report.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "report_content": {"type": "string", "description": "The full markdown content of the report."}
                        },
                        "required": ["report_content"]
                    }
                }
            }
        ]

    def report_vuln(self, content):
        import os
        with open("final_report.md", "w", encoding="utf-8") as f:
            f.write(content)
        return "Report saved to final_report.md"

    def run(self, context):
        import json
        self.log(f"Starting reporting task (Type: {self.report_type})...")
        
        vulns = context.get("vulns", [])
        tech_stack = context.get("tech_stack", {})
        
        vuln_text = json.dumps(vulns, indent=2)
        tech_text = json.dumps(tech_stack, indent=2)
        
        system_prompt = f"""You are a Report Agent. Your goal is to generate a comprehensive vulnerability report based on the findings.
        
Found Vulnerabilities:
{vuln_text}

Technology Stack:
{tech_text}

Please generate a detailed Markdown report including:
1. Executive Summary
2. Vulnerability Details (for each finding)
   - Title
   - Severity
   - File/Line
   - Description
   - Remediation
3. Conclusion

If NO vulnerabilities were found (empty list), please generate a report stating that no obvious vulnerabilities were detected by the automated scan, but recommend manual review of critical areas (e.g., file upload logic, authentication).

After generating the content, call `ReportVulnTool` to save it.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the report."}
        ]
        
        max_turns = 5
        tools = self.get_tool_definitions()
        
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
                    if function_name == "ReportVulnTool":
                        result = self.report_vuln(args.get('report_content'))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": result
                        })
                        return {"status": "completed", "report_path": "final_report.md"}
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": result
                    })

        return {"status": "completed"}
