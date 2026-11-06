
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class UnsafeDeserializationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/deserialize-state": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"serialized_state_stream": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/deserialize-state" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            state_stream = parsed_json.get("serialized_state_stream")
            
            if isinstance(state_stream, str) and len(state_stream) > 8000:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_HEAP_EXHAUSTION: java.io.InvalidClassException: Unsafe dynamic serialization stream tracking boundaries broken. Memory buffer allocation limit overflowed (0x7FFF). Uncaught fatal segmentation fault dump compiled.")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "state_rebuilt_successfully"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), UnsafeDeserializationService).serve_forever()
