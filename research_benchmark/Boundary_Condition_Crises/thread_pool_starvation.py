
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class ThreadPoolStarvationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/spawn-workers": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"batch_count": {"type": "integer"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/spawn-workers" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            count = parsed_json.get("batch_count")
            if isinstance(count, (int, float)) and count > 10000:
                time.sleep(1.8)
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"THREAD_EXHAUSTION_ERROR: java.util.concurrent.RejectedExecutionException: Worker queue capacity overflowed.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "jobs_queued"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ThreadPoolStarvationService).serve_forever()
