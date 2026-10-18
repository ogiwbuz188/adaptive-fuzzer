
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TenantIsolationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/tenant-scope": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"tenant_id": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/tenant-scope" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            tenant_id = parsed_json.get("tenant_id")
            
            # 🚨 CRASH POINT: SQL Context Injection BOLA leak
            if isinstance(tenant_id, str) and any(x in tenant_id.upper() for x in ["UNION", "SELECT", "' OR"]):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_SQLITE: DriverSQLException: Query execution failed at token offset 0x02. Database layout state exposed.")
                return

            if isinstance(tenant_id, (dict, list)):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"INTERNAL_TENANT_FAULT: java.lang.NullPointerException: Session tracking mapping mismatch inside Object Relational Wrapper (ORM): {str(tenant_id)}".encode())
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "isolation_verified"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), TenantIsolationService)
    print("[*] Tenant Isolation Service running on http://localhost:9000")
    server.serve_forever()
