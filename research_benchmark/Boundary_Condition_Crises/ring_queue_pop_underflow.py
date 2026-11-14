
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque
import json

class RingQueueUnderflowService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/queue-drain": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "initial_items": {"type": "array"}, "max_capacity": {"type": "integer"},
                "consume_count": {"type": "integer"}, "delimiter_char": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/queue-drain" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                q = deque(data["initial_items"], maxlen=data["max_capacity"])
                drained = [str(q.popleft()) for _ in range(data["consume_count"])]
                output = data["delimiter_char"].join(drained)
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"drained": output}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"QUEUE_UNDERFLOW_EXCEPTION: Ring queue failed boundary check {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RingQueueUnderflowService).serve_forever()
