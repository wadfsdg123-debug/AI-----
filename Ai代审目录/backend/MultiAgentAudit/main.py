
import os
import sys
import logging
import io
import argparse
from dotenv import load_dotenv

# 强制设置 stdout/stderr 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

from agents.ops_agent import OpsAgent
from agents.analyze_agent import AnalyzeAgent
from agents.hacker_agent import HackerAgent
from agents.reporter_agent import ReporterAgent

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Multi-Agent Security Audit System")
    parser.add_argument("path", nargs="?", default="uploads", help="Path to the file or directory to audit (default: uploads)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.path)
    
    # 确保目标存在
    if not os.path.exists(target_dir):
        # 如果是默认的 uploads 且不存在，则创建并提示
        if args.path == "uploads":
            os.makedirs(target_dir, exist_ok=True)
            print(f"Created default upload directory: {target_dir}")
            print("Please upload files to this directory and run again.")
            return
        else:
            print(f"Error: Target path '{target_dir}' not found.")
            return

    print("=== Multi-Agent Code Audit System Started ===\n")
    logging.info(f"System started. Target: {target_dir}")

    # 1. OpsAgent: 环境识别
    ops_agent = OpsAgent()
    env_data = ops_agent.run(target_dir)
    logging.info(f"OpsAgent result: {env_data}")
    if not env_data:
        print("OpsAgent failed to identify environment. Exiting.")
        return
    print("-" * 50)

    # 2. AnalyzeAgent: 代码审计
    analyze_agent = AnalyzeAgent()
    analyze_results = analyze_agent.run(target_dir, env_data)
    
    vuln_count = len(analyze_results.get("vulnerabilities", []))
    print(f"[Main Debug] AnalyzeAgent found {vuln_count} vulnerabilities.")
    logging.info(f"AnalyzeAgent found {vuln_count} vulnerabilities: {analyze_results}")

    if not analyze_results.get("vulnerabilities"):
        print("AnalyzeAgent found no vulnerabilities. Exiting.")
        return
    print("-" * 50)

    # 3. HackerAgent: 漏洞验证
    hacker_agent = HackerAgent()
    hacker_results = hacker_agent.run(analyze_results, env_data)
    logging.info(f"HackerAgent finished.")
    print("-" * 50)

    # 4. ReporterAgent: 生成报告
    reporter_agent = ReporterAgent()
    try:
        report_path = reporter_agent.run(env_data, analyze_results, hacker_results)
        logging.info(f"ReporterAgent finished. Report path: {report_path}")
    except Exception as e:
        logging.error(f"ReporterAgent failed: {e}", exc_info=True)
        print(f"ReporterAgent failed: {e}")
        report_path = None
    
    print("\n=== Audit Completed ===")
    if report_path:
        print(f"Report available at: {report_path}")

if __name__ == "__main__":
    main()
