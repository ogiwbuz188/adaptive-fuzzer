
from http.server import HTTPServer, BaseHTTPRequestHandler
import xml.etree.ElementTree as ET
import json

class XmlEtreeFragmentService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/xml-fragment": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "tag_name": {"type": "string"}, "inner_text": {"type": "string"}, "attr_val": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/xml-fragment" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                xml_blob = f"<{data['tag_name']} id='{data['attr_val']}'>{data['inner_text']}</{data['tag_name']}>"
                root = ET.fromstring(xml_blob)
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"tag": root.tag}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"XML_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), XmlEtreeFragmentService).serve_forever()
