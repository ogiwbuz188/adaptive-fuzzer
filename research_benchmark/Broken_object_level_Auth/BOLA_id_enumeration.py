
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BOLAEnumerationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/user-lookup": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"target_account_id": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/user-lookup" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            account_id = parsed_json.get("target_account_id")
            
            if isinstance(account_id, str) and any(sqli in account_id.upper() for sqli in ["UNION", "SELECT", "' OR"]):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"SQLITE_EXECUTION_FATAL_ERROR: Unhandled database engine exception: SQLite3Exception: columns parsing validation offset trace failed near index token mapping.")
                return

            if isinstance(account_id, (dict, list)):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"INTERNAL DATA LEAKAGE: java.lang.NullPointerException: Object relational validation filter tracking model broken for structural configuration primitive: {str(account_id)}".encode())
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "profile_verified"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), BOLAEnumerationService)
    print("[*] Broken Object Authorization (BOLA) Target Active on http://localhost:9000")
    server.serve_forever()
