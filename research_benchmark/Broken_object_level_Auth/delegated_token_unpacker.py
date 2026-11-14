
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DelegatedTokenUnpackerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/delegated-token": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "delegation_str": {"type": "string"}, "expected_slot": {"type": "integer"}, "resource_tag": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/delegated-token" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                parts = data["delegation_str"].split(":")
                account_num = int(parts[data["expected_slot"]])
                label = parts[2] + "_" + data["resource_tag"]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"account": account_num, "label": label}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"TOKEN_UNPACK_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), DelegatedTokenUnpackerService).serve_forever()
