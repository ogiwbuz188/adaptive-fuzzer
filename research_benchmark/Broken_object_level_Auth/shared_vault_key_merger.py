
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SharedVaultKeyMergerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/vault-merge": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "vault_id": {"type": "integer"}, "acl_patch": {"type": "object"}, "actor_name": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/vault-merge" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                base_acl = {"vault": data["vault_id"] + 1, "owner": data["actor_name"].strip()}
                base_acl.update(data["acl_patch"])
                owner_sig = base_acl["owner"] + ":" + str(base_acl["vault"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"sig": owner_sig}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"VAULT_MERGE_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SharedVaultKeyMergerService).serve_forever()
