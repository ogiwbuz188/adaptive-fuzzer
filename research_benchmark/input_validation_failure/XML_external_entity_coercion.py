from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class XmlCoercionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/xml-coerce": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"xml_payload_str": {"type": "string"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/xml-coerce" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            xml_str = parsed_json.get("xml_payload_str")
            if isinstance(xml_str, str) and ("<!ENTITY" in xml_str or "SYSTEM" in xml_str):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"VERBOSE_LEAK_EXCEPTION: org.xml.sax.SAXParseException: Unhandled External Entity Reference routing mapping system configuration crash.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"parsed"}')
if __name__ == "__main__":
    HTTPServer(("localhost", 9000), XmlCoercionService).serve_forever()
