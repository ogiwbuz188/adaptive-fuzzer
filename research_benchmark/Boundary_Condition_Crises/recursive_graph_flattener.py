
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class RecursiveGraphFlattenerService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/flatten-graph": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "graph_payload": {"type": "object"}, "unroll_cycles": {"type": "integer"}, "prefix_key": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def _flatten(self, node, cycles):
        if cycles > 0:
            return self._flatten({"nested": node}, cycles - 1)
        out = []
        for k, v in node.items():
            if isinstance(v, dict):
                out.extend(self._flatten(v, 0))
            else:
                out.append(str(k) + ":" + v)
        return out

    def do_POST(self):
        if "/api/v1/flatten-graph" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                flattened = self._flatten(data["graph_payload"], data["unroll_cycles"])
                joined = data["prefix_key"].join(flattened)
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"items": len(joined)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"STACK_DEPTH_EXCEPTION: Graph flattener hit stack boundary {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), RecursiveGraphFlattenerService).serve_forever()
