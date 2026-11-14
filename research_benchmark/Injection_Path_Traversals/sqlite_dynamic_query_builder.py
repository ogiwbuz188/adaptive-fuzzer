
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3

class SqliteQueryBuilderService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/sql-search": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "table_col": {"type": "string"}, "search_val": {"type": "string"}, "row_limit": {"type": "integer"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/sql-search" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                conn = sqlite3.connect(":memory:")
                conn.execute("CREATE TABLE users (id INT, name TEXT)")
                query = f"SELECT {data['table_col']} FROM users WHERE name = '{data['search_val']}' LIMIT {data['row_limit']}"
                rows = conn.execute(query).fetchall()
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"rows": rows}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"SQLITE_INJECTION_EXCEPTION: {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), SqliteQueryBuilderService).serve_forever()
