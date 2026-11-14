
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import shlex

class ShlexCommandSplitterService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/parse-cli": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "cli_flags": {"type": "string"}, "target_arg": {"type": "string"}, "arg_index": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/parse-cli" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                tokens = shlex.split(data["cli_flags"] + " " + data["target_arg"])
                chosen = tokens[data["arg_index"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"token": chosen}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"CMD_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ShlexCommandSplitterService).serve_forever()
