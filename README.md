# Adaptive Behavioral Fuzzer

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/Python-100%25-3776AB.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624.svg)](https://linux.org/)

**Adaptive Behavioral Fuzzer** is a research-oriented API fuzzing prototype designed to study whether execution-state deviations and runtime anomalies can expose potentially security-relevant behavior in synthetic REST API targets.

The system uses manifest-driven route selection, sandboxed benchmark execution, deterministic seed generation, structured request telemetry, behavioral detectors, and repeatable evaluation workflows. It includes a 100-target benchmark suite spanning authorization, boundary-condition, path-traversal, and input-validation scenarios.

> [!IMPORTANT]
> This project is intended for authorized research and testing only. A behavioral anomaly is **not automatically a vulnerability**. Detected findings must be independently reviewed and validated against a defined security property. Use only synthetic targets or systems where testing has been explicitly authorized.

## Key Capabilities

- **Manifest-driven benchmarks** — Executes a canonical inventory of 100 synthetic API targets.
- **Sandboxed execution** — Runs benchmark targets and local fuzzer workers inside separate Bubblewrap Linux namespaces.
- **Deterministic experiments** — Derives per-target seeds from a master seed and stable benchmark identifier.
- **Behavioral detection** — Supports statistical response analysis and an optional response-fingerprint detector.
- **Authorization scenarios** — Exercises selected owner-versus-other-user access patterns for synthetic BOLA fixtures.
- **Structured telemetry** — Preserves request-level JSONL events, process logs, reports, dashboards, and run identifiers.
- **Reproducible evaluation** — Validates report completeness and evaluates only independently verified labels.
- **CI/CD integration** — Includes automated tests, consistency checks, and a manually triggered benchmark workflow.

## Benchmark Inventory

The complete benchmark inventory is defined in [`research_benchmark/manifest.yaml`](research_benchmark/manifest.yaml).

| Benchmark category | Synthetic targets |
|---|---:|
| Broken Object Level Authorization (BOLA) | 25 |
| Boundary-condition cases | 25 |
| Path traversal and information-disclosure cases | 25 |
| Input-validation cases | 25 |
| **Total** | **100** |

The default configuration specifies 40 fuzzing iterations per target, a 10-second startup timeout, and a 90-second target wall-clock timeout. These values control benchmark execution; they do not represent real-world vulnerability prevalence or guaranteed detection performance.

## How It Works

1. The runner loads and validates the benchmark manifest.
2. A master seed produces deterministic, target-specific seeds.
3. Bubblewrap starts the benchmark target and fuzzer worker in isolated namespaces.
4. Route metadata is loaded from the manifest and supplemented by Swagger-assisted discovery.
5. Requests are mutated and sent against the target while response characteristics are recorded.
6. Statistical checks classify response deviations; fingerprint mode adds repeated-response analysis.
7. Request-level telemetry, process logs, reports, and dashboards are preserved by run ID.
8. The runner validates that each selected target produced exactly one completed report.

For component details and execution flow, see [`docs/architecture.md`](docs/architecture.md).

## Requirements

### Supported Environment

- Linux host, with Ubuntu or Debian recommended
- Python 3.11
- Bubblewrap (`bwrap`) installed and usable by the current user
- Git
- Python packages listed in [`requirements.txt`](requirements.txt)

Bubblewrap is Linux-specific. Native execution is not supported on Windows or macOS. A Linux virtual machine or Linux-based container may be used, subject to namespace permissions and host security policy.

### Ubuntu or Debian

```bash
sudo apt-get update
sudo apt-get install --yes python3.11 python3.11-venv python3-pip bubblewrap git

python3.11 --version
bwrap --version
```

Installing Bubblewrap does not guarantee that namespace creation is permitted by the host kernel, container runtime, or system security policy.

## Installation

```bash
git clone https://github.com/ogiwbuz188/adaptive-fuzzer.git
cd adaptive-fuzzer

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For test and development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Validate the local environment and benchmark metadata before an experiment:

```bash
python -m scripts.check_experiment_environment --json
python -m scripts.check_benchmark_labels
```

The label check verifies inventory consistency and allowed metadata values. It does not independently establish the vulnerability status of each target.

## Running the Benchmark

Run the complete 100-target benchmark:

```bash
python run_test.py --seed 1 --detector-mode statistical
```

Run a benchmark independently with multiple master seeds:

```bash
python run_test.py --seeds 1 2 3 --detector-mode statistical
```

Enable the optional response-fingerprint detector:

```bash
python run_test.py --seed 1 --detector-mode statistical+fingerprint
```

Run one target as a smoke test:

```bash
python run_test.py --seed 1 --benchmark-id missing_type_casts
```

Run a bounded subset:

```bash
python run_test.py --seed 1 --max-targets 5
```

Provide a stable run identifier:

```bash
python run_test.py --seed 1 --run-id local-smoke-001
```

Display all command-line options:

```bash
python run_test.py --help
```

> [!NOTE]
> The full suite executes serially and may take substantial time. Begin with a single-target smoke test before running the complete inventory.

## Validation and Evaluation

### Validate report completeness

```bash
python -m scripts.validate_dataset --run-id <run-id>
```

This command confirms that every selected target produced exactly one completed report. Report completeness does not imply detection accuracy or confirmed vulnerabilities.

### Generate anomaly plots

```bash
python notebook/generate_plots.py
```

Generated plots summarize recorded anomalies and response statuses. They must not be interpreted as independently confirmed vulnerability counts.

### Evaluate against verified labels

```bash
python -m scripts.evaluate_run --json <run-id>
```

The evaluator excludes labels unless `verification_status` is exactly `independently_verified`. The current benchmark metadata contains source-derived draft labels rather than an independently verified ground-truth dataset.

See [`docs/ground-truth.md`](docs/ground-truth.md) for the verification process and [`docs/benchmark-protocol.md`](docs/benchmark-protocol.md) for the experimental protocol.

## Output Structure

By default, run artifacts are written beneath `data/`:

| Path | Description |
|---|---|
| `data/raw/<run-id>.jsonl` | Versioned, request-level telemetry |
| `data/reports/<run-id>/` | Per-target reports and dashboards |
| `data/logs/<run-id>/` | Target and fuzzer process logs |
| `data/test_runs.csv` | Legacy anomaly summary records |

Retain the run ID, Git commit, master seed, detector mode, manifest, Python and dependency versions, operating system, and generated artifacts together for reproducibility.

## Reproducibility

The runner executes targets serially, uses fixed request budgets from the manifest, derives target-specific seeds from the master seed, and applies startup and wall-clock limits. Capture the environment before each experiment:

```bash
python -m scripts.check_experiment_environment --json
```

For multi-seed studies, preserve every run ID and output directory. Comparisons should use the same target inventory, request budget, detector configuration, and sufficiently similar execution environment.

## Research Status and Limitations

This repository is an evolving research prototype. Its current limitations include:

- **Ground truth is not independently verified.** Current labels are source-derived drafts and should not be presented as confirmed results.
- **Anomalies are not vulnerabilities.** Statistical deviations require additional evidence and security-property review.
- **Route discovery is limited.** The system uses manifest route metadata and Swagger-assisted discovery, rather than a complete OpenAPI parser or general-purpose service crawler.
- **Authorization coverage is selective.** Explicit owner/other-user checks cover configured synthetic BOLA fixtures only.
- **Sandboxing is process isolation, not a virtual machine.** Bubblewrap has a defined threat boundary and should not be assumed to safely execute arbitrary untrusted code.
- **The benchmark is synthetic.** Fixture behavior does not establish real-world vulnerability prevalence or production-system risk.
- **No controlled RESTler comparison is included.** See [`docs/restler-comparison.md`](docs/restler-comparison.md) for the proposed comparison protocol.
- **No full benchmark artifact is committed by default.** Full-run artifacts are generated separately through the benchmark workflow.

These limitations should be retained in research papers, reports, and presentations that use this project.

## Repository Structure

```text
.
├── .github/workflows/
│   ├── benchmark.yml              # Manually triggered benchmark workflow
│   └── tests.yml                  # Test and consistency workflow
├── docs/
│   ├── architecture.md
│   ├── benchmark-protocol.md
│   ├── ground-truth.md
│   ├── restler-comparison.md
│   └── sandbox-threat-model.md
├── notebook/
│   └── generate_plots.py
├── research_benchmark/
│   ├── manifest.yaml
│   ├── metadata/
│   └── 100 synthetic target directories
├── scripts/                        # Validation, evaluation, and environment tools
├── src/
│   ├── detectors/
│   ├── evaluation/
│   ├── execution/
│   ├── telemetry/
│   └── fuzzer.py
├── tests/
│   ├── unit/
│   └── integration/
├── LICENSE.md
├── requirements.txt
├── requirements-dev.txt
└── run_test.py
```

## Testing

Run the test suite:

```bash
python -m pytest
```

Run benchmark metadata consistency checks:

```bash
python -m scripts.check_benchmark_labels
python -m scripts.check_experiment_environment --json
```

## Contributing

Contributions are welcome. Before submitting a pull request:

1. Open an issue or clearly describe the proposed change.
2. Keep the manifest, labels, fixture implementations, and documentation synchronized.
3. Add or update tests for behavioral changes.
4. Run the test suite and metadata checks.
5. Do not classify a draft label as independently verified without the required evidence and review process.
6. Document changes that affect experimental comparability, sandbox assumptions, telemetry, or metrics.

## Development with AI-Assisted Tools

Development of this repository has used large language models and AI-assisted coding agents as software-development aids. Such tools may assist with code exploration, architecture brainstorming, implementation, testing, documentation, and defect analysis.

AI assistance does not replace engineering review or scientific validation. Generated code and text must be tested and reviewed by the project maintainers. For academic use, disclose AI assistance according to the policies of the relevant institution, conference, journal, or publisher.

## License

This project is licensed under the **Apache License, Version 2.0**. See [`LICENSE.md`](LICENSE.md) for the complete terms.

Copyright (c) 2026 Japneet Kaur ([ogiwbuz188](https://github.com/ogiwbuz188)).

## Citation

When using this repository in academic work, cite the exact release or commit used and record the benchmark manifest and experiment run IDs. Include:

- Project title and repository URL
- Author or maintainer name
- Release tag or Git commit hash
- Access date
- Benchmark manifest version
- Experiment run ID(s)

Do not claim validated detection accuracy unless labels have been independently reviewed and the corresponding evaluation has been completed.

## Project Origin

This project was created as a high school student research project. It is intended to demonstrate practical exploration of API security, software engineering, sandboxed experimentation, reproducibility, and responsible AI-assisted development. This README and the project as a whole are provided for educational and authorized research purposes; it is not a replacement for professional penetration testing or production security assurance.
