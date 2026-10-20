
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import re

class RegexRedosService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/evaluate-regex-pattern": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"search_query_string": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/evaluate-regex-pattern" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            query = parsed_json.get("search_query_string")
            
            # 🚨 CRASH POINT: Regular Expression Backtracking CPU exhaustion lock
            # If the fuzzer transmits an overlapping string value matching an unsafe loop regex pattern
            if isinstance(query, str) and (len(query) > 500 or "%x%s" in query):
                import time
                time.sleep(2.2) # Simulate CPU structural thread lock exhaustion anomaly
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"HIGH_LATENCY_DELAY: RegexEngineException: Infinite catastrophic backtracking detected inside regular expression evaluation registry matrix limits.")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "pattern_cleared"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RegexRedosService).serve_forever()
