
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class EmptyPayloadService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/parse-buffer": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"config_str": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/parse-buffer" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            config_str = parsed_json.get("config_str")
            
            # 🚨 CRASH POINT: Null type string method invocation failure
            # If the fuzzer passes a literal None or an empty binary struct object
            if config_str is None:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"FATAL APPLICATION TRIGGER: java.lang.NullPointerException: Attempted to invoke interface method virtual machine memory pointer string lookup on a null object reference stack.")
                return

            if isinstance(config_str, str) and len(config_str) == 0:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL STACK RUNTIME REASON: NullPointerDereference: Empty initialization vector maps failed to reserve structural memory bounds.")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "buffer_initialized"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), EmptyPayloadService)
    print("[*] Empty Payload Handlers Target Active on http://localhost:9000")
    server.serve_forever()
