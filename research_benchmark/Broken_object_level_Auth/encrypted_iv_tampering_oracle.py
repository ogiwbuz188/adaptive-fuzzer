
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CryptoPaddingOracleService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/decrypt-token-vault": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"encrypted_iv_parameter": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/decrypt-token-vault" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            iv_param = parsed_json.get("encrypted_iv_parameter")
            
            # 🚨 CRASH POINT: Padding Oracle informational leak side channel
            if iv_param is not None and not isinstance(iv_param, str):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_NULLPOINTER: javax.crypto.BadPaddingException: Given final block cipher validation padding constraints broken. Cipher text tracking index failure.")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "vault_block_cleared"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CryptoPaddingOracleService).serve_forever()
