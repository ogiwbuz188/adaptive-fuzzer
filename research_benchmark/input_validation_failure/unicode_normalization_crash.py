from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class UnicodeCrashService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/unicode-normalize": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"unicode_input_text": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/unicode-normalize" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            text = parsed_json.get("unicode_input_text")
            # 🚨 CRASH POINT: Handling specific null structures inside complex string metrics
            if isinstance(text, str) and ("\x00" in text or len(text.encode('utf-8')) > 3000):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_SYSTEM_LEAK: Uncaught UnicodeDecodeError: Wide-character mapping registry trace failure inside codec parsing engine window.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"normalized"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), UnicodeCrashService).serve_forever()
