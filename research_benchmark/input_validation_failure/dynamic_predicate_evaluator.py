
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DynamicPredicateService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/eval-predicate": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "left_operand": {"type": "integer"}, "operator_sym": {"type": "string"},
                "right_operand": {"type": "integer"}, "fallback_expr": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/eval-predicate" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                expr = f"({data['left_operand']} {data['operator_sym']} {data['right_operand']}) or ({data['fallback_expr']})"
                outcome = eval(expr, {"__builtins__": {}}, {})
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"matched": bool(outcome)}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"AST_PREDICATE_EXCEPTION: Expression evaluator failed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), DynamicPredicateService).serve_forever()
