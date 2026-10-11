import os
import glob
import subprocess
import time
import sys
import re
from src.fuzzer import AdvancedBehavioralFuzzer


def extract_target_path(file_path):
    """Extract the API endpoint path from a test server file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r'"(/api/v[0-9]/[^"]+)"', content)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"[-] Could not read spec path for {file_path}: {str(e)}")
    return "/api/v1/process"


def get_api_version(path):
    """Extract API version from endpoint path (v1, v2, v3, etc.)."""
    match = re.search(r"/api/(v\d+)/", path)
    return match.group(1) if match else "v1"


def build_endpoint_config(dynamic_path):
    """
    Dynamically build endpoint configuration based on API version.
    This removes the need to edit run_test.py whenever a new test file is added.
    
    Returns: (endpoint_list, num_runs, api_version)
    """
    api_version = get_api_version(dynamic_path)

    schemas = {
        "v3": {
            "auth_metadata": {"type": "object"},
            "transaction_payload": {"type": "object"},
            "compliance_checksum": {"type": "string"},
        },
        "v2": {
            "data_chunk": {"type": "string"},
            "user_profile": {"type": "object"},
            "transaction_id": {"type": "string"},
        },
        "v1": {
            "data": {"type": "string"},
        },
    }

    body_properties = schemas.get(api_version, schemas["v1"])
    runs_by_version = {"v3": 50, "v2": 50, "v1": 30}
    runs = runs_by_version.get(api_version, 30)

    endpoint = {
        "path": dynamic_path,
        "method": "POST",
        "blueprint": {
            "query": [],
            "body_properties": body_properties,
        },
    }

    return [endpoint], runs, api_version


def main():
    print("[*] Starting Autonomous Multi-Target Isolated Fuzzing Pipeline...")

    fuzzer = AdvancedBehavioralFuzzer(base_url="http://localhost:9000", max_workers=5)

    search_pattern = os.path.join("tests", "*.py")
    test_servers = glob.glob(search_pattern)

    if not test_servers:
        print("[-] No test servers discovered inside the tests/ directory folder.")
        return

    print(f"[+] Discovered {len(test_servers)} unique test environments to profile.")

    for server_file in sorted(test_servers):
        print("\n" + "=" * 70)
        print(f"[*] AUTONOMOUS EXECUTION: Booting up target script -> {server_file}")
        print("=" * 70)

        fuzzer.findings = []
        dynamic_path = extract_target_path(server_file)
        print(f"[+] Dynamically mapped target route: {dynamic_path}")

        fuzzer.endpoints, runs, api_version = build_endpoint_config(dynamic_path)
        print(f"[+] Configured for API {api_version} with {runs} test runs")

        file_prefix = os.path.splitext(os.path.basename(server_file))[0]
        report_name = f"{file_prefix}_dashboard.html"

        server_proc = subprocess.Popen([sys.executable, server_file])
        time.sleep(2)

        try:
            print(f"[*] Launching dynamic fuzz loop wrapper ({runs} iterations)...")
            fuzzer.run_fuzz_session(total_runs=runs)
        except Exception as run_error:
            print(f"[-] Error occurred while fuzzing {server_file}: {str(run_error)}")
        finally:
            print(f"[*] Shutting down target script process safely -> {server_file}")
            server_proc.terminate()
            server_proc.wait()

        fuzzer.generate_web_dashboard(report_name=report_name)
        time.sleep(2)

    print("\n[+] Pipeline Complete! All isolated reports successfully compiled.")


if __name__ == "__main__":
    main()
