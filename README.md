# 🛡️ Adaptive Behavioral Fuzzer (ABF)

An advanced, autonomous security testing framework designed to discover memory boundaries, logic errors, and security misconfigurations in RESTful microservices without human intervention. 

By leveraging an evolutionary genetic feedback loop, the framework dynamically mutates request layouts, bypasses network security thresholds, and profiles microsecond latency spikes before compiling everything into a self-contained web telemetry application dashboard.

---

## ✨ Features & Architecture Upgrades
- **Zero-Config Discovery:** Automatically crawls and parses OpenAPI/Swagger specifications to build live endpoint attack matrices.
- **Enterprise-Capable Mutations:** Recursively creates and corrupts nested JSON payloads to match complex application schemas.
- **WAF & Rate-Limiter Evasion:** Employs user-agent header rotation and adaptive request jitter to bypass traffic blocking rules.
- **Genetic Feedback Loop:** Feeds successful anomaly-inducing mutations back into the core seed pool to surface deep memory leaks over long sessions.
- **Automated UI Compiler:** Generates a clean, single-page HTML dashboard summarizing exceptions and system telemetry upon completion.

---

## ⚙️ Core Engineering Mechanisms

### 1. Attack Surface Mapping
The engine maps out query vectors and complex request bodies (`application/json`) from local or remote Swagger definition sheets. It stores parameters alongside structural type layouts.

### 2. Recursive Structural Mutation Engine
Inputs undergo heavy mutation strategies targeted at systemic runtime boundaries:
- **Type Scrambling & Confusion:** Replaces valid primitives with complex nested structures, multi-layered arrays, and invalid datatypes (`None`, `bool`, massive integers) to break deserialization filters.
- **Memory Exceeded Overflows:** Scales variable text bounds drastically (up to 30,000+ characters) to stress string allocation buffers and trigger segmentation faults.
- **Sanitisation Traversal:** Injects traversal indices (`../../etc/passwd`), null bytes (`\x00`), and raw script fragments to look for input validation gaps.

### 3. Asynchronous Pipeline & Traffic Evasion
The execution matrix drives traffic through high-speed, parallel worker pools using Python’s `concurrent.futures`. To prevent Web Application Firewalls (WAFs) or API Gateways from instantly banning the fuzzer's IP, every thread injects randomized millisecond timing delays (jitter) and selects a clean browser `User-Agent` identity for each request.

---

## 🚀 Quick Start & Project Execution

### 📦 Prerequisites
Install the required HTTP library:
```bash
pip install requests
```

### 🛠️ Configuration & Customization
To point the fuzzer at your own targets, open `src/fuzzer.py` and modify the configuration block at the bottom of the file:

* **`TARGET_HOST`**: Set this to your local server (`http://localhost:9000`) or your remote staging microservice URL.
* **`SPEC_URL`**: Provide the URL or local file path to the OpenAPI/Swagger JSON definition sheet.
* **`ENTERPRISE_TOKEN`**: Pass your authorization session string here (e.g., Bearer JWT tokens) if testing a secure endpoint. Pass `None` if the API is public.

### 💻 Running the Fuzzer
Run the orchestrated pipeline runner (which handles starting the test server and the fuzzer together):
```bash
python run_test.py
```

### 📊 Inspecting Telemetry Results
Once the session completes, double-click the newly generated `fuzz_dashboard.html` file in your root folder. It will load an interactive single-page diagnostics UI directly in any web browser to let you easily audit systemic vulnerabilities, uncaught 500 crashes, and latency alerts.


