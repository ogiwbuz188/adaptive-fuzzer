from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os

class OsPathFileReaderService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/read-asset": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "base_dir": {"type": "string"}, "file_name": {"type": "string"}, "read_bytes": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/read-asset" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                target = os.path.join("/var/app/assets", data["base_dir"], data["file_name"])
                with open(target, "r", encoding="utf-8") as f:
                    content = f.read(data["read_bytes"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"content": content}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"PATH_TRAVERSAL_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), OsPathFileReaderService).serve_forever()
