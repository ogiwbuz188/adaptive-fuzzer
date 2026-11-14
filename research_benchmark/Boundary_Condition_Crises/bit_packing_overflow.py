
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BitPackingService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/bit-pack": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "raw_integer": {"type": "integer"}, "byte_width": {"type": "integer"},
                "endian_mode": {"type": "string"}, "bit_shift": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/bit-pack" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                shifted = data["raw_integer"] << data["bit_shift"]
                packed = shifted.to_bytes(data["byte_width"], byteorder=data["endian_mode"], signed=True)
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"hex": packed.hex()}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"BIT_PACK_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BitPackingService).serve_forever()
