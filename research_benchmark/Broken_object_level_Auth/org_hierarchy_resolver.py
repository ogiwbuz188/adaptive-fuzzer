
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class OrgHierarchyService(BaseHTTPRequestHandler):
    ORGS = {"org_1": {"dept_a": {"secret_key": "K99"}}}

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/org-node": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "org_id": {"type": "string"}, "dept_id": {"type": "string"}, "user_claims": {"type": "object"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/org-node" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                node = self.ORGS[data["org_id"]][data["dept_id"]]
                token = node["secret_key"] + "_" + data["user_claims"]["role"].upper()
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"token": token}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"ORG_AUTH_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), OrgHierarchyService).serve_forever()
