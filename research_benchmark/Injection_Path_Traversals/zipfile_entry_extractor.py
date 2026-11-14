
from http.server import HTTPServer, BaseHTTPRequestHandler
import zipfile
import io
import json

class ZipfileEntryExtractorService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/zip-entry": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "archive_member": {"type": "string"}, "decode_codec": {"type": "string"}, "slice_len": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/zip-entry" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                mem = io.BytesIO()
                with zipfile.ZipFile(mem, "w") as zf:
                    zf.writestr("manifest.txt", "ok")
                mem.seek(0)
                with zipfile.ZipFile(mem, "r") as zf:
                    raw = zf.read(data["archive_member"])
                text = raw.decode(data["decode_codec"])[:data["slice_len"]]
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"text": text}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"ZIP_SLIP_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), ZipfileEntryExtractorService).serve_forever()
