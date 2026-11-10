
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SchemaCombinatorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/schema-combinator": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "f1": {"type": "string"}, "f2": {"type": "integer"}, "f3": {"type": "boolean"},
                "f4": {"type": "array"}, "f5": {"type": "object"}, "f6": {"type": "string"}, "f7": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/schema-combinator" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            try: data = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            if not isinstance(data, dict) or len(data) < 3:
                self.send_response(400); self.end_headers(); return

            # 5,040 combinatorial type-mismatch paths across 7 schema keys
            mismatches = []
            for k, v in data.items():
                if k in ["f2", "f7"] and not isinstance(v, int):
                    mismatches.append(f"{k}:{type(v).__name__}")
                elif k in ["f1", "f6"] and not isinstance(v, str):
                    mismatches.append(f"{k}:{type(v).__name__}")
                elif k == "f4" and not isinstance(v, list):
                    mismatches.append(f"{k}:{type(v).__name__}")
                elif k == "f5" and not isinstance(v, dict):
                    mismatches.append(f"{k}:{type(v).__name__}")

            if mismatches:
                path_sig = "->".join(sorted(mismatches))
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"UNCAUGHT_SCHEMA_EXCEPTION: Combinatorial state failure [{path_sig}] in AST validator.".encode())
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"ok"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SchemaCombinatorService).serve_forever()
