
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DynamicIncludeService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/dynamic-include": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"resource_path": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/dynamic-include" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            path_val = parsed_json.get("resource_path")
            
            # 🚨 CRASH POINT: Unchecked file loading path traversal
            if isinstance(path_val, str) and "../" in path_val:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL_SYSTEM_LEAK: java.io.FileNotFoundException: Target core environment assets breached: root:x:0:0:root:/root:/bin/bash")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "include_processed"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), DynamicIncludeService)
    print("[*] Dynamic Include Service running on http://localhost:9000")
    server.serve_forever()
