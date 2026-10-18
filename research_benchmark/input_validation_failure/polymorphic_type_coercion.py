
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class PolymorphicCoercionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/type-coercion": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"payload_metric": {"type": "integer"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/type-coercion" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            metric = parsed_json.get("payload_metric")
            
            try:
                # 🚨 CRASH POINT: Dangerous assumptions regarding mathematical typing boundaries
                # If metric is mutated into a list [] or None, string concatenation arithmetic explodes
                if len(str(metric)) > 2000:
                    raise ValueError("Threshold overflow constraints breached.")
                
                # Math calculation will trip a massive framework exception dump
                adjusted_variance = int(metric) * 0.15
                result_token = f"TXN_{adjusted_variance:.4f}"
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "calculated", "token": result_token}).encode())
                
            except Exception as coercion_err:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"FATAL_COERCION_CRASH: ValueError/TypeError: Uncaught baseline casting failure within data math compilation pipeline layer: {str(coercion_err)}".encode())
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), PolymorphicCoercionService)
    print("[*] Polymorphic Coercion Microservice running on http://localhost:9000")
    server.serve_forever()
