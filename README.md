Adaptive Behavioral Fuzzer


[!\[License: Apache-2.0\]\(https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE.md)

Adaptive Behavioral Fuzzer is a research prototype for executing a controlled inventory of synthetic API benchmark programs in bounded Linux sandboxes, exercising selected cross-user authorization scenarios, and collecting request-level telemetry. It combines statistical response-deviation checks with an optional response-fingerprint detector.
Research-use notice: This project is intended for academic research, experimentation, and evaluation on the synthetic benchmark targets included in this repository or on systems for which you have explicit authorization. It is not a validated general-purpose security scanner, penetration-testing product, or guarantee of vulnerability detection. Do not run it against third-party services without permission.

Contents
- Project goals
- What is implemented
- Benchmark inventory
- How it works
- Requirements
- Installation
- Running the benchmark
- Validating and evaluating results
- Outputs
- Reproducibility
- Research status and limitations
- Development with LLMs and coding agents
- Repository structure
- Contributing
- License
- Citation
Project goals
The project explores whether endpoint-specific behavioral deviations can provide useful signals during repeatable API security experiments. Its goals are to:
1. Run a manifest-defined set of synthetic API targets under bounded Linux isolation.
2. Exercise request mutation and collect structured, request-level observations.
3. Compare response behavior against endpoint baselines using statistical heuristics.
4. Optionally use response fingerprints as an additional anomaly signal.
5. Exercise explicitly configured owner/other-user authorization scenarios.
6. Preserve run identifiers, seeds, logs, reports, and telemetry to support later analysis.
The detector reports behavioral anomalies. An anomaly is not automatically a security vulnerability. Security conclusions require evidence of a violated security property and independently reviewed benchmark ground truth.
What is implemented
- Manifest-driven benchmark execution. [`research_benchmark/manifest.yaml`](research_benchmark/manifest.yaml) is the canonical inventory. It defines stable target IDs, Python entrypoints, HTTP routes and methods, ports, request budgets, timeouts, and any configured authorization scenarios.
- Serial sandboxed runner. [`run_test.py`](run_test.py) runs selected targets sequentially. Each target and its local fuzzer worker execute inside a separate Bubblewrap namespace. The sandbox uses private networking, read-only mounts for project source and benchmark code, a writable data mount, and process resource limits. The runner fails if Bubblewrap is unavailable or unusable; it does not silently fall back to an ordinary subprocess.
- Two detector configurations. statistical is the default. statistical+fingerprint enables the optional response-fingerprint detector in addition to statistical checks. The statistical implementation includes robust median absolute deviation (MAD) checks and endpoint baseline-drift checks.
- Selected BOLA fixtures. Two synthetic owner-versus-other-user scenarios exercise the same known object with distinct credentials. One fixture permits cross-user access and the other denies it. The check is limited to these explicitly configured scenarios; it is not a general authorization model or proof of BOLA coverage across arbitrary APIs.
- Structured telemetry and reports. Request-level JSONL events are written under data/raw/; per-target dashboards are written under data/reports/<run-id>/; process logs are written under data/logs/<run-id>/; and a legacy anomaly CSV is maintained at data/test_runs.csv.
- Dataset and label checks. Scripts check manifest/label inventory consistency and verify that a run has exactly one completed report for every selected target.
- Evaluation safeguards. The evaluation pipeline only includes labels whose verification status is independently_verified. Draft labels are excluded from accuracy metrics.
- Experiment utilities. The repository includes tools for recording environment information, evaluating a run, aggregating evaluation outputs, and preparing explicit mappings for a future RESTler comparison.
Benchmark inventory
The manifest contains 100 synthetic targets, organized into four groups of 25:
Benchmark group	Targets
Broken Object Level Authorization (BOLA)	25
Boundary-condition cases	25
Path traversal and information-disclosure cases	25
Input-validation cases	25
Total	100


The manifest currently configures 40 fuzzing iterations per target, a 10-second startup timeout, and a 90-second target wall-clock timeout. These are benchmark configuration values, not a claim that every request or target completes successfully. See [`docs/benchmark-protocol.md`](docs/benchmark-protocol.md) for the run protocol.

The benchmark programs are synthetic research fixtures. Category names and target names describe intended test themes; they do not establish real-world vulnerability prevalence or independently verified vulnerability labels.
How it works
At a high level, a run follows this sequence:
1. Load and validate the manifest. The runner reads the selected target definitions and validates requested benchmark IDs.
2. Derive per-target seeds. A target seed is deterministically derived from the master seed and stable benchmark ID.
3. Start the isolated target. The runner launches the target and local fuzzer in a Bubblewrap namespace and waits for service readiness.
4. Discover route metadata. The current implementation uses the manifest route and Swagger-assisted discovery. It is not a complete OpenAPI parser or general microservice crawler.
5. Establish response baselines and exercise requests. The fuzzer sends the configured requests and records response characteristics.
6. Classify behavioral deviations. Statistical checks identify response deviations; the optional fingerprint mode adds repeated-response fingerprint signals. Configured BOLA fixtures are evaluated through their explicit owner/other-user scenario.
7. Write evidence artifacts. Telemetry, target reports, and process logs are stored using the run ID.
8. Validate run completion. The CLI checks that each selected target has one completed report and exits unsuccessfully if targets or reports fail.
For implementation details, see [`docs/architecture.md`](docs/architecture.md).
Requirements
Supported environment
- Linux host (Ubuntu or Debian is a convenient starting point).
- Python 3.11 (the CI workflows are configured for Python 3.11).
- Bubblewrap (bwrap) installed and usable by the current user.
- Git, for cloning the repository and recording the source revision.
- Python dependencies listed in requirements.txt or requirements-dev.txt.
Bubblewrap is Linux-specific. Running the project under Windows or macOS directly is not supported by the sandbox runner. A Linux virtual machine is an option where a native Linux host is unavailable, provided Bubblewrap and the required namespace features are enabled inside that VM.
System dependencies
On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install --yes python3.11 python3.11-venv python3-pip bubblewrap git
Your distribution may provide Python 3.11 under a versioned package name or may require installation from its supported package source. Confirm that python3.11 and bwrap are available:
python3.11 --version
bwrap --version
Bubblewrap can be restricted by host security policy, container configuration, or kernel settings. Installing the executable alone does not guarantee that it can create the namespaces this project needs.
Installation
Clone the repository and enter its directory:
git clone https://github.com/ogiwbuz188/adaptive-fuzzer.git
cd adaptive-fuzzer
Create and activate a virtual environment:
python3.11 -m venv .venv
source .venv/bin/activate
Install the development dependencies (this also installs the runtime dependencies):
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
For runtime-only use, install:
python -m pip install -r requirements.txt
Check the experiment environment and validate manifest/label inventory consistency:
python -m scripts.check_experiment_environment --json
python -m scripts.check_benchmark_labels
The label check validates inventory consistency and allowed metadata values. It does not independently verify the expected vulnerability status of each target.
Running the benchmark
Run the full 100-target inventory with a master seed and the default statistical detector:
python run_test.py --seed 1 --detector-mode statistical
Run the inventory independently with multiple master seeds:
python run_test.py --seeds 1 2 3 --detector-mode statistical
Enable the optional response-fingerprint detector:
python run_test.py --seed 1 --detector-mode statistical+fingerprint
Run one target as a sandboxed smoke test:
python run_test.py --seed 1 --benchmark-id missing_type_casts
Run a bounded subset of the manifest:
python run_test.py --seed 1 --max-targets 5
The runner prints a run ID. You can provide your own unique run ID with --run-id:
python run_test.py --seed 1 --run-id local-smoke-001
The available command-line options can also be viewed with:
python run_test.py --help
Resource note: A full run may take a substantial amount of time because targets are executed serially and each target has its own startup and execution limits. Start with a single-target smoke test before launching the complete suite.
Validating and evaluating results
Validate report completeness
After a run, substitute the run ID printed by the runner:
python -m scripts.validate_dataset --run-id <run-id>
Validation checks that each selected target has exactly one completed report. A successful report-completeness check is not a detection-accuracy result.
Inspect anomaly summaries
Generate plots from the recorded anomaly CSV:
python notebook/generate_plots.py
These plots summarize recorded anomalies and response statuses. They must not be described as counts of independently confirmed vulnerabilities.
Evaluate against independently verified labels
The evaluation command is:
python -m scripts.evaluate_run --json <run-id>
The evaluator excludes labels unless verification_status is exactly independently_verified. The current research_benchmark/metadata/labels.csv contains source-derived draft labels pending independent review; therefore, the repository's current label set does not support meaningful precision, recall, F1-score, or confusion-matrix claims. The evaluator is designed to refuse unsupported accuracy reporting rather than treating draft labels as ground truth.

See [`docs/ground-truth.md`](docs/ground-truth.md) for the label-review process and [`docs/benchmark-protocol.md`](docs/benchmark-protocol.md) for the experimental protocol.
Outputs
By default, run artifacts are written under data/:
Path	Contents
data/raw/<run-id>.jsonl	Versioned request-level telemetry
data/reports/<run-id>/	Per-target reports and dashboards
data/logs/<run-id>/	Target and worker process logs
data/test_runs.csv	Legacy anomaly summary CSV


Keep the run ID, Git commit, master seed, detector mode, manifest, Python version, dependency versions, operating system, and generated artifacts together when retaining or sharing experimental results. Review telemetry and logs for sensitive information before publishing or uploading them.
Reproducibility
The runner executes targets serially, uses a fixed per-target request budget from the manifest, derives target seeds from the master seed and benchmark ID, and enforces startup and wall-clock timeouts. These controls support repeatable experiment configuration, but they do not make response timing, operating-system scheduling, or host behavior deterministic.

Capture the environment before an experiment:
python -m scripts.check_experiment_environment --json
For multi-seed studies, preserve each run's ID and outputs. Compare results only when the target inventory, request budgets, detector configuration, and execution environment are sufficiently aligned. Consult [`docs/benchmark-protocol.md`](docs/benchmark-protocol.md) before interpreting results.
Research status and limitations
This repository is an evolving research prototype. The following limitations are important when interpreting its outputs:
- Ground truth is not independently verified. All 100 label rows currently contain source-derived draft labels. The independent-review template provides for two distinct reviewers and evidence references. Until labels are independently verified, the evaluator excludes them and the project cannot support measured precision, recall, or F1 claims.
- No controlled RESTler comparison is included. RESTler is not distributed with this repository, and no controlled comparative results are reported. [`docs/restler-comparison.md`](docs/restler-comparison.md) describes the intended comparison protocol and mapping workflow.
- Behavioral anomalies are not synonymous with vulnerabilities. Latency changes, response-size changes, status changes, content-type mismatches, and repeated fingerprints are signals requiring interpretation. A security finding requires evidence that a security property was violated.
- Route discovery is limited. The runner uses manifest-defined route information and Swagger-assisted discovery. It is not a complete OpenAPI implementation, automatic multi-service crawler, or general stateful API dependency discovery engine.
- Authorization coverage is selective. The explicit owner/other-user checks cover the two configured synthetic BOLA scenarios; they do not generalize to every object model, role, tenant, or authentication scheme.
- Sandboxing has a defined threat boundary. Bubblewrap provides namespace-based process isolation, not a virtual machine or proof that arbitrary hostile code is safe. Per-process resource limits are applied; aggregate cgroup controls are best-effort when the host exposes a usable cgroup v2 hierarchy. No dedicated seccomp policy is installed by the current implementation. Review [`docs/sandbox-threat-model.md`](docs/sandbox-threat-model.md) before adding untrusted benchmark programs.
- Synthetic benchmark scope. The benchmark fixtures do not establish real-world vulnerability prevalence, and results from this suite should not be generalized to production microservices without additional evaluation.
- No full benchmark artifact is committed by default. The repository includes a manually triggered GitHub Actions workflow for full runs; it is separate from the push/pull-request test workflow because full runs can be resource intensive.
These limitations are part of the current research status and should be retained in papers, reports, and presentations that use this software.
Development with LLMs and coding agents
Development of this repository has used large language models (LLMs) and AI-assisted coding agents as software-development aids. Depending on the task, these tools have assisted with activities such as:
- exploring and explaining the existing codebase;
- brainstorming architecture and implementation approaches;
- drafting or refining Python code and configuration;
- generating and improving unit or integration tests;
- identifying potential defects and edge cases;
- improving documentation, experiment descriptions, and developer workflows.
AI assistance does not replace engineering review or scientific validation. Generated or suggested code and text must be reviewed, tested, and checked by the project maintainers. The maintainers remain responsible for the correctness, security, provenance, licensing compatibility, and research claims of the published repository. No particular LLM provider, model, or agent version is implied by this general disclosure; record exact tools and versions in an experiment or publication when they are relevant and known.

For academic use, authors should disclose AI assistance in accordance with the target institution, conference, journal, and publisher policies. LLM-generated content must not be treated as an independent reviewer, ground-truth authority, or source of experimental evidence. Benchmark labels require independent human review as described in [`docs/ground-truth.md`](docs/ground-truth.md).
Repository structure
.
├── .github/workflows/
│   ├── benchmark.yml              # Manually triggered full benchmark workflow
│   └── tests.yml                  # Push/PR test and consistency checks
├── docs/
│   ├── architecture.md            # Components and execution flow
│   ├── benchmark-protocol.md       # Run configuration and reproducibility
│   ├── ground-truth.md             # Label verification policy
│   ├── restler-comparison.md       # Proposed baseline comparison protocol
│   └── sandbox-threat-model.md     # Isolation boundary and limitations
├── notebook/
│   └── generate_plots.py           # Plot generation from anomaly summaries
├── research_benchmark/
│   ├── manifest.yaml               # Canonical 100-target inventory
│   └── metadata/                   # Draft labels and comparison mappings
├── scripts/                        # Validation, evaluation, and experiment tools
├── src/
│   ├── detectors/                  # Statistical, fingerprint, and BOLA checks
│   ├── execution/                  # Manifest, runner, sandbox, and worker
│   ├── telemetry/                  # Versioned event schema and JSONL writer
│   ├── evaluation/                 # Detection aggregation and metrics
│   └── fuzzer.py                   # Request mutation and detection coordination
├── tests/
│   ├── unit/
│   └── integration/
├── LICENSE.md                      # Apache License 2.0
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Runtime and development/test dependencies
└── run_test.py                      # Benchmark command-line entry point
Contributing
Issues, reproducible bug reports, documentation improvements, and research extensions are welcome. Before submitting a change:
1. Open an issue or describe the intended change in the pull request.
2. Keep benchmark changes synchronized across the manifest, labels, and relevant documentation.
3. Add or update tests for behavioral changes.
4. Run the test suite and metadata checks:
   python -m pytest
   python -m scripts.check_benchmark_labels
5. Do not mark labels as independently verified without the review evidence and process required by [`docs/ground-truth.md`](docs/ground-truth.md).
6. Document changes that affect experiment comparability, sandbox assumptions, telemetry schema, or reported metrics.
License
This project is distributed under the Apache License, Version 2.0. The full license text is available in [`LICENSE.md`](LICENSE.md). You may use, reproduce, modify, and distribute the project subject to the terms and conditions of that license. The license also contains conditions concerning notices, attribution, patent rights, and redistribution.

Unless a separate notice says otherwise, contributions to this repository are intended to be provided under the same project license. Review the license text for the complete terms. Third-party dependencies and external tools remain subject to their own licenses and terms.
Citation
If you use this repository in academic work, please cite the specific release or commit you used. A citation record can be added once the project has a stable release and the authors have finalized the preferred citation metadata. At minimum, record:
- project title and repository URL;
- author or maintainer name(s);
- release tag or Git commit hash;
- access date;
- benchmark manifest version and experiment run IDs.
Do not cite the software as having validated detection accuracy unless the corresponding labels have been independently verified and the reported evaluation has actually been conducted.
