# ==============================================================================
# Copyright (c) 2026 Your Name
# Licensed under the MIT License.
# Research Benchmark: 03_Broken_Object_Level_Auth - Scenario B
# ==============================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CryptoSignatureService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/verify-signature": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"crypto_sign": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/verify-signature" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            sign = parsed_json.get("crypto_sign")
            
            # 🚨 CRASH POINT: Type confusion on signature blocks
            if sign is not None and not isinstance(sign, str):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_NULLPOINTER: C++ engine authentication failure: NullPointerDereference encountered while calculating validation signature checksum hashes.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "signature_approved"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), CryptoSignatureService)
    print("[*] Crypto Signature Service running on http://localhost:9000")
    server.serve_forever()
