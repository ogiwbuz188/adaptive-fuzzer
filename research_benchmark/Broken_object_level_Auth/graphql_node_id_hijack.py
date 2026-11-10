
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class GraphqlNodeHijackService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/resolve-node": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"global_node_id": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/resolve-node" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            node_id = parsed_json.get("global_node_id")
            if isinstance(node_id, (dict, list)) or node_id is None:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"INTERNAL_AUTH_LEAK: RelayNodeResolverException: Failed to decode Base64 global ID; leaked primary key table: admin_vault_records.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "node_resolved"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), GraphqlNodeHijackService).serve_forever()
      
