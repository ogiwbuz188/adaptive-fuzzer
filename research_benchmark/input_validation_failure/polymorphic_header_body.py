
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class PolymorphicHeaderBodyService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/context-gate": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "session_blob": {"type": "object"}, "client_flag": {"type": "boolean"},
                "retry_limit": {"type": "integer"}, "payload_tag": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/context-gate" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            try: data = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            ua = self.headers.get("User-Agent", "Unknown")
            os_branch = "WIN" if "Windows" in ua else ("MAC" if "Macintosh" in ua else "NIX")

            if not isinstance(data, dict):
                self.send_response(400); self.end_headers(); return

            faults = []
            if not isinstance(data.get("session_blob"), dict):
                faults.append(f"BLOB_{type(data.get('session_blob')).__name__}")
            if not isinstance(data.get("client_flag"), bool):
                faults.append(f"FLAG_{type(data.get('client_flag')).__name__}")
            if not isinstance(data.get("retry_limit"), int):
                faults.append(f"RETRY_{type(data.get('retry_limit')).__name__}")
            if len(str(data.get("payload_tag", ""))) > 25:
                faults.append("TAG_OVERFLOW")

            if faults:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"CONTEXT_GATE_EXCEPTION: OS[{os_branch}] failed validation chain [{'+'.join(faults)}]".encode())
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"context_verified"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), PolymorphicHeaderBodyService).serve_forever()
