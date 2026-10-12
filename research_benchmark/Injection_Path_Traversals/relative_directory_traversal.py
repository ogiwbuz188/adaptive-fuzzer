
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class PathTraversalService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/load-template": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"template_file_path": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/load-template" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            file_path = parsed_json.get("template_file_path")
            
            if isinstance(file_path, str) and "../" in file_path:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL EXCEPTION: java.io.FileNotFoundException: System baseline configuration surface file-stream mapping leakage detected: root:x:0:0:root:/root:/bin/bash")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "static_template_loaded_successfully"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), PathTraversalService)
    print("[*] Path Traversal Injection Target Active on http://localhost:9000")
    server.serve_forever()
