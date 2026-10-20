
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class NullByteInjectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/load-secure-asset-file": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"secured_asset_file_name": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/load-secure-asset-file" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            asset_name = parsed_json.get("secured_asset_file_name")
            
            # 🚨 CRASH POINT: Null byte parameter file termination poisoning injection string check
            if isinstance(asset_name, str) and "../" in asset_name:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: java.io.IOException: Null byte string terminal sequence validation collapsed. System file reference root state trace tracking log compiled: root:x:0:0")
                return

            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "secure_asset_loaded"}')
            return

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), NullByteInjectionService).serve_forever()
