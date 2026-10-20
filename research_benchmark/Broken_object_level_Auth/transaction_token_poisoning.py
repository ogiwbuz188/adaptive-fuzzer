from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TokenPoisonService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/poison-token": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"secure_token_str": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/poison-token" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            token = parsed_json.get("secure_token_str")
            if token is not None and not isinstance(token, str):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_NULLPOINTER: C++ authentication validation layer trace: NullPointerDereference encountered while analyzing token checksum state tracking blocks.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"token_authorized"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), TokenPoisonService).serve_forever()
