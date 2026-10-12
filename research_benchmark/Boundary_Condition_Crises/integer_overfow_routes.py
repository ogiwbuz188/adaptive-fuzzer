
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class IntegerOverflowService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/allocate-buffer": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"buffer_size": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/allocate-buffer" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            size = parsed_json.get("buffer_size")
            
            if isinstance(size, (int, float)) and size > 2147483647:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"FATAL STRUCTURAL CRITICAL FAILURE: OverflowException: 32-bit signed integer boundary constraints shattered at register offset 0xFF. Process allocation segmentation fault dump initialized.")
                return
            
            if isinstance(size, str) and len(size) > 5000:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL STACK EXHAUSTION: NullPointerDereference array size boundary limits overflowed inside low-level C memory blocks serialization engine trace.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "allocation_safe"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), IntegerOverflowService)
    print("[*] Integer Overflow Boundary Target Active on http://localhost:9000")
    server.serve_forever()
