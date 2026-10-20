from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ArchiveTraversalService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/archive-extract": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"archive_path_str": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/archive-extract" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            path = parsed_json.get("archive_path_str")
            if isinstance(path, str) and "../" in path:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_SYSTEM_LEAK: java.io.FileNotFoundException: System core tracking configuration framework logs exposed to user interface components: root:x:0:0:root")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"extracted"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ArchiveTraversalService).serve_forever()
