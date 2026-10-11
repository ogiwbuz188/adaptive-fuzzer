#Copyright (c) 2026 Japneet Kaur [ogiwbuz188]

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at :

#   http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, softwaredistributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
#language governing permissions and limitations under the License.

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import uuid

class HyperVulnerableBankingService(BaseHTTPRequestHandler):
    """
    An advanced financial microservice layer designed with stateful authentication,
    cryptographic schema checks, and dynamic algorithmic rate-limiting anomalies
    to push the evolutionary boundaries of the behavioral testing fuzzer.
    """
    # Simulate an active session vault cache database memory footprint leaks
    ACTIVE_SESSIONS = {"session_token_999": {"user_id": 42, "role": "user", "balance": 5000.00}}
    REQUEST_COUNTERS = {}

    def do_GET(self):
        if self.path == "/swagger.json":
            schema = {
                "paths": {
                    "/api/v3/transfer-funds": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "auth_metadata": {"type": "object"},
                                                "transaction_payload": {"type": "object"},
                                                "compliance_checksum": {"type": "string"}
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
        if "/api/v3/transfer-funds" in self.path:
            client_ip = self.client_address[0]
            current_time = time.time()
            
            # 🚨 BUG VECTOR 1: Algorithmic Rate-Limiter CPU State Lock (Denial of Service)
            # Fuzzer multi-threading tracking can choke this unoptimized calculation pool
            if client_ip not in self.REQUEST_COUNTERS:
                self.REQUEST_COUNTERS[client_ip] = []
            self.REQUEST_COUNTERS[client_ip].append(current_time)
            
            # Unoptimized algorithm loop creates exponential latency penalties under load
            recent_requests = [t for t in self.REQUEST_COUNTERS[client_ip] if current_time - t < 10]
            if len(recent_requests) > 10:
                time.sleep(1.8) # Simulate structural thread exhaustion lockup
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Rate limit exceeded. Thread locking activated."}')
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                parsed_json = json.loads(body_bytes.decode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"FATAL SERIALIZATION EXCEPTION: com.fasterxml.jackson.databind.exc.MismatchedInputException: {str(e)}".encode())
                return

            auth = parsed_json.get("auth_metadata", {})
            payload = parsed_json.get("transaction_payload", {})
            checksum = parsed_json.get("compliance_checksum")

            # 🚨 BUG VECTOR 2: Cryptographic Null-Pointer Token Bypass
            # If the fuzzer injects an unexpected datatype into the checksum variable
            if checksum is not None and not isinstance(checksum, str):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"CRITICAL NULL_POINTER_DEREFERENCE: C++ engine segment faulted while reading memory pointer offset calculation from token verification stack.")
                return

            # 🚨 BUG VECTOR 3: Session De-serialization Information Disclosure Leak
            # If the fuzzer hits a specific object type structure inside auth parameters
            if isinstance(auth, dict) and "session_token" in auth:
                token = auth.get("session_token")
                if token not in self.ACTIVE_SESSIONS and isinstance(token, (dict, list)):
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"UNCAUGHT EXCEPTION: org.hibernate.exception.SQLGrammarException: select * from core_vault_sessions where token = " + str(token).encode())
                    return

            # 🚨 BUG VECTOR 4: Polymorphic Type Confusion / Business Logic Vulnerability
            # Transfer amount variables expect numbers, but fuzzer can pass arrays or boolean tags
            if isinstance(payload, dict) and "amount" in payload:
                amount = payload.get("amount")
                
                # Boundary check failure: String buffer injection stress
                if isinstance(amount, str) and len(amount) > 10000:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"SYSTEM STACK OVERFLOW: Infinite memory allocation trace error in balance buffer ledger block compilation parsing window.")
                    return
                
                # Logic break: Negative balance value injection
                if isinstance(amount, (int, float)) and amount < 0:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"LEDGER EXCEPTION: Negative ledger adjustments forbidden. Transaction hash signature failed validation constraint mappings.")
                    return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "transaction_processed_successfully", "code": "200_OK"}')
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("localhost", 9000), HyperVulnerableBankingService)
    print("[*] Hyper-Vulnerable Banking Microservice Engine Online on http://localhost:9000")
    print("[*] Auditing compliance transaction logic boundaries securely...")
    server.serve_forever()
