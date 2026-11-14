
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid

class UuidNamespaceService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/uuid-owner": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "resource_uuid": {"type": "string"}, "tenant_prefix": {"type": "string"}, "version_num": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/uuid-owner" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                parsed = uuid.UUID(data["resource_uuid"], version=data["version_num"])
                prefix_match = str(parsed).startswith(data["tenant_prefix"].lower())
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"owned": prefix_match}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"UUID_BOLA_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), UuidNamespaceService).serve_forever()
