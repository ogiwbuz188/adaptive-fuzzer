#Copyright (c) 2026 Japneet Kaur [ogiwbuz188]

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at :

#   http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, softwaredistributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
#language governing permissions and limitations under the License

import os
import glob
import subprocess
import html
import time
import sys
import re
import threading
import requests
from src.fuzzer import AdvancedBehavioralFuzzer


def extract_target_path(file_path):
    """Extract the API endpoint path from a research benchmark file.

    This is a lightweight fallback for servers that don't expose a
    swagger.json. Prefer the fuzzer's discover_via_spec when available.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Find all occurrences and return the first sensible one
        matches = re.findall(r'"(/api/v[0-9]+/[^"\s]+)"', content)
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
    runs_by_version = {"v3": 80, "v2": 60, "v1": 40}
    runs = runs_by_version.get(api_version, 40)

    endpoint = {
        "path": dynamic_path,
        "method": "POST",
        "blueprint": {
            "query": [],
            "body_properties": body_properties,
        },
    }

    return [endpoint], runs, api_version


def _monitor_target(server_proc, fuzzer, file_prefix, poll_interval=0.5):
    """Monitor a target process for unexpected exits and scan its logs
    for crash markers. When detected, surface them into fuzzer findings.
    """
    stdout_path = f"{file_prefix}.out"
    stderr_path = f"{file_prefix}.err"

    def tail_last(path, limit=2048):
        try:
            with open(path, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                if size == 0:
                    return b""
                read_size = min(limit, size)
                fh.seek(-read_size, os.SEEK_END)
                return fh.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    crash_markers = [
        "segmentation fault",
        "stack overflow",
        "traceback",
        "exception",
        "fatal",
        "panic:",
        "core dumped",
        "oom",
        "outofmemory",
    ]

    while True:
        # Check if process ended unexpectedly
        code = server_proc.poll()
        if code is not None and code != 0:
            evidence = tail_last(stderr_path, 4096) or tail_last(stdout_path, 4096)
            fuzzer.log_anomaly(
                "TARGET_CRASHED",
                0,
                "PROCESS",
                server_proc.args[1] if len(server_proc.args) > 1 else "",
                "PROCESS_EXIT",
                evidence,
            )
            break
        # Scan logs for crash markers
        logs = tail_last(stderr_path, 4096) + "\n" + tail_last(stdout_path, 4096)
        if any(marker in logs.lower() for marker in crash_markers):
            fuzzer.log_anomaly(
                "TARGET_LOG_CRASH_EVIDENCE",
                0,
                "PROCESS_LOG",
                server_proc.args[1] if len(server_proc.args) > 1 else "",
                "LOG_TRACE",
                logs[-2000:],
            )
            # don't break immediately — we keep monitoring until process exits
        time.sleep(poll_interval)


def main():
    print("[*] Starting Autonomous Multi-Target Isolated Fuzzing Pipeline...")

    fuzzer = AdvancedBehavioralFuzzer(base_url="http://localhost:9000", max_workers=8)

    # Recursively search for all Python files in research_benchmark and its subdirectories
    search_pattern = os.path.join("research_benchmark", "**", "*.py")
    test_servers = glob.glob(search_pattern, recursive=True)

    if not test_servers:
        print("[-] No benchmark servers discovered inside the research_benchmark/ directory.")
        return

    print(f"[+] Discovered {len(test_servers)} unique research benchmark environments to profile.")

    for server_file in sorted(test_servers):
        print("\n" + "=" * 70)
        print(f"[*] AUTONOMOUS EXECUTION: Booting up target script -> {server_file}")
        print("=" * 70)

        fuzzer.findings = []

        # If server exposes swagger, prefer that for discovery. We'll still
        # fallback to static extraction where needed.
        dynamic_path = extract_target_path(server_file)
        print(f"[+] Fallback mapped target route: {dynamic_path}")

        endpoints, runs, api_version = build_endpoint_config(dynamic_path)
        fuzzer.endpoints = endpoints
        print(f"[+] Configured for API {api_version} with {runs} test runs")

        file_prefix = os.path.splitext(os.path.basename(server_file))[0]
        stdout_path = f"{file_prefix}.out"
        stderr_path = f"{file_prefix}.err"

        with open(stdout_path, "wb") as out_f, open(stderr_path, "wb") as err_f:
            server_proc = subprocess.Popen([sys.executable, server_file], stdout=out_f, stderr=err_f)

        # Give the server a moment to start
        time.sleep(1.0)

        # After boot, try to let the fuzzer probe /swagger.json to discover
        # a richer set of endpoints when available.
        try:
            resp = requests.get("http://localhost:9000/swagger.json", timeout=1)
            if resp.status_code == 200:
                try:
                    fuzzer.discover_via_spec("http://localhost:9000/swagger.json")
                    print(f"[+] Discovered {len(fuzzer.endpoints)} endpoints via swagger.json")
                    # override runs based on new endpoints density
                    runs = max(runs, 30 * len(fuzzer.endpoints))
                except Exception as e:
                    print(f"[-] Swagger discovery failed: {e}")
        except Exception:
            # swagger not present; continue with fallback
            pass

        # Start monitor thread to capture crashes printed to server logs and unexpected exits
        monitor_thread = threading.Thread(target=_monitor_target, args=(server_proc, fuzzer, file_prefix), daemon=True)
        monitor_thread.start()

        try:
            print(f"[*] Launching dynamic fuzz loop wrapper ({runs} iterations)...")
            fuzzer.run_fuzz_session(total_runs=runs)
        except Exception as run_error:
            print(f"[-] Error occurred while fuzzing {server_file}: {str(run_error)}")
        finally:
            print(f"[*] Shutting down target script process safely -> {server_file}")
            # Ask the process to terminate and wait a short time
            try:
                server_proc.terminate()
                server_proc.wait(timeout=3)
            except Exception:
                server_proc.kill()

        # Ensure monitor thread sees final logs
        time.sleep(0.5)

        # Merge any latest logs into evidence files saved with the report
        fuzzer.generate_web_dashboard(report_name=f"{file_prefix}_dashboard.html")
        time.sleep(1)

    print("\n[+] Pipeline Complete! All isolated reports successfully compiled.")


if __name__ == "__main__":
    main()
