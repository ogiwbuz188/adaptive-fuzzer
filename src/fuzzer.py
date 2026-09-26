import html
import json
import random
import string
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin

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

        self.corpus = [
            "test_payload",
            '{"admin": true}',
            "' OR 1=1 --",
            "<script>alert(1)</script>",
            "A" * 1000,
            "A" * 30000,
            "-1",
            "2147483647",
            "null",
            "[]",
            "{}",
        ]

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

    def mutate(self, seed):
        strategy = random.choice(
            [
                "overflow",
                "type_scramble",
                "nested_json",
                "traversal",
                "format_string",
            ]
        )

        if strategy == "overflow":
            return str(seed) * 40

        if strategy == "type_scramble":
            return random.choice(
                [None, True, False, -1, 999999999999, []]
            )

        if strategy == "nested_json":
            return {
                random.choice(string.ascii_letters): {
                    random.choice(string.ascii_letters): seed
                }
            }

        if strategy == "traversal":
            return "../" * 12 + "etc/passwd"

        if strategy == "format_string":
            return "%x%s" * 8

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

        print(
            f"[!] {classification}: {method} {url} "
            f"(status={status})",
            flush=True,
        )

    def analyze(self, response, duration, method, url, payload):
        anomalies = []
        body = response.text.lower()

        if response.status_code == 500:
            anomalies.append("500_INTERNAL_SERVER_ERROR")
        elif response.status_code == 413:
            anomalies.append("413_PAYLOAD_TOO_LARGE")

        if duration > 1.5:
            anomalies.append("HIGH_LATENCY_DELAY")

        indicators = [
            "stack trace",
            "exception",
            "nullpointer",
            "overflow",
            "fatal",
            "segmentation fault",
        ]

        for indicator in indicators:
            if indicator in body:
                anomalies.append(
                    f"VERBOSE_LEAK_{indicator.upper()}"
                )

        for anomaly in anomalies:
            self.log_anomaly(
                anomaly,
                response.status_code,
                method,
                url,
                payload,
                response.text,
            )

    def fuzz_worker(self, target):
        method = target["method"]
        path = target["path"]
        blueprint = target["blueprint"]
        url = urljoin(self.base_url + "/", path.lstrip("/"))

        try:
            time.sleep(random.uniform(0.05, 0.25))

            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "application/json",
            }

            request_kwargs = {
                "timeout": 4,
                "headers": headers,
            }

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
            response = requests.request(
                method,
                url,
                **request_kwargs,
            )
            duration = time.time() - start

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

        self.total_requests = total_runs

        print(
            f"[*] Dispatching execution matrix across "
            f"{self.max_workers} threads...",
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
