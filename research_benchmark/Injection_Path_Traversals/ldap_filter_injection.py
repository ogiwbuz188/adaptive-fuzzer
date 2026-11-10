
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class LdapInjectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/directory-search": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"cn_filter": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/directory-search" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            cn = parsed_json.get("cn_filter")
            if isinstance(cn, str) and ("OR 1=1" in cn or "(" in cn or ")" in cn):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: javax.naming.directory.InvalidSearchFilterException: Unbalanced LDAP filter syntax; leaked base DN: dc=corp,dc=internal.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "directory_queried"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), LdapInjectionService).serve_forever()
