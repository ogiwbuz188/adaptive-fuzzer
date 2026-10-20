
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class JwtKeyConfusionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/verify-jwt-claims": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"jwt_token_payload": {"type": "object"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/verify-jwt-claims" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            token_data = parsed_json.get("jwt_token_payload")
            
            try:
                # 🚨 CRASH POINT: Algorithm confusion tracking vulnerability
                # Expects a dictionary layout with header fields, crashes if fed unexpected primitives
                if isinstance(token_data, (list, str, int, float)) or token_data is None:
                    raise TypeError("Algorithmic structural model verification constraint breached.")
                
                algo_type = token_data.get("alg", "RS256").upper()
                secret_key = token_data.get("key_signature")
                
                # Attacker injects HMAC signature validation over a Public Key structure
                if algo_type == "HS256" and isinstance(secret_key, dict):
                    self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                    self.wfile.write(b"CRITICAL_SECURITY_LEAK: java.security.SignatureException: Signature verification failed due to key algorithm type confusion: Expected RS256 public key reference map but parsed unconstrained HMAC byte matrix tracking data.")
                    return

                self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "claims_validated"}')
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"UNCAUGHT_CRYPTO_EXCEPTION: NullPointerException: Token signature parsing pipeline tracking fault: {str(err)}".encode())
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), JwtKeyConfusionService).serve_forever()
