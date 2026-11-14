
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import math

class HarmonicSeriesService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/harmonic-converge": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "term_count": {"type": "integer"}, "start_denominator": {"type": "integer"},
                "log_base": {"type": "integer"}, "scale_factor": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/harmonic-converge" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                total = sum(1.0 / (data["start_denominator"] + i) for i in range(data["term_count"]))
                scaled = math.log(total * data["scale_factor"], data["log_base"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"converged": scaled}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"MATH_DOMAIN_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), HarmonicSeriesService).serve_forever()
