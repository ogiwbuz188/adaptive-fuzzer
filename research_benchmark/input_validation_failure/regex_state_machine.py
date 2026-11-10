
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class RegexStateMachineService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/state-parser": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "token_a": {"type": "string"}, "token_b": {"type": "string"}, "token_c": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/state-parser" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            try: data = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            if not isinstance(data, dict):
                self.send_response(400); self.end_headers(); return

            triggers = ["%x", "%s", "'", "<script>", "../", "true", "null", "AAAA"]
            hit_states = []
            for key in ["token_a", "token_b", "token_c"]:
                val = str(data.get(key, ""))
                for idx, trig in enumerate(triggers):
                    if trig in val:
                        hit_states.append(f"{key}_S{idx}_{len(val)%15}")

            if hit_states:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"LEXER_STATE_EXCEPTION: Unhandled grammar transition [{' | '.join(hit_states)}] in token compiler.".encode())
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"tokens_clean"}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RegexStateMachineService).serve_forever()
