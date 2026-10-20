from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CompositeKeyService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/composite-lookup": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"composite_user_id": {"type": "integer"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/composite-lookup" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            uid = parsed_json.get("composite_user_id")
            if isinstance(uid, (dict, list)):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"INTERNAL_DATA_LEAKAGE: java.lang.NullPointerException: Session tracking context mapping mismatch inside Object Relational Mapping (ORM) proxy layer model: {str(uid)}".encode())
                return
            if isinstance(uid, str) and ("UNION" in uid.upper() or "SELECT" in uid.upper()):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_SQLITE: DriverSQLException: Query compilation matrix failed near offset sequence validation reference index tracking marker.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"fetched"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CompositeKeyService).serve_forever()
