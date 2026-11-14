
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class AclBitmaskService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/acl-bitmask": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "subject_id": {"type": "integer"}, "object_id": {"type": "integer"}, "required_bits": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/acl-bitmask" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                acl_flags = (data["subject_id"] ^ data["object_id"]) << data["required_bits"]
                if acl_flags % data["subject_id"] != 0:
                    raise PermissionError("Bitmask ACL verification failed")
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"flags": acl_flags}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"ACL_MASK_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), AclBitmaskService).serve_forever()
