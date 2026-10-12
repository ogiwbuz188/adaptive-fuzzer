# Adaptive Behavioral Fuzzer

A lightweight, autonomous API fuzzing engine designed to stress-test REST services, identify boundary-condition failures, and generate human-readable telemetry dashboards and analytics from the resulting findings.

This repository combines dynamic route discovery, adaptive payload generation, multi-threaded execution, automated HTML reporting, CSV telemetry capture, and GitHub Actions integration to help uncover edge-case vulnerabilities in benchmark services.

## Why this project exists

Modern APIs often fail under unexpected, malformed, oversized, nested, or hostile payloads. Traditional validation may miss edge cases that only appear under realistic traffic patterns or concurrent use.

This project helps by:

- scanning benchmark server scripts in the `research_benchmark/` directory,
- extracting the relevant API route automatically,
- building payloads that trigger boundary and type-confusion issues,
- exercising the endpoint repeatedly under a fuzzing workflow,
- capturing anomalies such as timeouts, 500 responses, latency spikes, debug leakage, and connection drops,
- producing a dashboard and data exports that summarize the findings for review.

## What is now included

The project includes:

- multi-target execution across multiple Python benchmark environments,
- automatic route extraction from server files,
- API-version-aware payload generation (`v1`, `v2`, `v3`),
- telemetry CSV export for analytics,
- chart generation via `notebooks/generate_plots.py`,
- GitHub Actions automation for CI execution and artifact uploads,
- HTML dashboards and PNG analysis charts for visual review.

## Key features

- automatic discovery of benchmark server scripts under `research_benchmark/`
- recursive scanning of nested benchmark subdirectories
- dynamic route extraction from server implementations
- API-version-aware payload schema selection (`v1`, `v2`, `v3`, and fallback behavior)
- multi-target execution across multiple Python endpoints
- request mutation strategies for oversized, malformed, nested, and hostile inputs
- concurrency-driven fuzzing execution with thread workers
- HTML telemetry report generation per discovered target
- CSV dataset generation for downstream analysis
- Python chart generation for telemetry summaries
- CI-friendly execution via GitHub Actions

## Repository structure

```text
adaptive-fuzzer/
├── .github/
│   └── workflows/
│       └── fuzz.yml
├── data/
│   └── test_runs.csv            # generated telemetry export
├── notebooks/
│   └── generate_plots.py        # analytics and chart generation
├── src/
│   └── fuzzer.py                # core fuzzing engine
├── research_benchmark/
│   ├── input_validation_failure/
│   │   └── missing_type_casts.py
│   ├── memory_safety/
│   │   └── ...
│   └── ...
├── requirements.txt
├── run_test.py                  # orchestration entry point
├── README.md
├── *_dashboard.html             # generated HTML dashboards
├── LICENSE.md
└── notebooks/                   # generated PNG chart outputs
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

1. Finds all Python files under `research_benchmark/` recursively
2. Reads each benchmark server to locate the target route
3. Starts the target script locally
4. Builds the correct endpoint configuration dynamically
5. Executes the fuzzing loop against that target
6. Saves a per-file telemetry report like `servername_dashboard.html`
7. Appends results to `data/test_runs.csv`

## Auto-discovery and route extraction

The `run_test.py` workflow no longer depends on hardcoded branch logic for each target type. Instead, it does this automatically:

- checks every `.py` file in `research_benchmark/` and nested folders
- extracts the endpoint string from the benchmark file
- identifies the API version from the route (for example `/api/v3/...`)
- selects the right request schema for that version
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

This means if you add a new server file under `research_benchmark/` or any subdirectory, you do not need to modify `run_test.py` again just to support it.

## Adding a new benchmark file

Create a new Python file under `research_benchmark/` or in a nested subdirectory, for example:

```python
# research_benchmark/new_category/new_api_server.py
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

## Telemetry outputs

Each discovered benchmark file produces its own HTML dashboard report, like:

```text
missing_type_casts_dashboard.html
memory_guard_dashboard.html
new_api_server_dashboard.html
```

These reports include:

- total request counts
- discovered route information
- HTTP status results
- failure patterns and anomaly classes
- payload samples and evidence snippets

In addition, the system appends structured findings to `data/test_runs.csv` for downstream analysis.

## Analytics and chart generation

The repository includes a plotting script at `notebooks/generate_plots.py` to convert captured telemetry into visual summaries.

This script reads `data/test_runs.csv` and creates charts such as:

- vulnerability distribution bar charts,
- request timeline status plots,
- summary visualizations for CI or report review.

Example usage:

```bash
python notebooks/generate_plots.py
```

The script writes PNG files into the `notebooks/` directory, which are then suitable for artifact storage and shareable reports.

## GitHub Actions integration

The CI workflow in `.github/workflows/fuzz.yml` runs the fuzzer, generates telemetry, and archives the outputs.

```yaml
name: Automated Boundary Fuzzing

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  fuzz-test:
    name: Execute Autonomous Multi-Target Fuzz Matrix
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Code Repository
      uses: actions/checkout@v4

    - name: Set up Python Environment
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install Environment Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Execute Autonomous Fuzzing Loop
      run: |
        python run_test.py

    - name: Compile Analytical Telemetry Paper Charts
      if: always()
      run: |
        python notebooks/generate_plots.py

    - name: Archive All Generated Telemetry Reports & Visual Charts
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: fuzzer-telemetry-reports
        path: |
          *_dashboard.html
          notebooks/*.png
          data/*.csv
        retention-days: 7
```

This allows telemetry reports and plots to be uploaded as GitHub Actions artifacts for review.

## Project components

### `run_test.py`

This is the orchestration entry point. It:

- discovers benchmark targets,
- extracts endpoint routes,
- starts the target server,
- configures the fuzzer,
- runs the fuzz session,
- exports the HTML dashboard,
- writes telemetry CSV rows.

### `src/fuzzer.py`

This contains the core fuzzing logic, including:

- request generation,
- mutation strategies,
- endpoint handling,
- concurrency execution,
- anomaly detection,
- dashboard generation,
- CSV export generation.

### `notebooks/generate_plots.py`

This handles analytical chart generation from the telemetry dataset.

### `research_benchmark/`

This directory contains benchmark API servers used for local validation and telemetry generation.

## Example anomaly classes detected

The fuzzer can surface issues such as:

- `500_INTERNAL_SERVER_ERROR`
- `TIMEOUT_EXHAUSTION`
- `HIGH_LATENCY_DELAY`
- `VERBOSE_LEAK_EXCEPTION`
- `VERBOSE_LEAK_SEGMENTATION FAULT`
- `CONNECTION_DROP_OR_DATA_FAULT`

## Notes

This project is intended for controlled testing in local environments, lab environments, or systems you own or are explicitly authorized to test. Use it responsibly and only against environments you are permitted to assess.

---

Quick usage summary:

```bash
pip install -r requirements.txt
python run_test.py
python notebooks/generate_plots.py
```

Then open the generated `*_dashboard.html` file or inspect the generated PNG charts in `notebooks/` to review the results.
