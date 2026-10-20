# ==============================================================================
# Copyright (c) 2026 Your Name
# Licensed under the MIT License.
# Research Benchmark: 02_Boundary_Condition_Crises - Advanced Scenario A
# ==============================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BinaryBufferBoundaryService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/read-binary-frame": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"hex_stream_buffer": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/read-binary-frame" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            hex_stream = parsed_json.get("hex_stream_buffer")
            
            # 🚨 CRASH POINT: Low level out-of-bounds byte tracking allocation fault
            if isinstance(hex_stream, str) and len(hex_stream) > 4000:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"FATAL_MEMORY_BOUNDARY: IndexOutOfBoundsException: Calculated structural byte-frame size tracking constraints shattered at index registry allocation window (0x7FFF). Segmentation fault tracing dump initialized.")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "binary_frame_indexed"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BinaryBufferBoundaryService).serve_forever()
