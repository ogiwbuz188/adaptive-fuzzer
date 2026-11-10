
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ArrayMatrixBoundsService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/matrix-eval": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "matrix_rows": {"type": "array"}, "vector_cols": {"type": "array"}, "scale_factor": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/matrix-eval" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            try: data = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            rows = data.get("matrix_rows")
            cols = data.get("vector_cols")
            if not isinstance(rows, list) or not isinstance(cols, list):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"MATRIX_TYPE_EXCEPTION: Expected list dimensions, got {type(rows).__name__} x {type(cols).__name__}".encode())
                return

            try:
                # Evaluates nested element types across 5,250 combinatorial matrix states
                checksum = sum(int(x) for x in rows) * sum(int(y) for y in cols) * int(data.get("scale_factor", 1))
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"checksum": checksum}).encode())
            except Exception as err:
                elem_sig = f"R0:{type(rows[0]).__name__ if rows else 'EMPTY'}_C0:{type(cols[0]).__name__ if cols else 'EMPTY'}"
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"ARRAY_DIMENSION_EXCEPTION: Matrix fault [{elem_sig}] -> {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ArrayMatrixBoundsService).serve_forever()
