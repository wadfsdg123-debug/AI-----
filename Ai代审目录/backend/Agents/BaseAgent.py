class Agent:
    def __init__(self, name, description, llm_client=None):
        self.name = name
        self.description = description
        self.memory = None
        self.tools = []
        self.id = None
        self.llm = llm_client

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def set_id(self, agent_id):
        self.id = agent_id

    def get_id(self):
        return self.id

    def set_memory(self, memory):
        self.memory = memory

    def get_memory(self):
        return self.memory

    def register_tool(self, tool):
        self.tools.append(tool)

    def log(self, message):
        import time
        import json
        
        # Print to console
        print(f"[{self.name}] {message}", flush=True)
        
        # Log to file
        try:
            with open("agent_monitor.log", "a", encoding="utf-8") as f:
                entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "agent": self.name,
                    "message": str(message)
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def run(self, context):
        """
        Execute the agent's main logic.
        :param context: A dictionary containing task info, env info, etc.
        :return: Result of the execution
        """
        raise NotImplementedError("Agents must implement the run method")

    def common_system_prompt(self):
        return """You are working within a vulnerability discovery system. Some tools you call may have issues. If you encounter such problems or have improvement suggestions (e.g., what capabilities could be provided) to make completing this work more efficient, you can use the IssueTool to provide feedback.
If the user provides a list of subtasks, then you need to complete the subtasks in order. When finishing or abandoning a specific subtask, you must call the TaskListTool to update the status of the task list."""
