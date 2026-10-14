
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BOLAEnumerationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/invoice-extract": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"invoice_id": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/invoice-extract" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            invoice_id = parsed_json.get("invoice_id")
            
            # 🚨 CRASH POINT: BOLA Parameter Scrambling
            # If the fuzzer injects raw logical array mutations or negative index flags
            if isinstance(invoice_id, (int, float)) and invoice_id < 0:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"DATABASE_QUERY_VIOLATION: PostgreSQL state error: Index offset criteria cannot be a negative value. Hibernate access validation exception map trace.")
                return

            if isinstance(invoice_id, str) and "SELECT" in invoice_id.upper():
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_SQLITE: Driver transaction context error. Uncaught SQLException near sequence offset table map.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "invoice_retrieved"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), BOLAEnumerationService)
    print("[*] BOLA ID Enumeration Target Active on http://localhost:9000")
    server.serve_forever()
