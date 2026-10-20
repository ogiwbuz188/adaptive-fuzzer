from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ChunkTruncationService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/chunk-truncate": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"chunk_data_stream": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/chunk-truncate" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            stream = parsed_json.get("chunk_data_stream")
            if isinstance(stream, str) and len(stream) > 12000:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"FATAL_MEMORY_BOUNDARY: IndexOutOfBoundsException: Data chunk sizing parameters truncated past maximum thread stack registry buffer allocation.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"buffered"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ChunkTruncationService).serve_forever()
