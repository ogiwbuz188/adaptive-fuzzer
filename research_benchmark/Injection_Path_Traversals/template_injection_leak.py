from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TemplateInjectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/template-render": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"template_compile_path": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/template-render" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            tpath = parsed_json.get("template_compile_path")
            if isinstance(tpath, str) and "../" in tpath:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: java.io.IOException: Server template loader configuration matrix validation collapsed. System reference root state trace compiled: root:x:0:0")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"template_rendered"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), TemplateInjectionService).serve_forever()
