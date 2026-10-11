# Adaptive Behavioral Fuzzer

A lightweight, autonomous API fuzzing engine designed to stress-test REST services, identify boundary-condition failures, and generate human-readable telemetry dashboards from the results.

This repository combines dynamic route discovery, adaptive payload generation, multi-threaded execution, and automated HTML reporting to help uncover fragile application behavior quickly and reliably.

## Why this project exists

Modern APIs often fail under unexpected, malformed, oversized, nested, or hostile payloads. Traditional validation may miss edge cases that only appear under real traffic patterns. This project helps surface those failures by:

- scanning test server scripts in the `tests/` directory,
- extracting the relevant API route automatically,
- building payloads that trigger boundary and type confusion issues,
- exercising the endpoint repeatedly under a fuzzing workflow,
- capturing anomalies such as timeouts, 500 responses, latency spikes, and debug leakage,
- producing a dashboard summarizing the findings for review.

## Key features

- automatic discovery of test server scripts under `tests/`
- dynamic route extraction from server implementations
- API-version-aware payload schema selection (`v1`, `v2`, `v3`, and fallback behavior)
- multi-target execution across multiple Python test files
- request mutation strategies for oversized or malformed inputs
- concurrency-driven fuzzing execution
- HTML telemetry report generation per discovered test file
- CI-friendly execution via GitHub Actions

## Repository structure

```text
adaptive-fuzzer/
├── .github/
│   └── workflows/
│       └── fuzz.yml
├── src/
│   └── fuzzer.py
├── tests/
│   └── mock_server.py
├── run_test.py
├── requirements.txt
├── README.md
└── *_dashboard.html   # generated artifacts after execution
```

## Prerequisites

- Python 3.11+
- pip
- Git

## Install dependencies

```bash
pip install -r requirements.txt
```

## How to run the fuzzing engine

From the repository root:

```bash
python run_test.py
```

This script:

1. Finds all Python files under `tests/`
2. Reads each test server to locate the target route
3. Starts the target script locally
4. Builds the correct endpoint configuration dynamically
5. Executes the fuzzing loop against that target
6. Saves a per-file telemetry report like `servername_dashboard.html`

## How the auto-discovery works

The upgraded `run_test.py` no longer depends on hardcoded `if "v3" ... elif "v2" ...` logic. Instead, it does this automatically:

- checks every `.py` file in `tests/`
- extracts the endpoint string from the test file
- identifies the API version from the route (for example `/api/v2/...`)
- chooses the right request schema for that version
- configures the fuzzer automatically

Example logic:

```python
def get_api_version(path):
    match = re.search(r"/api/(v\d+)/", path)
    return match.group(1) if match else "v1"
```

Then the script maps that version to a payload template:

```python
schemas = {
    "v3": {
        "auth_metadata": {"type": "object"},
        "transaction_payload": {"type": "object"},
        "compliance_checksum": {"type": "string"},
    },
    "v2": {
        "data_chunk": {"type": "string"},
        "user_profile": {"type": "object"},
        "transaction_id": {"type": "string"},
    },
    "v1": {
        "data": {"type": "string"},
    },
}
```

This means if you add a new server file under `tests/`, you do not need to modify `run_test.py` again just to support it.

## Adding a new test server file

Create a new Python file which you want to test under `tests/`, for example:

```python
# tests/new_api_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/v3/process', methods=['POST'])
def process_request():
    payload = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "received": payload})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
```

Then run:

```bash
python run_test.py
```

The engine will automatically detect the file, extract `/api/v3/process`, build a matching endpoint configuration, and generate a report for that file.

## Output artifacts

Each discovered test file produces its own HTML dashboard report, like:

```text
mock_server_dashboard.html
new_api_server_dashboard.html
```

These reports include:

- request totals
- discovered route information
- HTTP status results
- failure patterns and anomaly classes
- payload samples and evidence snippets

## GitHub Actions integration

This repository includes a CI workflow in `.github/workflows/fuzz.yml`:

```yaml
name: Automated Boundary Fuzzing

on: [push]

jobs:
  fuzz-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run Tests
        run: |
          pip install -r requirements.txt
          python run_test.py
      - name: Save Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: fuzzer-telemetry-reports
          path: "*_dashboard.html"
```

This allows telemetry reports to be uploaded as GitHub Actions artifacts for review.

## Project components

### `run_test.py`

This is the orchestration entry point. It:

- discovers test targets,
- extracts endpoint routes,
- starts the target server,
- configures the fuzzer,
- runs the fuzz session,
- exports the HTML dashboard.

### `src/fuzzer.py`

This contains the core fuzzing logic, including:

- request generation,
- mutation strategies,
- endpoint handling,
- concurrency execution,
- anomaly detection,
- dashboard generation.

### `tests/`

This directory contains mock or real test API servers used for local validation and telemetry generation.

## Notes

This project is intended for controlled testing in local environments, lab environments, or systems you own or are explicitly authorized to test. Use it responsibly and only against environments where you have the right to assess security behavior.



---

Quick usage summary:

```bash
pip install -r requirements.txt
python run_test.py
```

Then open the generated `*_dashboard.html` file to inspect the results.
