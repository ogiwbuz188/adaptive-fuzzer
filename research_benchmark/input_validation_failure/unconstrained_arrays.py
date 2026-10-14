# ==============================================================================
# Copyright (c) 2026 Your Name
# Licensed under the MIT License.
# Research Benchmark: 01_Input_Validation_Failures
# ==============================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class UnconstrainedArrayService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/batch-items": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"item_list": {"type": "array"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/batch-items" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            item_list = parsed_json.get("item_list")
            
            try:
                # 🚨 CRASH POINT: Lack of input type constraint checks
                # If fuzzer sends a plain primitive string/int instead of a bounded array
                if len(item_list) > 100:
                    pass
                
                # If fuzzer sends an empty map or incompatible type, this operation crashes the thread
                first_element = item_list[0]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "verified", "head": first_element}).encode())
            except Exception as runtime_err:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"CRITICAL_DESERIALIZATION_FAULT: KeyError/IndexError: Object sequence evaluation failed inside collection iterator proxy: {str(runtime_err)}".encode())
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), UnconstrainedArrayService)
    print("[*] Unconstrained Arrays Target Active on http://localhost:9000")
    server.serve_forever()

