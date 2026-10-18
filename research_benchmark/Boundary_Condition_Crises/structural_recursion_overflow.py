
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class StructuralRecursionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/recursion-depth": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"nested_tree": {"type": "object"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def _parse_depth(self, node, depth=0):
        if depth > 10:
            raise OverflowError("Maximum architectural tracking recursion depth exceeded.")
        if isinstance(node, dict):
            for k, v in node.items():
                self._parse_depth(v, depth + 1)

    def do_POST(self):
        if "/api/v1/recursion-depth" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            tree = parsed_json.get("nested_tree")
            
            try:
                # 🚨 CRASH POINT: Deeply nested JSON strategy breaks internal processing loop
                self._parse_depth(tree)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "tree_validated"}')
            except OverflowError as overflow_err:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"SYSTEM_STACK_OVERFLOW: RuntimeError: Uncaught stack frames overflow limit hit while executing JSON schema depth calculations: {str(overflow_err)}".encode())
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), StructuralRecursionService)
    print("[*] Structural Recursion Service running on http://localhost:9000")
    server.serve_forever()
