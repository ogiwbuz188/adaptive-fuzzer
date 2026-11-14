
from http.server import HTTPServer, BaseHTTPRequestHandler
import configparser
import json

class ConfigparserSectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/load-ini": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "section_name": {"type": "string"}, "ini_line": {"type": "string"}, "lookup_key": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/load-ini" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                cfg = configparser.ConfigParser()
                blob = f"[{data['section_name']}]\n{data['ini_line']}\n"
                cfg.read_string(blob)
                val = cfg[data["section_name"]][data["lookup_key"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"val": val}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"INI_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ConfigparserSectionService).serve_forever()
