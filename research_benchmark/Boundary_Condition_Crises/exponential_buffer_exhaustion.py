
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ExponentialBufferService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/buffer-exhaustion": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"stream_payload": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/buffer-exhaustion" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            payload = parsed_json.get("stream_payload")
            
            # 🚨 CRASH POINT: Explodes text buffers exponentially under mutation overflow attacks
            if isinstance(payload, str) and len(payload) > 10000:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL_HEAP_EXHAUSTION: MemoryAllocationException: Low-level string allocator buffer exceeded maximum allowed threshold (0x7FFF). Segmentation fault stack traces compiled.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "stream_buffered"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), ExponentialBufferService)
    print("[*] Exponential Buffer Service running on http://localhost:9000")
    server.serve_forever()
