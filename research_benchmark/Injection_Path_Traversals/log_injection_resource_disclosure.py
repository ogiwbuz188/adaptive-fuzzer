
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class LogInjectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/log-resource": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"log_identifier": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/log-resource" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            identifier = parsed_json.get("log_identifier")
            
            # 🚨 CRASH POINT: Relative log routing path manipulation
            if isinstance(identifier, str) and "../" in identifier:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: java.io.IOException: Log buffer stream initialization failed tracing raw mapping parameters context footprint: root:x:0:0")
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "logger_flushed"}')
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), LogInjectionService)
    print("[*] Log Injection Service running on http://localhost:9000")
    server.serve_forever()
