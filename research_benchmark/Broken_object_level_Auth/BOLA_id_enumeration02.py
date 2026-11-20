from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlsplit


OWNED_OBJECTS = {
    "42": {
        "id": "42",
        "owner": "owner",
        "record": "synthetic owner-only record",
    }
}


class BOLAAccessControlService(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        return

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/swagger.json":
            self._send_json(
                200,
                {
                    "paths": {
                        "/api/v1/user-lookup": {
                            "get": {
                                "parameters": [
                                    {
                                        "name": "id",
                                        "in": "query",
                                        "schema": {"type": "string"},
                                    }
                                ]
                            }
                        }
                    }
                },
            )
            return

        if urlsplit(self.path).path != "/api/v1/user-lookup":
            self._send_json(404, {"error": "not found"})
            return

        object_id = parse_qs(urlsplit(self.path).query).get("id", [""])[0]
        principal = {
            "Bearer owner-token": "owner",
            "Bearer other-token": "other",
        }.get(self.headers.get("Authorization"))
        record = OWNED_OBJECTS.get(object_id)

        if principal is None:
            self._send_json(401, {"error": "authentication required"})
        elif record is None:
            self._send_json(404, {"error": "object not found"})
        elif record["owner"] != principal:
            self._send_json(403, {"error": "forbidden"})
        else:
            self._send_json(200, record)


if __name__ == "__main__":
    HTTPServer(("localhost", 9000), BOLAAccessControlService).serve_forever()
