# Adaptive Behavioral Fuzzer

An experimental research prototype for running synthetic API benchmarks under
bounded Linux isolation, testing selected cross-user authorization scenarios,
and recording request-level telemetry. It is not a validated general-purpose
security scanner.

## What is implemented

- [research_benchmark/manifest.yaml](research_benchmark/manifest.yaml) is the
  canonical inventory of 100 targets, with stable IDs, entrypoints, routes,
  methods, budgets, timeouts, and any defined authorization scenarios.
- [run_test.py](run_test.py) runs targets serially with one fuzzer worker. Each
  target and its local fuzzer run inside a separate Bubblewrap namespace with
  private networking, read-only source mounts, a writable run-data mount, and
  CPU, address-space, file-size, and descriptor limits. A missing or unusable
  Bubblewrap executable is an error; the runner never silently falls back to
  ordinary subprocess execution.
- The statistical detector and optional response-fingerprint detector are
  distinct configurations: `statistical` and
  `statistical+fingerprint`. The default run is statistical-only.
- Two BOLA benchmark scenarios use explicit owner and other-user credentials
  for the same known object. The first target intentionally permits the second
  user; the second denies access. The detector is read-only and requires the
  response to identify the requested object.
- The fuzzer records request-level JSONL events under `data/raw/`, dashboards
  under `data/reports/<run-id>/`, process logs under `data/logs/<run-id>/`, and
  its legacy anomaly CSV under `data/test_runs.csv`.
- Dataset validation checks that every manifest target has exactly one
  completed report for a run. Failed or missing reports fail validation.

## Limitations and research status

- Bubblewrap isolation is Linux-specific and is not a virtual machine or a
  defense against kernel vulnerabilities. It limits visible host paths,
  disables network access outside the private namespace, and applies per-process
  resource limits. See [docs/sandbox-threat-model.md](docs/sandbox-threat-model.md).
- The runner currently uses simple manifest schemas and Swagger discovery; it
  is not a complete OpenAPI implementation. Results may depend on target and
  host behavior even when the seed is fixed.
- The statistical detector now includes robust MAD checks and endpoint baseline
  drift checks, while preserving separate opt-in fingerprint detection.
- Label rows cover all 100 targets with source-derived draft labels, but all
  remain pending independent review. Metrics exclude non-verified labels, so
  the repository currently cannot support a meaningful precision, recall, or
  F1 claim.
- No RESTler integration or controlled comparison is implemented. RESTler is
  not installed in the current environment, and no comparative results are
  reported.
- BOLA ground-truth labels remain pending independent review; the negative
  control label now matches the manifest and executable behavior.
- No complete 100-target run is included in the repository. The manual
  benchmark workflow is configured but has not been run on GitHub Actions.
- The benchmark programs are synthetic examples. Their names and responses do
  not establish real-world vulnerability prevalence.

## Setup

Linux, Bubblewrap, and the project dependencies are required. Python 3.11 is
the version configured for CI:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Validate and test

```bash
python -m pytest
python -m scripts.check_benchmark_labels
```

The test workflow runs these checks on pushes and pull requests. The full
benchmark is a separate manual workflow because targets can be resource
intensive.

## Run benchmarks

Run the complete inventory with an explicit seed and detector configuration:

```bash
python run_test.py --seed 1 --detector-mode statistical
```

Repeat the same inventory with multiple independent master seeds:

```bash
python run_test.py --seeds 1 2 3 --detector-mode statistical
```

Run a single target as a sandboxed smoke test:

```bash
python run_test.py --seed 1 --benchmark-id missing_type_casts
```

The CLI prints a run ID. Reports and logs are stored in run-ID directories;
telemetry is named with the run ID. To check report completeness:

```bash
python -m scripts.validate_dataset --run-id <run-id>
```

Generate plots from the anomaly CSV:

```bash
python notebook/generate_plots.py
```

Plots summarize recorded anomalies and statuses; they do not represent
independently verified vulnerability counts.

## Repository layout

```text
src/
  detectors/                 Statistical, response-fingerprint, and BOLA checks
  execution/                 Manifest loading, Bubblewrap runner, sandbox worker
  telemetry/                 Versioned request-event schema and JSONL writer
  fuzzer.py                  Request mutation, detection coordination, dashboard
research_benchmark/
  manifest.yaml              Canonical 100-target run inventory
  metadata/labels.csv        Explicit labels; unverified labels remain pending
scripts/
  check_benchmark_labels.py
  validate_dataset.py
tests/
  unit/
  integration/
notebook/generate_plots.py
```

## Reproducibility and protocol

Each run records the seed, benchmark ID, run ID, and detector mode in request
events and reports. The runner is serial, uses a fixed per-target request
budget, and enforces a wall-clock timeout. These controls improve repeatability
but do not make response timings or host scheduling deterministic. See
[docs/benchmark-protocol.md](docs/benchmark-protocol.md) and
[docs/ground-truth.md](docs/ground-truth.md) before interpreting results.
