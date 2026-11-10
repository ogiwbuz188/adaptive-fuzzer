
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CsvFormulaService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/export-csv-row": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"cell_content": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/export-csv-row" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            cell = parsed_json.get("cell_content")
            if isinstance(cell, str) and (cell.startswith(("=", "+", "-", "@")) or "'" in cell):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"FATAL_FORMULA_EXCEPTION: org.apache.poi.ss.formula.FormulaParseException: Unhandled DDE command evaluation in spreadsheet cell serializer stack.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "row_appended"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CsvFormulaService).serve_forever()
