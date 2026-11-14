
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json

class PathlibSandboxService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/resolve-sandbox": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "sub_folder": {"type": "string"}, "doc_slug": {"type": "string"}, "ext_suffix": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/resolve-sandbox" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                root = Path("/srv/sandbox").resolve()
                candidate = (root / data["sub_folder"] / (data["doc_slug"] + data["ext_suffix"])).resolve()
                rel = candidate.relative_to(root)
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"resolved": str(rel)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"SANDBOX_ESCAPE_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), PathlibSandboxService).serve_forever()
