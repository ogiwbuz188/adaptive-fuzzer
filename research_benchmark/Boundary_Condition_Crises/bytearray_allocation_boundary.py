
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import struct

class BytearrayAllocationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/alloc-frame": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "frame_bytes": {"type": "integer"}, "short_header": {"type": "integer"},
                "fill_seed": {"type": "string"}, "padding_multiplier": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/alloc-frame" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                buf = bytearray(data["frame_bytes"] * data["padding_multiplier"])
                packed = struct.pack(">h", data["short_header"])
                seed_bytes = data["fill_seed"].encode("ascii")
                buf[0:len(packed)] = packed
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"allocated": len(buf), "seed_len": len(seed_bytes)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"BUFFER_ALLOCATION_EXCEPTION: Binary frame boundary failed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BytearrayAllocationService).serve_forever()
