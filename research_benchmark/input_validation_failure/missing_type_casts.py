
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MissingTypeCastService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/validate-cast": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"age_metric": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/validate-cast" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception as parse_err:
                self.send_response(400)
                self.end_headers()
                return

            age_metric = parsed_json.get("age_metric")
            
            try:
                if age_metric < 0:
                    pass
                calculated_days = age_metric * 365
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "processed", "days": calculated_days}).encode())
            except TypeError as type_err:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"UNCAUGHT_RUNTIME_EXCEPTION: TypeError: '<' not supported between instances of '{type(age_metric).__name__}' and 'int' inside math compiler stack registry trace: {str(type_err)}".encode())
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), MissingTypeCastService)
    print("[*] Missing Type Casts Vulnerable Server Target Active on http://localhost:9000")
    server.serve_forever()
