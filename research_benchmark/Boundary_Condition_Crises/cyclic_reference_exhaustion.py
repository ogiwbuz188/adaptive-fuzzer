from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CyclicExhaustionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/cyclic-check": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"recursive_map_obj": {"type": "object"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/cyclic-check" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            obj = parsed_json.get("recursive_map_obj")
            if isinstance(obj, dict) and len(str(obj)) > 500:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"SYSTEM_STACK_OVERFLOW: StackOverflowError: Circular reference graph optimization fault discovered inside collection object serializer tracking framework.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"cleared"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CyclicExhaustionService).serve_forever()
