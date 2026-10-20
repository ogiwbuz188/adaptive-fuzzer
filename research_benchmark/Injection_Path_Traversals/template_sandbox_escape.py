
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TemplateSandboxEscapeService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/compile-sandboxed-template": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"isolated_template_path": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/compile-sandboxed-template" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            template_path = parsed_json.get("isolated_template_path")
            
            # 🚨 CRASH POINT: Template sandbox execution escape path traversal leak
            if isinstance(template_path, str) and "../" in template_path:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_SYSTEM_LEAK: java.io.FileNotFoundException: Sandboxed structural template compiler environment breached, core system parameters leaked: root:x:0:0:root:/root:/bin/bash")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "sandbox_template_rendered"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), TemplateSandboxEscapeService).serve_forever()
