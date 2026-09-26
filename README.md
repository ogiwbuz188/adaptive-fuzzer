# Adaptive Behavioral Fuzzer

A lightweight, autonomous API fuzzing framework built to stress-test REST services, identify boundary-condition failures, and generate a human-readable security dashboard from the resulting findings.

This repository combines OpenAPI/Swagger-driven route discovery, adaptive payload mutation, multi-threaded execution, and automatic HTML reporting to help surface fragile application behavior quickly.

## Why this project exists

Modern APIs often fail under unexpected, malformed, oversized, or deeply nested request payloads. Traditional validation checks may miss edge cases that only appear under real traffic patterns. This project was designed to automate that discovery process by:

- scanning API route definitions,
- generating adversarial payloads,
- exercising endpoints across multiple worker threads,
- recording anomalies such as timeouts, 500s, latency spikes, and verbose error leakage,
- producing a dashboard that summarizes the findings for review.

## Key features

- Swagger/OpenAPI-based endpoint discovery
- Recursive JSON payload generation for structured request bodies
- Mutation strategies for overflow, type confusion, traversal, and format abuse
- Parallel fuzz execution using Python concurrency
- Request logging and anomaly classification
- HTML telemetry dashboard generation
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
└── mock_server_dashboard.html   # generated after running the pipeline
```

## Getting started

### Prerequisites

- Python 3.11+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the fuzzer

```bash
python run_test.py
```

This launches the local mock API server, discovers the `/api/v1/process` route, runs the fuzzing session, and generates a telemetry dashboard.

## What the pipeline does

`run_test.py` orchestrates the full testing flow:

1. Finds test server scripts under `tests/`
2. Extracts a route from the target server schema
3. Starts the local HTTP server
4. Configures the fuzzer with the discovered endpoint
5. Runs concurrent mutation-based requests
6. Captures anomalies and status codes
7. Saves the HTML dashboard report

## Fuzzing behavior

The fuzzer creates structured and adversarial inputs by mutating JSON fields based on the endpoint’s expected schema. Example mutation types include:

- oversized strings
- nested objects and arrays
- invalid scalar types
- traversal payloads such as `../etc/passwd`
- format-string payloads
- boundary-condition keywords that trigger error leakage

This helps identify responses that reveal implementation weaknesses, high latency conditions, or service instability.

## Output and reporting

After the run completes, the project generates a dashboard such as:

```text
mock_server_dashboard.html
```

The dashboard includes:

- total request volume,
- route coverage,
- anomaly classifications,
- HTTP status details,
- payload samples,
- evidence snippets from server responses.

## GitHub Actions workflow

The repository includes a workflow in `.github/workflows/fuzz.yml` to automate the fuzzing run in CI.

The workflow:

- checks out the repository,
- sets up Python 3.11,
- installs dependencies,
- executes `python run_test.py`,
- uploads the generated dashboard as an artifact.

This helps ensure that fuzzing checks remain part of the automated validation pipeline.

## Project components

### `run_test.py`

Entry point for the full execution pipeline. It boots the mock server, wires in the fuzzer, sets the route, runs the test session, and saves the generated report.

### `src/fuzzer.py`

Contains the core logic for:

- Swagger route parsing,
- mutation generation,
- payload construction,
- concurrent request execution,
- anomaly analysis,
- dashboard generation.

### `tests/mock_server.py`

A deliberately vulnerable mock service used to validate the fuzzer against common attack patterns and boundary failures.

## Example usage

```bash
python run_test.py
```

Then open the generated HTML report in a browser to inspect the results.

## Notes

This repository is intended for security research, controlled API testing, and educational use in simulated or local environments. Always validate on systems you own or are explicitly authorized to test.

## License

This project is provided as-is for research and experimentation. Add your preferred license here if you plan to distribute it publicly.

---


