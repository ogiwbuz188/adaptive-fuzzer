
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class GraphqlDepthService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/graphql-query": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"query_document": {"type": "string"}}}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/graphql-query" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try: parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception: self.send_response(400); self.end_headers(); return

            query_doc = parsed_json.get("query_document")
            if isinstance(query_doc, dict) or (isinstance(query_doc, str) and (query_doc.count("{") > 2 or len(query_doc) > 300)):
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"UNCAUGHT_PARSER_EXCEPTION: graphql.execution.AbortExecutionException: Query AST depth and alias resolution exceeded execution stack limits.")
                return
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"data": {"status": "resolved"}}')

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), GraphqlDepthService).serve_forever()
