import json
import os
import random
import string
import time
import concurrent.futures
from urllib.parse import urljoin
import requests

class AdvancedBehavioralFuzzer:
    def __init__(self, base_url, max_workers=5, auth_token=None):
        self.base_url = base_url
        self.max_workers = max_workers
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})
            
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]
        
        self.corpus = [
            "test_payload", '{"admin": true}', "' OR 1=1 --", "<script>alert(1)</script>",
            "A" * 1000, "A" * 30000, "-1", "2147483647", "null", "[]", "{}"
        ]
        self.endpoints = []
        self.findings = []
        self.total_requests = 0

    def discover_via_spec(self, json_spec_url_or_path):
        print(f"[*] Extracting routes from schema: {json_spec_url_or_path}")
        try:
            if json_spec_url_or_path.startswith("http"):
                spec = self.session.get(json_spec_url_or_path, timeout=5).json()
            else:
                with open(json_spec_url_or_path, 'r') as f:
                    spec = json.load(f)
            
            for path, methods in spec.get("paths", {}).items():
                for method, details in methods.items():
                    if method.upper() not in ["GET", "POST", "PUT", "DELETE"]:
                        continue
                    
                    param_structure = {"query": [], "body_properties": {}}
                    for param in details.get("parameters", []):
                        if param.get("in") in ["query", "formData"]:
                            param_structure["query"].append(param.get("name"))
                            
                    if "requestBody" in details:
                        content = details["requestBody"].get("content", {})
                        schema = content.get("application/json", {}).get("schema", {})
                        if "properties" in schema:
                            param_structure["body_properties"] = schema["properties"]

                    self.endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "blueprint": param_structure
                    })
            print(f"[+] Scan map locked. Tracked {len(self.endpoints)} complex routes.")
        except Exception as e:
            print(f"[-] Parsing failed ({str(e)}). Using local fallback layout.")
            self.endpoints = [{"path": "/api/v2/secure-process", "method": "POST", "blueprint": {"query": [], "body_properties": {"data_chunk": {"type": "string"}, "user_profile": {"type": "object"}, "transaction_id": {"type": "integer"}}}}]

    def _mutate(self, seed):
        strategy = random.choice(['overflow', 'type_scramble', 'nested_json', 'traversal', 'format_str'])
        if strategy == 'overflow':
            return str(seed) * 40
        elif strategy == 'type_scramble':
            return random.choice([None, True, False, -1, 999999999999, []])
        elif strategy == 'nested_json':
            return {random.choice(string.ascii_letters): {random.choice(string.ascii_letters): seed}}
        elif strategy == 'traversal':
            return "../" * 12 + "etc/passwd"
        elif strategy == 'format_str':
            return "%x%s" * 8
        return seed

    def _build_enterprise_payload(self, properties):
        payload = {}
        for key, details in properties.items():
            expected_type = details.get("type", "string")
            if random.random() < 0.30:
                payload[key] = self._mutate(random.choice(self.corpus))
            else:
                if expected_type == "object":
                    payload[key] = self._build_enterprise_payload(details.get("properties", {"nested_fallback": {}}))
                elif expected_type == "array":
                    payload[key] = [self._mutate(random.choice(self.corpus))]
                else:
                    payload[key] = self._mutate(random.choice(self.corpus))
        return payload

    def _fuzz_worker(self, target):
        url = ""
        method = target["method"]
        try:
            path = target["path"]
            blueprint = target["blueprint"]

            headers = {"User-Agent": random.choice(self.user_agents)}
            time.sleep(random.uniform(0.05, 0.25))

            url = urljoin(self.base_url, path.lstrip("/"))
            kwargs = {"timeout": 4, "headers": headers}

            if method in ["POST", "PUT"]:
                if blueprint["body_properties"]:
                    kwargs["json"] = self._build_enterprise_payload(blueprint["body_properties"])
                else:
                    kwargs["json"] = {"input": self._mutate(random.choice(self.corpus))}
                send_payload = kwargs["json"]
            else:
                if blueprint["query"]:
                    chosen_param = random.choice(blueprint["query"])
                    kwargs["params"] = {chosen_param: self._mutate(random.choice(self.corpus))}
                else:
                    kwargs["params"] = {"input": self._mutate(random.choice(self.corpus))}
                send_payload = kwargs["params"]

            start = time.time()
            res = self.session.request(method, url, **kwargs)
            self._analyze(res, time.time() - start, method, url, send_payload)

        except requests.exceptions.Timeout:
            self._log_anomaly("TIMEOUT_EXHAUSTION", 504, method, url, "TIMEOUT", "Microservice gateway limit broken.")
        except Exception as e:
            self._log_anomaly("CONNECTION_DROP_OR_DATA_FAULT", 0, method, url, "PAYLOAD_ERR", str(e))

    def _analyze(self, response, duration, method, url, send_payload):
        anomalies = []
        body = response.text.lower()

        if response.status_code == 500:
            anomalies.append("500_INTERNAL_SERVER_ERROR")
        elif response.status_code == 413:
            anomalies.append("413_PAYLOAD_TOO_LARGE")

        if duration > 1.5:
            anomalies.append("HIGH_LATENCY_DELAY")

        indicators = ["stack trace", "exception", "nullpointer", "overflow", "fatal", "segmentation fault"]
        for ind in indicators:
            if ind in body:
                anomalies.append(f"VERBOSE_LEAK_{ind.upper()}")

        for anomaly in anomalies:
            self._log_anomaly(anomaly, response.status_code, method, url, send_payload, response.text[:250])

    def _log_anomaly(self, classification, status, method, url, payload, snippet):
        self.findings.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "type": classification,
            "status": status,
            "method": method,
            "url": url,
            "payload": str(payload)[:100],
            "evidence": snippet.replace("<", "&lt;").replace(">", "&gt;")
        })

    def run_fuzz_session(self, total_runs=40):
        print(f"[*] Dispatching execution matrix across {self.max_workers} threads...")
        self.total_requests = total_runs
        if not self.endpoints:
            print("[-] No endpoints loaded. Call discover_via_spec() first or using local fallback layout.")
            self.endpoints = [{"path": "/api/v2/secure-process", "method": "POST", "blueprint": {"query": [], "body_properties": {"data_chunk": {"type": "string"}}}}]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._fuzz_worker, random.choice(self.endpoints)) for _ in range(total_runs)]
            concurrent.futures.wait(futures)


class DashboardManager:
    def __init__(self, output_dir="/var/reports", findings=None, endpoints=None, total_requests=0):
        self.output_dir = output_dir
        self.findings = findings or []
        self.endpoints = endpoints or []
        self.total_requests = total_requests

    def generate_web_dashboard(self, report_name="fuzz_dashboard.html"):
        full_path = f"{self.output_dir}/{report_name}"
        print(f"Creating dashboard at: {full_path}")

        os.makedirs(self.output_dir, exist_ok=True)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Fuzzer Telemetry Dashboard</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #0b0f19; color: #94a3b8; padding: 2rem; margin: 0; }}
        .wrapper {{ max-width: 1300px; margin: 0 auto; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #233554; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        h1 {{ color: #f8fafc; margin: 0; font-size: 1.6rem; }}
        .metrics {{ display: flex; gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{ background: #151d30; border: 1px solid #233554; border-radius: 8px; padding: 1.2rem; flex: 1; }}
        .num {{ font-size: 2rem; font-weight: bold; color: #38bdf8; }}
        table {{ width: 100%; border-collapse: collapse; background: #151d30; border: 1px solid #233554; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid #233554; font-size: 0.9rem; }}
        th {{ background: #0f172a; color: #f8fafc; }}
        tr:hover td {{ background: #1c273e; }}
        .code {{ font-family: monospace; background: #0b0f19; padding: 0.5rem; border-radius: 4px; border: 1px solid #233554; color: #cbd5e1; word-break: break-all; max-width: 350px; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <div>
                <h1>🛡️ Boundary Telemetry Dashboard</h1>
                <p style="margin: 0.3rem 0 0 0; font-size:0.85rem;">Autonomous edge-case validation report logs</p>
            </div>
        </header>

        <div class="metrics">
            <div class="card"><h3>Total Scheduled Executions</h3><div class="num">{self.total_requests}</div></div>
            <div class="card"><h3>Target Routes Extracted</h3><div class="num">{len(self.endpoints)}</div></div>
        </div>

        <h2>Behavioral Alert Streams</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Anomaly Group</th>
                    <th>Status</th>
                    <th>Request Context</th>
                    <th>Payload Trigger</th>
                    <th>Captured Evidence Window</th>
                </tr>
            </thead>
            <tbody>
        """

        if not self.findings:
            html_template += """<tr><td colspan="6" style="text-align: center; color: #4ade80; padding: 4rem;">No boundary errors or execution crashes discovered across endpoint schemas. Target microservice validated within limits.</td></tr>"""
        else:
            for item in self.findings:
                html_template += f"""
                <tr>
                    <td>{item['timestamp']}</td>
                    <td><strong style="color: #f87171;">{item['type']}</strong></td>
                    <td><code>{item['status']}</code></td>
                    <td><span style="font-size:0.85rem; color:#e2e8f0;">{item['method']} {item['url']}</span></td>
                    <td><div class="code">{item['payload']}</div></td>
                    <td><div class="code" style="color: #fca5a5;">{item['evidence']}</div></td>
                </tr>"""

        html_template += """
            </tbody>
        </table>
    </div>
</body>
</html>"""

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"[+] UI generation complete. Review findings inside '{full_path}'.")
        return full_path


if __name__ == "__main__":
    TARGET_HOST = "http://localhost:9000"
    SPEC_URL = "http://localhost:9000/swagger.json"

    fuzzer = AdvancedBehavioralFuzzer(base_url=TARGET_HOST, max_workers=5)
    fuzzer.discover_via_spec(SPEC_URL)
    fuzzer.run_fuzz_session(total_runs=40)

    dashboard = DashboardManager(
        output_dir="/var/reports",
        findings=fuzzer.findings,
        endpoints=fuzzer.endpoints,
        total_requests=fuzzer.total_requests,
    )
    dashboard.generate_web_dashboard(report_name="fuzz_dashboard.html")
