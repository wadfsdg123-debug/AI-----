
import os
import json
from agents.base_agent import BaseAgent
from core.prompts import Prompts

class ReporterAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReporterAgent")

    def run(self, ops_data, analyze_data, hacker_data, output_path="report.md"):
        """
        汇总数据生成报告。
        """
        print(f"[{self.name}] Generating security audit report...")
        
        # DEBUG: Dump data
        with open("debug_data.json", "w", encoding="utf-8") as f:
            json.dump({
                "ops": ops_data,
                "analyze": analyze_data,
                "hacker": hacker_data
            }, f, indent=2, ensure_ascii=False)
        print(f"[{self.name}] Debug data saved to debug_data.json")

        # 格式化数据为字符串供 LLM 阅读
        ops_str = json.dumps(ops_data, indent=2, ensure_ascii=False)
        analyze_str = json.dumps(analyze_data, indent=2, ensure_ascii=False)
        hacker_str = json.dumps(hacker_data, indent=2, ensure_ascii=False)
        
        user_prompt = Prompts.REPORTER_TEMPLATE.format(
            ops_data=ops_str,
            analyze_data=analyze_str,
            hacker_data=hacker_str
        )
        
        report_content = self.llm.chat(Prompts.REPORTER_SYSTEM, user_prompt)
        
        # 清理报告内容，移除可能的 Markdown 代码块标记和开场白
        cleaned_report = report_content.strip()
        
        # 移除 ```markdown 或 ```
        if cleaned_report.startswith("```markdown"):
            cleaned_report = cleaned_report[11:]
        elif cleaned_report.startswith("```"):
            cleaned_report = cleaned_report[3:]
        if cleaned_report.endswith("```"):
            cleaned_report = cleaned_report[:-3]
            
        cleaned_report = cleaned_report.strip()

        # 强制确保以标题开始（如果 LLM 还是说了废话）
        # 查找第一个一级标题的位置
        title_index = cleaned_report.find("# 安全审计报告")
        if title_index != -1:
            cleaned_report = cleaned_report[title_index:]
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_report)
            print(f"[{self.name}] Report saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving report: {e}")
            return None
