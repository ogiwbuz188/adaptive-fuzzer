
from http.server import HTTPServer, BaseHTTPRequestHandler
import importlib
import json

class ImportlibModuleResolverService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/resolve-module": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "pkg_prefix": {"type": "string"}, "mod_name": {"type": "string"}, "attr_name": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/resolve-module" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                mod_path = data["pkg_prefix"] + "." + data["mod_name"]
                mod = importlib.import_module(mod_path)
                attr = getattr(mod, data["attr_name"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"attr": str(attr)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"MODULE_TRAVERSAL_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ImportlibModuleResolverService).serve_forever()
