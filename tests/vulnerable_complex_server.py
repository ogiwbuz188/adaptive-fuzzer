from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import re

class EnterpriseComplexVulnerableService(BaseHTTPRequestHandler):
    """
    An advanced mock service engineered to simulate multiple layers of microservice
    flaws (Data Leakage, Memory Stress, Logic Bugs, Type Confusion, and Resource Locks)
    without completely dropping the network socket connection.
    """
    
    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {
                "paths": {
                    "/api/v2/secure-process": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "data_chunk": {"type": "string"},
                                                "user_profile": {"type": "object"},
                                                "transaction_id": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schema).encode())
            return
        
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if "/api/v2/secure-process" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                # Attempt structural parsing
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception as parse_err:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"FATAL EXCEPTION: org.json.JSONException: Invalid token sequence character map. {str(parse_err)}".encode())
                return

            # Extract fields for multi-vector anomaly simulation
            data_chunk = parsed_json.get("data_chunk")
            user_profile = parsed_json.get("user_profile")
            transaction_id = parsed_json.get("transaction_id")

            # 🚨 BUG VECTOR 1: Directory Traversal Data Leak (Triggered by strings like ../)
            if isinstance(data_chunk, str) and "../" in data_chunk:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL FAILURE: java.io.FileNotFoundException: System core leakage mapping: root:x:0:0:root:/root:/bin/bash")
                return

            # 🚨 BUG VECTOR 2: Buffer/Heap Memory Boundary Stress (Triggered by massive string overflow strings)
            if isinstance(data_chunk, str) and len(data_chunk) > 15000:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL OUT_OF_MEMORY: C++ vector<T> allocation boundary limits breached. NullPointer Dereference tracking dump.")
                return

            # 🚨 BUG VECTOR 3: Algorithmic ReDoS / Delay Locking (Triggered by deeply nested JSON configurations)
            if isinstance(user_profile, dict) and len(str(user_profile)) > 200:
                # Simulates an infinite evaluation regex pattern hanging the microservice CPU execution loop
                time.sleep(2.1)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "degraded_performance_due_to_cpu_lock"}')
                return

            # 🚨 BUG VECTOR 4: Business Logic Breakdown / SQL injection string parsing
            if isinstance(data_chunk, str) and any(sqli in data_chunk.upper() for sqli in ["UNION", "SELECT", "' OR"]):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"SQLITE_EXEC_ERROR: Driver syntax validation failed at offset 0x4F. Unhandled SQLite3Exception trace triggered.")
                return

            # 🚨 BUG VECTOR 5: Data Type Confusion / Schema Breakdown (Triggered by corrupting expected integer blocks)
            if transaction_id is not None and not isinstance(transaction_id, int):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"UNCAUGHT RUNTIME FAULT: TypeError: Cannot cast structural object configuration type '{type(transaction_id).__name__}' down into numeric binary columns.".encode())
                return

            # Regular validation route path
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "transaction_authorized"}')
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), EnterpriseComplexVulnerableService)
    print("[*] Enterprise Complex Test Target Active on http://localhost:9000")
    print("[*] Monitoring multi-vector injection patterns...")
    server.serve_forever()
