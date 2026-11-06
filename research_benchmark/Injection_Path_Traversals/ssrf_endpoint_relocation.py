
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SsrfEndpointRelocationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/relocate-resource": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"remote_forward_url": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/relocate-resource" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            forward_url = parsed_json.get("remote_forward_url")
            
            if isinstance(forward_url, str) and ("../" in forward_url or "127.0.0.1" in forward_url):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_SYSTEM_LEAK: java.io.FileNotFoundException: System endpoint relocation loop blocked. Infrastructure routing logs exposed: root:x:0:0:root:/root:/bin/bash")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "relocation_completed"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SsrfEndpointRelocationService).serve_forever()
