from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class RoleClimbingService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/role-verify": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"account_role_str": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/role-verify" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            role = parsed_json.get("account_role_str")
            if isinstance(role, str) and ("admin" in role.lower() or "true" in role.lower()):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"UNCAUGHT_SCHEMA_EXCEPTION: SecurityAccessDeniedException: Fatal object relational role tracking violation mapping access descriptor parameters: token validation state compromised.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"role_denied"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RoleClimbingService).serve_forever()
