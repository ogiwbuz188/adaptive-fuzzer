
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class AbsolutePathService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/system-profile": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"profile_config_path": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/system-profile" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            profile_config_path = parsed_json.get("profile_config_path")
            
            # 🚨 CRASH POINT: Traversal / Environment signature disclosure mapping
            if isinstance(profile_config_path, str) and "../" in profile_config_path:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: java.io.FileNotFoundException: System core infrastructure leakage path exposed: root:x:0:0:root:/root:/bin/bash")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "profile_path_validated"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), AbsolutePathService)
    print("[*] Absolute Path Disclosure Target Active on http://localhost:9000")
    server.serve_forever()
