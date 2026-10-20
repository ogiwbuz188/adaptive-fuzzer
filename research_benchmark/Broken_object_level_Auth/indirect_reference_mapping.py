from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class IndirectRefService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/reference-map": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"reference_index_id": {"type": "integer"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/reference-map" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            ref = parsed_json.get("reference_index_id")
            if isinstance(ref, (int, float)) and ref < 0:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"DATABASE_QUERY_VIOLATION: PostgreSQL state error: Index offset criteria validation mapping matrix bounds collapsed. Indirect sequence reference reference missing.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"mapped"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), IndirectRefService).serve_forever()
