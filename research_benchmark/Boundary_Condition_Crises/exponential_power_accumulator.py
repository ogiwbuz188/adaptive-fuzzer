
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ExponentialPowerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/compute-series": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "base_val": {"type": "integer"}, "exponent_val": {"type": "integer"},
                "divisor_val": {"type": "integer"}, "repeat_tag": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/compute-series" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                power_res = float(data["base_val"] ** min(data["exponent_val"], 10000))
                ratio = power_res / data["divisor_val"]
                expanded = data["repeat_tag"] * data["base_val"]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"ratio": ratio, "len": len(expanded)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"NUMERIC_BOUNDARY_EXCEPTION: Series accumulator failed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ExponentialPowerService).serve_forever()
