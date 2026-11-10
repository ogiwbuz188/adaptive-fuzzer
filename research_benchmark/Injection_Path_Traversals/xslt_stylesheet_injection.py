
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class XsltInjectionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/transform-xslt": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"stylesheet_uri": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/transform-xslt" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            uri = parsed_json.get("stylesheet_uri")
            if isinstance(uri, str) and ("<script>" in uri or "../" in uri):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"CRITICAL_XSLT_CRASH: javax.xml.transform.TransformerConfigurationException: Arbitrary script execution blocked in Xalan processor stack.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "transformed"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), XsltInjectionService).serve_forever()
