# Benchmark protocol

## Inventory and execution

`research_benchmark/manifest.yaml` is the authoritative target inventory. It
defines stable IDs, entrypoints, route/method settings, fuzz request budgets,
startup and wall-clock timeouts, and any target-specific authorization
scenarios. The manifest and the label file are checked for matching benchmark
IDs by `python -m scripts.check_benchmark_labels`.

The default invocation runs the full inventory sequentially:

```bash
python run_test.py --seed 1 --detector-mode statistical
```

Repeat the selected inventory with independent master seeds:

```bash
python run_test.py --seeds 1 2 3 --detector-mode statistical
```

Run the semantic-only, statistical, and statistical-plus-fingerprint modes
with matching seeds and manifest budgets:

```bash
python -m scripts.run_detector_ablation --seeds 1,2,3
```

The wrapper records separate run IDs for each mode. Evaluate those runs
individually and aggregate their evaluation JSON files with
`python -m scripts.aggregate_evaluations <run-1.json> <run-2.json> ...`.
Evaluation remains unavailable until labels are independently verified.

For a bounded local smoke test, select one target:

```bash
python run_test.py --seed 1 --benchmark-id missing_type_casts
```

Each target gets a seed derived from the master seed and its stable benchmark
ID. The report records that target seed. The request budget, startup timeout,
and wall-clock timeout come from the manifest (currently 40 iterations, a
10-second startup timeout, and a 90-second target timeout). The runner sets
per-process limits: 60 seconds of CPU time (61-second hard limit), 1 GiB of
address space, 100 MiB maximum file size, 128 open files, and no core dumps.
These are per-process limits, not aggregate quotas across a process tree.

Use a unique run ID when rerunning with the same data directory. The CLI
generates one by default and prints it before execution; it can also be supplied
explicitly with `--run-id`. A run's reports and logs are isolated in run-ID
subdirectories, while telemetry is written to a run-ID JSONL file and the
legacy summary CSV is appended.

## Completion and retained artifacts

The CLI validates that the selected target set has exactly one report per
target and that every report is marked completed. An unsuccessful run exits
nonzero. For direct validation after a run:

```bash
python -m scripts.validate_dataset --run-id <run-id>
```

Retain the commit, Python and dependency versions, master seed, run ID, selected
detector mode, manifest, and outputs with any reported result. Compare runs
only when their target inventory, budgets, environment, and detector
configuration are compatible. Fixed seeds do not eliminate timing, scheduling,
or platform variation.

`run_test.py` writes the full source, Python, package, kernel, Bubblewrap,
hardware, seed, and detector provenance to `data/run_manifest.json` before
starting each run. Use `python -m scripts.check_experiment_environment --json`
to print an additional environment snapshot. Use
`python -m scripts.evaluate_run --json <run-id>` only after independent
ground-truth labels are marked `independently_verified`.

## Benchmark status

The repository does not include a controlled RESTler comparison, and the
current labels are not independently verified. Do not present current results
as comparative performance or ground-truth accuracy measurements. Full runs
are resource-intensive; CI exposes them as a manual workflow separate from
push/pull-request tests.
