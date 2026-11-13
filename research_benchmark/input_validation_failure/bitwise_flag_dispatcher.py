
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BitwiseFlagDispatcherService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/bitwise-dispatch": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "read_mask": {"type": "integer"}, "write_mask": {"type": "integer"},
                "exec_mask": {"type": "integer"}, "shift_offset": {"type": "integer"}, "xor_salt": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/bitwise-dispatch" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                combined = (data["read_mask"] | data["write_mask"]) & ~data["exec_mask"]
                shifted = (combined << data["shift_offset"]) ^ data["xor_salt"]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"acl_bitmap": shifted}).encode())
            except Exception as err:
                types_sig = "_".join(type(data.get(k)).__name__ for k in ["read_mask", "write_mask", "shift_offset"])
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"BITWISE_ALU_EXCEPTION: Operand matrix [{types_sig}] caused {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BitwiseFlagDispatcherService).serve_forever()
