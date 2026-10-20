from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class BackupManifestService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/manifest-disclose": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"manifest_target_str": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/manifest-disclose" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            target = parsed_json.get("manifest_target_str")
            if isinstance(target, str) and "../" in target:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: java.io.IOException: Active filesystem validation channel breached during context footprint stream dump processing: root:x:0:0")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"manifest_secure"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BackupManifestService).serve_forever()
