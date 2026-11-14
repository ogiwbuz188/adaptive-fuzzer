
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CrossTenantBucketRouterService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/bucket-shard": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "tenant_num": {"type": "integer"}, "shard_total": {"type": "integer"}, "bucket_key": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/bucket-shard" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                shard_idx = data["tenant_num"] % data["shard_total"]
                bucket_uri = f"shard_{shard_idx}/" + data["bucket_key"].encode("ascii").decode("ascii")
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"uri": bucket_uri}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"SHARD_BOLA_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), CrossTenantBucketRouterService).serve_forever()
