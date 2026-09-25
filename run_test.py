import os
import glob
import subprocess
import time
import sys
import re
from src.fuzzer import AdvancedBehavioralFuzzer

def extract_target_path(file_path):
    """
    Autonomously scans the text inside the server file to extract 
    the active REST endpoint route using regex.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Look for patterns like /api/v1/... or /api/v2/...
        matches = re.findall(r'"(/api/v[0-9]/[^"]+)"', content)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"[-] Could not read spec path for {file_path}: {str(e)}")
    
    # Fallback default path if regex doesn't match perfectly
    return "/api/v1/process"

def main():
    print("[*] Starting Autonomous Multi-Target Fuzzing Pipeline...")
    
    # Initialize your centralized master fuzzer instance
    fuzzer = AdvancedBehavioralFuzzer(base_url="http://localhost:9000", max_workers=5)
    
    # Autonomously find all python server files inside the tests/ directory
    search_pattern = os.path.join("tests", "*.py")
    test_servers = glob.glob(search_pattern)
    
    if not test_servers:
        print("[-] No test servers discovered inside the tests/ directory folder.")
        return
        
    print(f"[+] Discovered {len(test_servers)} unique test server frameworks to profile.")
    
    for server_file in sorted(test_servers):
        print("\n" + "="*70)
        print(f"[*] AUTONOMOUS EXECUTION: Booting up target script -> {server_file}")
        print("="*70)
        
        # 1. Discover the target route dynamically from the file's raw content
        dynamic_path = extract_target_path(server_file)
        print(f"[+] Dynamically mapped target route: {dynamic_path}")
        
        # 2. Configure the fuzzer's parameters on the fly based on the path layout
        if "v2" in dynamic_path:
            fuzzer.endpoints = [{"path": dynamic_path, "method": "POST", "blueprint": {"query": [], "body_properties": {"data_chunk": {"type": "string"}, "user_profile": {"type": "object"}, "transaction_id": {"type": "integer"}}}}]
            runs = 50
        else:
            fuzzer.endpoints = [{"path": dynamic_path, "method": "POST", "blueprint": {"query": [], "body_properties": {"data": {"type": "string"}}}}]
            runs = 30

        # 3. Spin up the server file as an independent background process
        server_proc = subprocess.Popen([sys.executable, server_file])
        time.sleep(2)  # Give the server port 2 seconds to bind securely to port 9000
        
        try:
            print(f"[*] Launching dynamic fuzz loop wrapper ({runs} iterations)...")
            fuzzer.run_fuzz_session(total_runs=runs)
        except Exception as run_error:
            print(f"[-] Error occurred while fuzzing {server_file}: {str(run_error)}")
        finally:
            # 4. Safely kill the active server process before looping to the next file
            print(f"[*] Shutting down target script process safely -> {server_file}")
            server_proc.terminate()
            server_proc.wait()
            
        # Give the operating system network sockets a 2-second cooldown to avoid port conflicts
        time.sleep(2)
        
    print("\n[+] Pipeline Complete! All discovered test targets successfully audited.")

if __name__ == "__main__":
    main()
