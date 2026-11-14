
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class PaginationCursorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/paginate-cursor": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "page_num": {"type": "integer"}, "page_size": {"type": "integer"},
                "cursor_salt": {"type": "string"}, "max_records": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/paginate-cursor" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                ledger = list(range(data["max_records"]))
                total_pages = len(ledger) // data["page_size"]
                offset = (data["page_num"] - 1) * data["page_size"]
                page_slice = ledger[offset : offset + data["page_size"]]
                first_item = page_slice[0] + len(data["cursor_salt"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"pages": total_pages, "head": first_item}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"CURSOR_BOUNDARY_EXCEPTION: Pagination ledger crashed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), PaginationCursorService).serve_forever()
