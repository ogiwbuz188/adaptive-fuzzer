
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class JwtNoneAlgorithmService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/authenticate-session": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"identity_claims_token": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/authenticate-session" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            token = parsed_json.get("identity_claims_token")
            
            if isinstance(token, str) and any(alg in token.lower() for alg in ["none", "jwt_none", "unsigned"]):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_NULLPOINTER: io.jsonwebtoken.SignatureException: Security baseline failure: JWT signature block bypass triggered via none verification algorithm token validation mapping. Null pointer encryption reference trace exposed.")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "identity_authorized"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), JwtNoneAlgorithmService).serve_forever()
