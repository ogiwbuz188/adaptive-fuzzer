from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import math

class FloatLockService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/float-precision": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"precision_scale_val": {"type": "number"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/float-precision" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            val = parsed_json.get("precision_scale_val")
            if isinstance(val, (int, float)) and (math.isnan(val) or math.isinf(val) or val == -1):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_MATH_ERROR: FloatingPointException: Infinite loop sequence generated during numeric allocation compilation matrix calculations.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"safe"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), FloatLockService).serve_forever()
