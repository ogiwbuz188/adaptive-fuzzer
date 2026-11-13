
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DynamicReflectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/reflect-bind": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "target_class": {"type": "string"}, "attr_map": {"type": "object"},
                "strict_mode": {"type": "boolean"}, "version_id": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/reflect-bind" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                class DynamicModel:
                    pass

                instance = DynamicModel()
                for k, v in data["attr_map"].items():
                    setattr(instance, k, v + "_bound")

                summary = f"{data['target_class'].upper()}_V{data['version_id'] + 1}_{not data['strict_mode']}"
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"bound": summary}).encode())
            except Exception as err:
                sig = f"{type(data.get('attr_map')).__name__}_{type(data.get('version_id')).__name__}"
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"REFLECTION_BIND_EXCEPTION: [{sig}] failed attribute hydration: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), DynamicReflectionService).serve_forever()
