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

## Benchmark status

The repository does not include a controlled RESTler comparison, and the
current labels are not independently verified. Do not present current results
as comparative performance or ground-truth accuracy measurements. Full runs
are resource-intensive; CI exposes them as a manual workflow separate from
push/pull-request tests.
