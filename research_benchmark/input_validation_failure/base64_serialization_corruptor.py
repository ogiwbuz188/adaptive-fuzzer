from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64

class Base64CorruptorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/b64-decode": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"b64_encoded_data": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/b64-decode" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            b64_data = parsed_json.get("b64_encoded_data")
            try:
                if b64_data is not None:
                    # 🚨 CRASH POINT: Mutated non-b64 strings trigger uncaught binary format faults
                    base64.b64decode(str(b64_data).encode('utf-8'), validate=True)
                self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"valid"}')
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"FATAL_SERIALIZATION_FAULT: binascii.Error: Unhandled padding exception during stream decode: {str(e)}".encode())
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), Base64CorruptorService).serve_forever()
