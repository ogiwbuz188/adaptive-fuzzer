
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BatchDocumentExporterService(BaseHTTPRequestHandler):
    DOCS = {1: "doc_alpha", 2: "doc_beta", 3: "doc_gamma"}

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/batch-export": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "doc_ids": {"type": "array"}, "owner_tag": {"type": "string"}, "format_ext": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/batch-export" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                exported = [self.DOCS[i] + "_" + data["owner_tag"] + "." + data["format_ext"] for i in data["doc_ids"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"files": exported}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"BATCH_BOLA_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BatchDocumentExporterService).serve_forever()
