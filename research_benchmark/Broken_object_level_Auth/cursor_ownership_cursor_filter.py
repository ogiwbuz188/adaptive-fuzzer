
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CursorOwnershipFilterService(BaseHTTPRequestHandler):
    RECORDS = [{"uid": 1, "secret": "S1"}, {"uid": 2, "secret": "S2"}]

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/filter-records": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "allowed_uids": {"type": "array"}, "format_mask": {"type": "string"}, "limit_num": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/filter-records" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                uid_set = set(data["allowed_uids"])
                matched = [data["format_mask"].format(r["secret"]) for r in self.RECORDS if r["uid"] in uid_set]
                sliced = matched[:data["limit_num"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"records": sliced}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"OWNERSHIP_FILTER_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CursorOwnershipFilterService).serve_forever()
