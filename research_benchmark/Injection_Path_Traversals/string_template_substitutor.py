
from http.server import HTTPServer, BaseHTTPRequestHandler
from string import Template
import json

class StringTemplateSubstitutorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/render-template": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "raw_template": {"type": "string"}, "context_vars": {"type": "object"}, "fallback_var": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/render-template" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                tmpl = Template(data["raw_template"] + " $" + data["fallback_var"])
                rendered = tmpl.substitute(data["context_vars"])
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"rendered": rendered}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"SSTI_TEMPLATE_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), StringTemplateSubstitutorService).serve_forever()
