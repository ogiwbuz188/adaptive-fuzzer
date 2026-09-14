```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class ComplicatedVulnerableService(BaseHTTPRequestHandler):
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
                                            "properties": {
                                                "data": {"type": "string"},
                                                "config": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/process" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            payload = data.get("data") or data.get("config")

            if isinstance(payload, str) and len(payload) > 10000:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Fatal Error: Segmentation fault. Heap allocation memory limit exhausted.")
                return

            if isinstance(payload, dict) and any(k in payload for k in string.ascii_letters):
                time.sleep(1.6) 
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "heavy_processing_complete"}')
                return

            if isinstance(payload, str) and "etc/passwd" in payload:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Internal Exception: java.io.FileNotFoundException: Access denied to local system configurations.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "accepted"}')
            return
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), ComplicatedVulnerableService)
    print("[*] Complicated Target Service Active on http://localhost:9000")
    server.serve_forever()
