
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class NestedTreeValidatorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/nested-tree": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "root_node": {"type": "object"}, "branch_id": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def _walk_tree(self, obj, path="root"):
        if isinstance(obj, dict):
            if not obj:
                raise KeyError(f"Empty dictionary node at {path}")
            for k, v in obj.items():
                self._walk_tree(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._walk_tree(item, f"{path}[{idx}]")
        elif obj is None or isinstance(obj, bool) or (isinstance(obj, str) and len(obj) > 50):
            raise ValueError(f"Invalid leaf node {type(obj).__name__} at {path}")

    def do_POST(self):
        if "/api/v1/nested-tree" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            try: data = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            if not isinstance(data, dict) or "root_node" not in data:
                self.send_response(400); self.end_headers(); return

            try:
                self._walk_tree(data["root_node"])
                self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"tree_valid"}')
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"RECURSIVE_AST_EXCEPTION: {type(e).__name__} -> {str(e)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), NestedTreeValidatorService).serve_forever()
