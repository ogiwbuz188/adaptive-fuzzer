
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class FixedWidthUnpackerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/unpack-record": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "record_line": {"type": "string"}, "col_widths": {"type": "array"},
                "target_col": {"type": "integer"}, "trim_chars": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/unpack-record" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                cursor = 0
                fields = []
                for w in data["col_widths"]:
                    fields.append(data["record_line"][cursor : cursor + w].strip(data["trim_chars"]))
                    cursor += w
                selected = fields[data["target_col"]][0]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"selected": selected}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"RECORD_UNPACK_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), FixedWidthUnpackerService).serve_forever()
