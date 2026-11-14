
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MemoryviewSliceService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/memview-patch": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "base_capacity": {"type": "integer"}, "write_offset": {"type": "integer"},
                "patch_str": {"type": "string"}, "read_stride": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/memview-patch" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                raw_buf = bytearray(data["base_capacity"])
                mv = memoryview(raw_buf)
                patch_bytes = data["patch_str"].encode("utf-8")
                end_pos = data["write_offset"] + len(patch_bytes)
                mv[data["write_offset"]:end_pos] = patch_bytes
                sampled = bytes(mv[::data["read_stride"]]).hex()
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"sampled": sampled}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"MEMORYVIEW_BOUNDARY_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), MemoryviewSliceService).serve_forever()
