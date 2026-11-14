
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SessionOwnerComparatorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/compare-owner": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "session_uid": {"type": "integer"}, "target_uid": {"type": "integer"}, "audit_note": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/compare-owner" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                diff = data["session_uid"] - data["target_uid"]
                if diff < 0 or len(data["audit_note"]) == 0:
                    raise PermissionError(f"Cross-tenant delta violation: {diff}")
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"delta": diff}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"OWNER_DELTA_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SessionOwnerComparatorService).serve_forever()
