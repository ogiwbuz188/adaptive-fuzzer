import subprocess
import time
import sys
from src.fuzzer import AdvancedBehavioralFuzzer

def main():
    print("[*] Spinning up mock vulnerable system architecture...")
    server_proc = subprocess.Popen([sys.executable, "tests/mock_server.py"])
    time.sleep(2) 

    try:
        fuzzer = AdvancedBehavioralFuzzer(base_url="http://localhost:9000", max_workers=4)
        fuzzer.discover_via_spec("http://localhost:9000/swagger.json")
        fuzzer.run_fuzz_session(total_runs=50)
    finally:
        print("[*] Safely destroying backend server resources...")
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    main()
