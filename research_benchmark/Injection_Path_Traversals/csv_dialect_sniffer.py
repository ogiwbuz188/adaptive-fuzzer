
from http.server import HTTPServer, BaseHTTPRequestHandler
import csv
import io
import json

class CsvDialectSnifferService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/csv-parse": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "csv_body": {"type": "string"}, "delim_char": {"type": "string"}, "col_idx": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/csv-parse" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                reader = csv.reader(io.StringIO(data["csv_body"]), delimiter=data["delim_char"])
                rows = list(reader)
                cell = rows[data["col_idx"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"cell": cell}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"CSV_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CsvDialectSnifferService).serve_forever()
