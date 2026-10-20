from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ParamPollutionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/shadow-check": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"shadow_config_obj": {"type": "object"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/shadow-check" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            config = parsed_json.get("shadow_config_obj")
            try:
                # 🚨 CRASH POINT: Assuming keys exist inside nested configuration maps
                if isinstance(config, list) or config is None:
                    raise KeyError("Object parameter configuration tracking map missing reference.")
                result = config.get("debug_level", "INFO").upper()
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"status":"active","level":result}).encode())
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"UNCAUGHT_SCHEMA_EXCEPTION: KeyError: Configuration key map shadowing failure tracing parameters state index: {str(e)}".encode())
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ParamPollutionService).serve_forever()
