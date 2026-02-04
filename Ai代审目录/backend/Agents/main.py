import os
import json
import subprocess
import time
import sys
from AnalyzeAgent import AnalyzeAgent
from OpsAgent import OpsAgent
from ReportAgent import ReportAgent
from VerifierAgent import VerifierAgent
from LLMClient import LLMClient

def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        # Fallback to example if config doesn't exist (or error out)
        print("Warning: config.json not found. Using defaults/environment variables.")
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}

def main():
    config = load_config()
    llm_config = config.get("llm", {})

    print("Initializing LLM Client...")
    llm_client = LLMClient(
        api_key=llm_config.get("api_key"),
        base_url=llm_config.get("base_url"),
        model=llm_config.get("model")
    )
    
    print("Initializing Agents...")
    ops_agent = OpsAgent(llm_client=llm_client)
    analyze_agent = AnalyzeAgent(llm_client=llm_client, max_vuln_count=10)
    verifier_agent = VerifierAgent(llm_client=llm_client)
    report_agent = ReportAgent(llm_client=llm_client)
    
    # Support command line argument for target path
    if len(sys.argv) > 1:
        target_path = os.path.abspath(sys.argv[1])
    else:
        target_path = os.path.abspath(config.get("default_target_path", "./uploads/upload"))
        
    print(f"Target path: {target_path}")
    
    # 0. Environment Setup via OpsAgent
    print("Starting Environment Setup (OpsAgent)...")
    env_context = {"target_path": target_path}
    ops_result = ops_agent.run(env_context)
    
    target_url = "http://127.0.0.1:8000" # Fallback
    container_id = None
    
    if ops_result.get("status") == "completed" and ops_result.get("env"):
        env_info = ops_result["env"]
        if env_info.get("url"):
            target_url = env_info["url"]
            print(f"Environment setup successfully at {target_url}")
        if env_info.get("container_id"):
            container_id = env_info["container_id"]
            
    # 1. Run Analysis
    print("Starting Analysis Phase...")
    
    analysis_context = {
        "target_path": target_path
    }
    
    # Check if report exists and load it to skip analysis (Optional optimization)
    # MODIFIED: Always run analysis regardless of existing report to ensure autonomy
    if False and os.path.exists("audit_report.json"):
        print("Loading existing audit report to skip analysis...")
        with open("audit_report.json", "r", encoding='utf-8') as f:
            report_data = json.load(f)
            analysis_result = {
                "tech_stack": report_data.get("tech_stack", {}),
                "vulns": report_data.get("vulns", [])
            }
            # Update analyze_agent found_vulns just in case
            analyze_agent.found_vulns = analysis_result["vulns"]
            analyze_agent.tech_stack = analysis_result["tech_stack"]
    else:
        try:
            print(f"[Main] Running AnalyzeAgent on {target_path}...")
            analysis_result = analyze_agent.run(analysis_context)
            print(f"[Main] AnalyzeAgent finished. Result keys: {analysis_result.keys()}")
        except Exception as e:
            print(f"Analysis failed with error: {e}")
            analysis_result = {
                "status": "failed", 
                "vulns": analyze_agent.found_vulns, 
                "tech_stack": analyze_agent.tech_stack
            }
    
    tech_stack = analysis_result.get("tech_stack", {})
    vulns = analysis_result.get("vulns", [])
    
    print(f"Identified Tech Stack: {tech_stack}")
    print(f"Found {len(vulns)} vulnerabilities.")
    if len(vulns) == 0:
        print("[Main] WARNING: No vulnerabilities found. Check AnalyzeAgent logs.")

    try:
        # 3. Verify each vulnerability
        for vuln in vulns:
            vuln_title = vuln.get('type') or vuln.get('title')
            print(f"\n--- Verifying: {vuln_title} ---")
            
            context = {
                "vuln": vuln,
                "target_url": target_url,
                "target_path": target_path
            }
            
            # Default verification status
            vuln['verified'] = False
            
            try:
                result = verifier_agent.run(context)
                print(f"Verification Result: {result}")
                
                # Check verification result
                if result.get("status") == "completed":
                    verify_data = result.get("result", {})
                    # If list (multiple attempts), check if any success
                    if isinstance(verify_data, list):
                        for attempt in verify_data:
                            if attempt.get("status") == "success":
                                vuln['verified'] = True
                                vuln['poc'] = attempt.get('poc', 'No PoC')
                                break
                    elif isinstance(verify_data, dict):
                         if verify_data.get("status") == "success":
                             vuln['verified'] = True
                             vuln['poc'] = verify_data.get('poc', 'No PoC')
            except Exception as e:
                print(f"Error verifying vuln: {e}")

    finally:
        # 4. Stop Sandbox
        if container_id:
            print(f"Stopping container {container_id}...")
            try:
                subprocess.run(["docker", "stop", container_id], check=False)
                subprocess.run(["docker", "rm", container_id], check=False)
            except Exception as e:
                print(f"Error cleaning up container: {e}")

    # 5. Save Final Audit Report
    final_report = {
        "tech_stack": tech_stack,
        "vulns": vulns
    }
    
    report_file = "audit_report.json"
    with open(report_file, "w", encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    print(f"\nFull Audit Report saved to {report_file}")
    
    # 6. Generate Human-Readable Report via ReportAgent
    print("Generating Final Report (ReportAgent)...")
    report_context = {
        "vulns": vulns,
        "tech_stack": tech_stack
    }
    report_agent.run(report_context)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR IN MAIN: {e}")
        import traceback
        traceback.print_exc()
