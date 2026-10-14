#Copyright (c) 2026 Japneet Kaur [ogiwbuz188]

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at :

#   http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, softwaredistributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
#language governing permissions and limitations under the License.

import os
import csv
import json
import random
import string
import threading
import time
import traceback
import html
import math
import statistics
import hashlib
import socket
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


HOST = "127.0.0.1"
PORT = 9000
BASE_URL = f"http://{HOST}:{PORT}"
REPORT_NAME = "mock_server_dashboard.html"


class MockServerHandler(BaseHTTPRequestHandler):
    """Local HTTP target used by the fuzzer."""

    def log_message(self, format_string, *args):
        # Keep GitHub Actions output focused on the fuzzer.
        return

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, status_code, text):
        body = text.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {
                "paths": {
                    "/api/v1/process": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "data": {"type": "string"},
                                                "config": {"type": "object"},
                                            },
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            self.send_json(200, schema)
            return

        self.send_text(404, "Not found")

    def do_POST(self):
        if self.path != "/api/v1/process":
            self.send_text(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_text(400, "Invalid JSON")
            return

        payload = data.get("data") or data.get("config")

        if isinstance(payload, str) and len(payload) > 10000:
            self.send_text(
                500,
                "Fatal Error: Segmentation fault. "
                "Heap allocation memory limit exhausted.",
            )
            return

        if isinstance(payload, dict) and any(
            isinstance(key, str) and key in string.ascii_letters
            for key in payload
        ):
            time.sleep(1.6)
            self.send_json(200, {"status": "heavy_processing_complete"})
            return

        if isinstance(payload, str) and "etc/passwd" in payload:
            self.send_text(
                500,
                "Internal Exception: java.io.FileNotFoundException: "
                "Access denied to local system configurations.",
            )
            return

        self.send_json(200, {"status": "accepted"})


class AdvancedBehavioralFuzzer:
    def __init__(self, base_url, max_workers=5):
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers
        self.endpoints = []
        self.findings = []
        self.total_requests = 0
        self.findings_lock = threading.Lock()

        # Baselines collected at discovery time so anomalies are relative
        # to the target's normal behavior instead of exact bug signatures.
        self.baselines = {}  # key: (method, path) -> stats dict
        self.baseline_samples = int(os.environ.get("FUZZ_BASELINE_SAMPLES", "8"))
        self.z_threshold = float(os.environ.get("FUZZ_Z_THRESHOLD", "2.5"))

        # Response signatures tracking to detect 'input ignored' behavior
        self.response_signatures = {}  # key: (method,path) -> Counter(sig)
        self.signatures_lock = threading.Lock()

        # Seeds that provoked anomalies — used for feedback-directed fuzzing
        self.interesting_seeds = []
        self.interesting_lock = threading.Lock()

        self.user_agents = [
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15"
            ),
            (
                "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) "
                "Gecko/20100101 Firefox/119.0"
            ),
        ]

        # Expanded corpus that covers previously discovered seeds and new edge cases
        self.corpus = [
            "test_payload",
            '{"admin": true}',
            "' OR 1=1 --",
            "<script>alert(1)</script>",
            "A" * 1000,
            "A" * 30000,
            "\x00\x00\x00",
            "\ud83d\ude00" * 200,
            "-1",
            "2147483647",
            str(2 ** 63),
            "null",
            "[]",
            "{}",
            "NaN",
            "Infinity",
        ]

    def _collect_baseline(self, method, path, blueprint, samples=None, timeout=3):
        samples = samples or self.baseline_samples
        lens = []
        lats = []
        statuses = []
        ctypes = set()

        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {"User-Agent": random.choice(self.user_agents)}

        for _ in range(samples):
            try:
                start = time.time()
                if method in {"POST", "PUT"}:
                    if blueprint.get("body_properties"):
                        payload = self.build_payload(blueprint["body_properties"])
                        r = requests.request(method, url, json=payload, timeout=timeout, headers=headers)
                    else:
                        payload = {"input": "warmup"}
                        r = requests.request(method, url, json=payload, timeout=timeout, headers=headers)
                else:
                    params = {}
                    if blueprint.get("query"):
                        params[blueprint["query"][0]] = "warmup"
                    r = requests.request(method, url, params=params, timeout=timeout, headers=headers)
                dur = time.time() - start
                lats.append(dur)
                statuses.append(r.status_code)
                cur_len = len(r.content or b"")
                lens.append(cur_len)
                ctypes.add(r.headers.get("Content-Type", "").split(";")[0].strip())
                time.sleep(0.06)
            except Exception:
                # Record a high-latency/zero-length sample to bias detection
                lats.append(timeout)
                lens.append(0)
                statuses.append(0)

        baseline = {
            "len_mean": statistics.mean(lens) if lens else 0,
            "len_std": statistics.pstdev(lens) if len(lens) > 1 else 0,
            "lat_mean": statistics.mean(lats) if lats else 0,
            "lat_std": statistics.pstdev(lats) if len(lats) > 1 else 0,
            "status_counter": Counter(statuses),
            "content_types": ctypes,
        }
        return baseline

    def discover_via_spec(self, spec_url):
        print(f"[*] Extracting routes from schema: {spec_url}", flush=True)

        response = requests.get(spec_url, timeout=5)
        response.raise_for_status()
        spec = response.json()

        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                method = method.upper()

                if method not in {"GET", "POST", "PUT", "DELETE"}:
                    continue

                blueprint = {
                    "query": [],
                    "body_properties": {},
                }

                for parameter in details.get("parameters", []):
                    if parameter.get("in") in {"query", "formData"}:
                        blueprint["query"].append(parameter.get("name"))

                request_body = details.get("requestBody", {})
                content = request_body.get("content", {})
                json_schema = content.get("application/json", {}).get(
                    "schema", {}
                )

                if "properties" in json_schema:
                    blueprint["body_properties"] = json_schema["properties"]

                self.endpoints.append(
                    {
                        "path": path,
                        "method": method,
                        "blueprint": blueprint,
                    }
                )

        if not self.endpoints:
            raise RuntimeError("No supported endpoints were discovered")

        print(
            f"[+] Scan map locked. "
            f"Tracked {len(self.endpoints)} route(s).",
            flush=True,
        )

        # Build richer baselines using multiple warmup samples
        for ep in self.endpoints:
            try:
                baseline = self._collect_baseline(ep["method"], ep["path"], ep["blueprint"])
                self.baselines[(ep["method"], ep["path"])] = baseline
            except Exception as e:
                print(f"[-] Baseline collection failed for {ep}: {e}")
                self.baselines[(ep["method"], ep["path"])]= {
                    "len_mean": 0,
                    "len_std": 0,
                    "lat_mean": 0,
                    "lat_std": 0,
                    "status_counter": Counter(),
                    "content_types": set(),
                }

    def mutate(self, seed):
        # Occasionally prefer interesting seeds discovered during earlier runs
        with self.interesting_lock:
            if self.interesting_seeds and random.random() < 0.18:
                seed = random.choice(self.interesting_seeds)

        strategy = random.choice(
            [
                "overflow",
                "type_scramble",
                "nested_json",
                "traversal",
                "format_string",
                "int_edge",
                "float_edge",
                "partial_close",
            ]
        )

        if strategy == "overflow":
            return str(seed) * random.randint(20, 80)

        if strategy == "type_scramble":
            return random.choice(
                [None, True, False, -1, 999999999999, [], {}]
            )

        if strategy == "nested_json":
            return {
                random.choice(string.ascii_letters): {
                    random.choice(string.ascii_letters): seed
                }
            }

        if strategy == "traversal":
            return "../" * random.randint(6, 18) + "etc/passwd"

        if strategy == "format_string":
            return "%x%s" * random.randint(4, 16)

        if strategy == "int_edge":
            return random.choice([-2147483649, -9223372036854775809, 2**63 - 1, 2**63])

        if strategy == "float_edge":
            return random.choice([float("nan"), float("inf"), -float("inf"), 1e309])

        if strategy == "partial_close":
            # Marker object the worker will interpret to send a partial request
            return {"__partial_close__": True, "data": str(seed)}

        return seed

    def build_payload(self, properties):
        payload = {}

        for key, details in properties.items():
            expected_type = details.get("type", "string")

            if random.random() < 0.30:
                payload[key] = self.mutate(random.choice(self.corpus))
            elif expected_type == "object":
                nested_properties = details.get(
                    "properties",
                    {"nested_fallback": {"type": "string"}},
                )
                payload[key] = self.build_payload(nested_properties)
            elif expected_type == "array":
                payload[key] = [
                    self.mutate(random.choice(self.corpus))
                ]
            else:
                payload[key] = self.mutate(
                    random.choice(self.corpus)
                )

        return payload

    def _zscore(self, value, mean, std):
        if std == 0:
            # if no variability, consider only large absolute deviations
            return abs(value - mean) / (mean + 1)
        return abs((value - mean) / std)

    def log_anomaly(
        self,
        classification,
        status,
        method,
        url,
        payload,
        evidence,
    ):
        finding = {
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(),
            ),
            "type": classification,
            "status": status,
            "method": method,
            "url": url,
            "payload": str(payload)[:200],
            "evidence": str(evidence)[:500],
        }

        with self.findings_lock:
            self.findings.append(finding)

        # If anomaly came from a payload, keep it as an interesting seed
        try:
            with self.interesting_lock:
                if payload and payload not in self.interesting_seeds:
                    self.interesting_seeds.append(payload)
                    # keep the interesting list bounded
                    if len(self.interesting_seeds) > 200:
                        self.interesting_seeds = self.interesting_seeds[-200:]
        except Exception:
            pass

        print(
            f"[!] {classification}: {method} {url} "
            f"(status={status})",
            flush=True,
        )

    def analyze(self, response, duration, method, url, send_payload):
        """Analyze HTTP response for symptomatic indicators using statistical
        and heuristic checks. This intentionally searches for symptoms (not
        specific bug names) so unknown bugs can be discovered.
        """
        anomalies = []

        # Normalize body
        try:
            body = (response.text or "").lower()
        except Exception:
            body = ""

        status = response.status_code if hasattr(response, "status_code") else 0

        # Status-based
        if status >= 500:
            anomalies.append("500_INTERNAL_SERVER_ERROR")
        elif status == 413:
            anomalies.append("413_PAYLOAD_TOO_LARGE")
        elif status == 429:
            anomalies.append("429_RATE_LIMIT_LOCK")

        # Latency: compare vs baseline using z-score
        parsed = urlparse(url)
        path = parsed.path
        baseline = self.baselines.get((method, path))

        cur_len = len(response.content or b"")

        if baseline:
            size_z = self._zscore(cur_len, baseline.get("len_mean", 0), baseline.get("len_std", 0))
            lat_z = self._zscore(duration, baseline.get("lat_mean", 0), baseline.get("lat_std", 0))

            if size_z > self.z_threshold:
                anomalies.append("RESPONSE_SIZE_OUTLIER")
            if lat_z > self.z_threshold:
                anomalies.append("LATENCY_OUTLIER")

            # Content-Type deviation
            ctype = response.headers.get("Content-Type", "").split(";")[0].strip()
            if baseline.get("content_types") and ctype and ctype not in baseline.get("content_types"):
                anomalies.append("CONTENTTYPE_MISMATCH")
        else:
            # Heuristics when no baseline available
            if cur_len == 0:
                anomalies.append("EMPTY_RESPONSE_BODY")
            elif cur_len > 200000:
                anomalies.append("UNEXPECTED_LARGE_RESPONSE")

        # Content-Length header mismatch
        hdr_len = response.headers.get("Content-Length")
        if hdr_len is not None:
            try:
                if int(hdr_len) != cur_len:
                    anomalies.append("CONTENT_LENGTH_MISMATCH")
            except Exception:
                anomalies.append("INVALID_CONTENT_LENGTH_HEADER")

        # Textual crash markers
        crash_markers = [
            "segmentation fault",
            "stack overflow",
            "nullpointerexception",
            "null pointer exception",
            "traceback",
            "exception",
            "fatal",
            "panic:",
            "core dumped",
            "oom",
            "outofmemory",
            "memoryerror",
        ]

        for marker in crash_markers:
            if marker in body:
                anomalies.append("STACK_OR_FATAL_TRACE")
                break

        # JSON well-formedness
        ctype_l = response.headers.get("Content-Type", "").lower()
        if "application/json" in ctype_l:
            try:
                response.json()
            except Exception:
                anomalies.append("MALFORMED_JSON_RESPONSE")
        else:
            if ("text" in ctype_l or "html" in ctype_l or ctype_l == "") and b"\x00" in (response.content or b""):
                anomalies.append("BINARY_IN_TEXT_RESPONSE")

        # Response-signature tracking to detect 'input ignored' behaviour
        sig = (response.status_code, hashlib.sha256(response.content or b"").hexdigest())
        key = (method, path)
        with self.signatures_lock:
            ctr = self.response_signatures.setdefault(key, Counter())
            ctr[sig] += 1
            total = sum(ctr.values())
            top_count = ctr.most_common(1)[0][1] if ctr else 0
            if total >= 12 and (top_count / total) > 0.80:
                anomalies.append("INPUT_IGNORED_OR_FILTERED")

        # Surface anomalies
        for anomaly in set(anomalies):
            evidence = response.text[:1000] if hasattr(response, "text") else b""
            self.log_anomaly(anomaly, status, method, url, send_payload, evidence)

    def _send_partial_http(self, url, method, headers, body_bytes, timeout=2):
        """Send a partial HTTP request and close the socket to try to trigger
        fragile parsers that crash on truncated input.
        Returns a synthetic response-like object for analysis.
        """
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"

        req_lines = [f"{method} {path} HTTP/1.1", f"Host: {host}"]
        for k, v in (headers or {}).items():
            req_lines.append(f"{k}: {v}")
        req_lines.append(f"Content-Length: {len(body_bytes)}")
        req_lines.append("")
        req_head = "\r\n".join(req_lines).encode("utf-8")

        try:
            conn = socket.create_connection((host, port), timeout=timeout)
            conn.sendall(req_head + body_bytes[: max(1, len(body_bytes) // 4)])
            # Intentionally close early
            conn.close()
            # Build a synthetic response indicating we closed early
            class _R:
                status_code = 0
                headers = {}
                content = b""
                text = ""
            return _R()
        except Exception:
            class _R:
                status_code = 0
                headers = {}
                content = b""
                text = ""
            return _R()

    def fuzz_worker(self, target):
        method = target["method"]
        path = target["path"]
        blueprint = target["blueprint"]
        url = urljoin(self.base_url + "/", path.lstrip("/"))

        try:
            time.sleep(random.uniform(0.02, 0.12))

            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "application/json",
            }

            request_kwargs = {
                "timeout": 6,
                "headers": headers,
            }

            partial_probe = False
            if method in {"POST", "PUT"}:
                if blueprint["body_properties"]:
                    payload = self.build_payload(
                        blueprint["body_properties"]
                    )
                else:
                    payload = {
                        "input": self.mutate(
                            random.choice(self.corpus)
                        )
                    }

                # Detect if mutate returned a partial-close marker
                if isinstance(payload, dict) and payload.get("__partial_close__"):
                    partial_probe = True
                    body_bytes = json.dumps({k: v for k, v in payload.items() if k != "__partial_close__"}).encode("utf-8")
                else:
                    request_kwargs["json"] = payload
            else:
                if blueprint["query"]:
                    parameter = random.choice(blueprint["query"])
                else:
                    parameter = "input"

                payload = {
                    parameter: self.mutate(
                        random.choice(self.corpus)
                    )
                }
                request_kwargs["params"] = payload

            start = time.time()

            if partial_probe:
                # send a truncated request using raw socket
                response = self._send_partial_http(url, method, headers, body_bytes)
                duration = time.time() - start
            else:
                response = requests.request(
                    method,
                    url,
                    **request_kwargs,
                )
                duration = time.time() - start

            # Analyze response for symptomatic indications of failure
            self.analyze(
                response,
                duration,
                method,
                url,
                payload,
            )

        except requests.exceptions.Timeout as error:
            self.log_anomaly(
                "TIMEOUT_EXHAUSTION",
                504,
                method,
                url,
                "TIMEOUT",
                str(error),
            )

        except requests.exceptions.ConnectionError as error:
            # Connection errors are strong signals of crashes / process exits
            self.log_anomaly(
                "CONNECTION_REFUSED_OR_RESET",
                0,
                method,
                url,
                "CONN_ERR",
                repr(error),
            )

        except Exception as error:
            self.log_anomaly(
                "CONNECTION_DROP_OR_DATA_FAULT",
                0,
                method,
                url,
                "PAYLOAD_ERR",
                repr(error),
            )
            traceback.print_exc()

    def run_fuzz_session(self, total_runs=30):
        if not self.endpoints:
            raise RuntimeError(
                "No endpoints loaded. "
                "Call discover_via_spec() first."
            )

        # allow dynamic scaling: if there are interesting seeds, intensify
        if self.interesting_seeds:
            total_runs = int(total_runs * (1 + min(3, len(self.interesting_seeds) / 50)))

        self.total_requests = total_runs

        print(
            f"[*] Dispatching execution matrix across "
            f"{self.max_workers} threads... (runs={total_runs})",
            flush=True,
        )

        failures = []

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            futures = [
                executor.submit(
                    self.fuzz_worker,
                    random.choice(self.endpoints),
                )
                for _ in range(total_runs)
            ]

            for future in as_completed(futures):
                try:
                    # Ensures unexpected worker exceptions are visible.
                    future.result()
                except Exception as error:
                    failures.append(error)
                    print(
                        f"[-] Worker failed: {error}",
                        flush=True,
                    )
                    traceback.print_exc()

        if failures:
            raise RuntimeError(
                f"{len(failures)} worker(s) failed"
            )

    def generate_web_dashboard(self, report_name):
        report_path = Path(report_name)

        rows = []

        for finding in self.findings:
            rows.append(
                "<tr>"
                f"<td>{html.escape(finding['timestamp'])}</td>"
                f"<td><strong>{html.escape(finding['type'])}</strong></td>"
                f"<td>{html.escape(str(finding['status']))}</td>"
                f"<td>{html.escape(finding['method'] + ' ' + finding['url'])}</td>"
                f"<td><pre>{html.escape(finding['payload'])}</pre></td>"
                f"<td><pre>{html.escape(finding['evidence'])}</pre></td>"
                "</tr>"
            )

        if not rows:
            rows.append(
                "<tr><td colspan='6'>"
                "No anomalies discovered."
                "</td></tr>"
            )

        document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Fuzzer Telemetry Dashboard</title>
<style>
body {{
    font-family: system-ui, sans-serif;
    background: #0b0f19;
    color: #cbd5e1;
    margin: 0;
    padding: 32px;
}}
main {{
    max-width: 1400px;
    margin: auto;
}}
h1 {{
    color: #f8fafc;
}}
.metrics {{
    display: flex;
    gap: 16px;
    margin: 24px 0;
}}
.card {{
    background: #151d30;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 20px;
    min-width: 220px;
}}
.number {{
    color: #38bdf8;
    font-size: 32px;
    font-weight: bold;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: #151d30;
}}
th, td {{
    border: 1px solid #334155;
    padding: 12px;
    text-align: left;
    vertical-align: top;
}}
th {{
    color: #f8fafc;
    background: #0f172a;
}}
pre {{
    white-space: pre-wrap;
    word-break: break-word;
    max-width: 350px;
}}
strong {{
    color: #f87171;
}}
</style>
</head>
<body>
<main>
<h1>Boundary Telemetry Dashboard</h1>

<div class="metrics">
<div class="card">
<div>Total Requests</div>
<div class="number">{self.total_requests}</div>
</div>
<div class="card">
<div>Endpoints</div>
<div class="number">{len(self.endpoints)}</div>
</div>
<div class="card">
<div>Findings</div>
<div class="number">{len(self.findings)}</div>
</div>
</div>

<table>
<thead>
<tr>
<th>Time</th>
<th>Anomaly</th>
<th>Status</th>
<th>Request</th>
<th>Payload</th>
<th>Evidence</th>
</tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</main>
</body>
</html>
"""

        report_path.write_text(document, encoding="utf-8")
        os.makedirs("data", exist_ok=True)
        csv_file_path = os.path.join("data", "test_runs.csv")
        file_exists = os.path.exists(csv_file_path)
        
        try:
            with open(csv_file_path, mode="a", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                if not file_exists:
                    writer.writerow(["Time", "Anomaly Group", "Status", "Context Route", "Payload Trigger"])
                
                for item in self.findings:
                    writer.writerow([
                        item['timestamp'], 
                        item['type'], 
                        item['status'], 
                        f"{item['method']} {item['url']}", 
                        item['payload']
                    ])
            print(f"[+] Data telemetry sheet dynamically appended inside '{csv_file_path}'")
        except Exception as csv_err:
            print(f"[-] CSV file logging engine trace dropped: {str(csv_err)}")

        print(
            f"[+] Dashboard written to {report_path}",
            flush=True,
        )


def wait_for_server(url, timeout=10):
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1)
            response.raise_for_status()
            return
        except Exception as error:
            last_error = error
            time.sleep(0.2)

    raise RuntimeError(
        f"Target server did not become ready: {last_error}"
    )


def main():
    print(
        "[*] Starting Autonomous Boundary Fuzzing Pipeline...",
        flush=True,
    )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        MockServerHandler,
    )
    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    server_thread.start()

    fuzzer = AdvancedBehavioralFuzzer(
        base_url=BASE_URL,
        max_workers=5,
    )

    try:
        wait_for_server(f"{BASE_URL}/swagger.json")
        fuzzer.discover_via_spec(
            f"{BASE_URL}/swagger.json"
        )

        print(
            "[*] Launching dynamic fuzz loop wrapper "
            "(30 iterations)...",
            flush=True,
        )

        fuzzer.run_fuzz_session(total_runs=30)

    except Exception as error:
        print(
            f"[-] Fuzzing pipeline failed: {error}",
            flush=True,
        )
        traceback.print_exc()
        raise

    finally:
        print(
            "[*] Shutting down target server safely...",
            flush=True,
        )
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)

    fuzzer.generate_web_dashboard(REPORT_NAME)

    print(
        "[+] Pipeline complete.",
        flush=True,
    )


if __name__ == "__main__":
    main()
