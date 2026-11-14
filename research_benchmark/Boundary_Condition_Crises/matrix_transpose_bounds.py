
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MatrixTransposeService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/matrix-transpose": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "grid_matrix": {"type": "array"}, "row_index": {"type": "integer"},
                "col_index": {"type": "integer"}, "multiplier": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/matrix-transpose" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                transposed = [list(col) for col in zip(*data["grid_matrix"])]
                cell_val = transposed[data["row_index"]][data["col_index"]] * data["multiplier"]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"cell": cell_val}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"MATRIX_BOUNDS_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), MatrixTransposeService).serve_forever()
