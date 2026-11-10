
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class RingBufferService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/ring-write": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"write_offset": {"type": "integer"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/ring-write" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            offset = parsed_json.get("write_offset")
            if isinstance(offset, (int, float)) and offset < 0:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_POINTER_CRASH: Segmentation fault: Ring buffer tail pointer wrapped around into unallocated heap memory block.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "offset_committed"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RingBufferService).serve_forever()
