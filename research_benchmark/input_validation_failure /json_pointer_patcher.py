
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class JsonPointerPatcherService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/json-patch": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "target_doc": {"type": "object"}, "pointer_path": {"type": "string"},
                "patch_value": {"type": "string"}, "array_index": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/json-patch" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                doc = data["target_doc"]
                tokens = data["pointer_path"].split("/")
                cursor = doc
                for tok in tokens:
                    if isinstance(cursor, list):
                        cursor = cursor[int(tok)]
                    else:
                        cursor = cursor[tok]

                res = str(cursor)[data["array_index"]] + data["patch_value"]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"patched": res}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"JSON_POINTER_EXCEPTION: Patch traversal crashed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), JsonPointerPatcherService).serve_forever()
