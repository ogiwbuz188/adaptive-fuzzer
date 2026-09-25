import os
import glob
import subprocess
import time
import sys
import re
from src.fuzzer import AdvancedBehavioralFuzzer

def extract_target_path(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r'"(/api/v[0-9]/[^"]+)"', content)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"[-] Could not read spec path for {file_path}: {str(e)}")
    return "/api/v1/process"

def main():
    print("[*] Starting Autonomous Multi-Target Isolated Fuzzing Pipeline...")
    
    fuzzer = AdvancedBehavioralFuzzer(base_url="http://localhost:9000", max_workers=5)
    
    search_pattern = os.path.join("tests", "*.py")
    test_servers = glob.glob(search_pattern)
    
    if not test_servers:
        print("[-] No test servers discovered inside the tests/ directory folder.")
        return
        
    for server_file in sorted(test_servers):
        print("\n" + "="*70)
        print(f"[*] AUTONOMOUS EXECUTION: Booting up target script -> {server_file}")
        print("="*70)
        
        # Reset findings pool so reports don't mix
        fuzzer.findings = []
        
        dynamic_path = extract_target_path(server_file)
        print(f"[+] Dynamically mapped target route: {dynamic_path}")
        
        if "v2" in dynamic_path:
            fuzzer.endpoints = [{"path": dynamic_path, "method": "POST", "blueprint": {"query": [], "body_properties": {"data_chunk": {"type": "string"}, "user_profile": {"type": "object"}, "transaction_id": {"type": "integer"}}}}]
            runs = 50
        else:
            fuzzer.endpoints = [{"path": dynamic_path, "method": "POST", "blueprint": {"query": [], "body_properties": {"data": {"type": "string"}}}}]
            runs = 30

        server_proc = subprocess.Popen([sys.executable, server_file])
        time.sleep(2)  
        
        # FIXED: Extracting index [0] to get the raw name string element cleanly
        file_prefix = os.path.splitext(os.path.basename(server_file))[0]
        custom_report_name = f"{file_prefix}_dashboard.html"
        
        try:
            print(f"[*] Launching dynamic fuzz loop wrapper ({runs} iterations)...")
            fuzzer.run_fuzz_session(total_runs=runs)
        except Exception as run_error:
            print(f"[-] Error occurred while fuzzing {server_file}: {str(run_error)}")
        finally:
            print(f"[*] Shutting down target script process safely -> {server_file}")
            server_proc.terminate()
            server_proc.wait()
            
        fuzzer.generate_web_dashboard(report_name=custom_report_name)
        time.sleep(2)
        
    print("\n[+] Pipeline Complete! Isolated reports successfully compiled.")

if __name__ == "__main__":
    main()
