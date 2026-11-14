
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DirectLedgerLookupService(BaseHTTPRequestHandler):
    LEDGER = [{"id": 100, "owner": "alice", "bal": 500}, {"id": 101, "owner": "bob", "bal": 900}]

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/ledger-index": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "record_slot": {"type": "integer"}, "requester_id": {"type": "integer"}, "field_key": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/ledger-index" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                record = self.LEDGER[data["record_slot"]]
                if record["id"] != data["requester_id"] + 100:
                    raise PermissionError(f"Owner mismatch for {record['owner']}")
                val = record[data["field_key"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"value": val}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"BOLA_LEDGER_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), DirectLedgerLookupService).serve_forever()
