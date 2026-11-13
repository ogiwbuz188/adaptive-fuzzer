
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
import json

class DatetimeCronParserService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/schedule-cron": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {
                "iso_date": {"type": "string"}, "offset_days": {"type": "integer"},
                "offset_seconds": {"type": "integer"}, "timezone_tag": {"type": "string"}
            }}}}}}}}}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(schema).encode()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if "/api/v1/schedule-cron" in self.path:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            try:
                base_dt = datetime.fromisoformat(data["iso_date"])
                delta = timedelta(days=data["offset_days"], seconds=data["offset_seconds"])
                scheduled = (base_dt + delta).strftime(f"%Y-%m-%d %H:%M:%S {data['timezone_tag']}")
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"scheduled_at": scheduled}).encode())
            except Exception as err:
                self.send_response(500); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(f"TEMPORAL_PARSER_EXCEPTION: Cron scheduler failed with {type(err).__name__}: {str(err)}".encode())

if __name__ == "__main__":
    HTTPServer(("localhost", 9000), DatetimeCronParserService).serve_forever()
