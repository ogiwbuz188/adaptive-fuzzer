
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MetadataSchemaPollutionService(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {"paths": {"/api/v1/metadata-pollution": {"post": {"requestBody": {"content": {"application/json": {"schema": {"properties": {"meta_attributes": {"type": "object"}}}}}}}}}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v1/metadata-pollution" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            meta = parsed_json.get("meta_attributes")
            
            try:
                # Simulated complex object merging routine vulnerable to type pollution
                if not isinstance(meta, dict):
                    # Blindly processing properties without validating inner structures
                    raise AttributeError("Invalid mapping descriptor format initialized.")
                
                # 🚨 CRASH POINT: If fuzzer mutates keys into lists or types that lack a .items() method
                runtime_cache = {}
                for key, value in meta.items():
                    if isinstance(value, dict):
                        for sub_key, sub_val in value.items():
                            runtime_cache[f"sys_{sub_key}"] = sub_val
                    else:
                        runtime_cache[key] = str(value).upper()
                        
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "sync_complete", "keys": list(runtime_cache.keys())}).encode())
                
            except Exception as system_fault:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"UNCAUGHT_SCHEMA_EXCEPTION: AttributeError: Core dynamic metadata compiler crashed while processing schema map definitions tracking offset window: {str(system_fault)}".encode())
            return

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), MetadataSchemaPollutionService)
    print("[*] Metadata Pollution Microservice running on http://localhost:9000")
    server.serve_forever()
