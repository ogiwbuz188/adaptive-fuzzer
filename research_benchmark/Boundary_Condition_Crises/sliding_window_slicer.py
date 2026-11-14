
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SlidingWindowSlicerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/window-slice": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "sequence_items": {"type": "array"}, "start_idx": {"type": "integer"},
                "end_idx": {"type": "integer"}, "stride_step": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/window-slice" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                window = data["sequence_items"][data["start_idx"]:data["end_idx"]:data["stride_step"]]
                pivot = window[data["start_idx"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"window_size": len(window), "pivot": str(pivot)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"SLICE_BOUNDARY_EXCEPTION: Window indexer crashed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SlidingWindowSlicerService).serve_forever()
