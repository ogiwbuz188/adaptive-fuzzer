
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HistogramBucketService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/bucket-quantize": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "sample_values": {"type": "array"}, "bucket_count": {"type": "integer"},
                "min_bound": {"type": "integer"}, "max_bound": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/bucket-quantize" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                span = (data["max_bound"] - data["min_bound"]) / data["bucket_count"]
                buckets = [0] * data["bucket_count"]
                for val in data["sample_values"]:
                    idx = int((val - data["min_bound"]) / span)
                    buckets[idx] += 1
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"buckets": buckets}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"HISTOGRAM_BOUNDARY_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), HistogramBucketService).serve_forever()
