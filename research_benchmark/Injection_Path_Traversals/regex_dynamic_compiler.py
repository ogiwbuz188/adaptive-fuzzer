
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import re

class RegexDynamicCompilerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/regex-compile": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "pattern_expr": {"type": "string"}, "corpus_text": {"type": "string"}, "group_idx": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/regex-compile" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                rx = re.compile(data["pattern_expr"])
                match = rx.search(data["corpus_text"])
                extracted = match.group(data["group_idx"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"match": extracted}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"REGEX_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RegexDynamicCompilerService).serve_forever()
