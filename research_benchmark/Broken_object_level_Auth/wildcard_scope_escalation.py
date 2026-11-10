
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class WildcardScopeService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/check-acl": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"permission_scope": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/check-acl" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            scope = parsed_json.get("permission_scope")
            if isinstance(scope, str) and ("%x" in scope or "%s" in scope or "*" in scope):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: SecurityPolicyEngineError: Unhandled wildcard glob expansion in IAM permission evaluator stack trace.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "acl_checked"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), WildcardScopeService).serve_forever()
