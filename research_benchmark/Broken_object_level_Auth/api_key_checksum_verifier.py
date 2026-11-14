
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ApiKeyChecksumVerifierService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/verify-apikey": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "api_key_hex": {"type": "string"}, "account_offset": {"type": "integer"}, "key_tag": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/verify-apikey" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                raw_num = int(data["api_key_hex"][:8], 16)
                owner_id = raw_num ^ data["account_offset"]
                tag = data["key_tag"].split("-")[1]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"owner_id": owner_id, "tag": tag}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"APIKEY_BOLA_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ApiKeyChecksumVerifierService).serve_forever()
