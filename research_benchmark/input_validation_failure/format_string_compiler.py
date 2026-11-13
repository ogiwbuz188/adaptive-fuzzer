
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class FormatStringCompilerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/compile-template": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "header_fmt": {"type": "string"}, "body_fmt": {"type": "string"},
                "footer_fmt": {"type": "string"}, "arg_tuple": {"type": "array"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/compile-template" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                h = data["header_fmt"] % tuple(data["arg_tuple"])
                b = data["body_fmt"].format(*data["arg_tuple"])
                f = data["footer_fmt"] % len(data["arg_tuple"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"rendered": f"{h}|{b}|{f}"}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"FORMAT_COMPILER_EXCEPTION: Template interpolation crashed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), FormatStringCompilerService).serve_forever()
