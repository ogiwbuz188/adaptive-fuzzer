# Architecture

## Run flow

1. `run_test.py` loads and validates the canonical manifest.
2. The CLI selects the requested targets and derives a stable per-target seed
   from the master seed and benchmark ID.
3. `BenchmarkRunner` launches Bubblewrap once per target. The target service and
   fuzzer share that target's private network namespace, allowing local HTTP
   requests while preventing ordinary network access to the host or outside
   services.
4. The sandbox worker starts the benchmark service, waits for its configured
   route, then runs the fuzzer and any declared authorization scenario.
5. The runner records stdout/stderr and writes a failed report on runner failure
   or timeout. After all selected targets finish, report validation requires
   exactly one completed dashboard per selected target.

The runner is serial, and configured fuzzing uses one worker. A fixed seed and
fixed request budget make request generation reproducible; they do not
guarantee identical timing or responses across hosts.

## Detection modes

- `semantic-only` flags HTTP 500 responses and stack/fatal trace markers only.
- `statistical` runs the statistical response anomaly detector.
- `statistical+fingerprint` additionally runs the response-fingerprint
  detector.

Fingerprinting is opt-in and is not part of the default statistical-only run.
For path-traversal targets, the sandbox additionally mounts a per-run random
canary at `/tmp/canary_secret.txt`; the path oracle flags responses containing
that exact token. This detects disclosure only when a response contains the
canary and does not by itself establish vulnerability ground truth. All modes
produce observations about benchmark responses, not verified vulnerability
labels.

## BOLA scenario flow

A manifest scenario identifies a known object, its route and method, and two
different credential headers representing an owner and another user. The probe
compares the responses to that same object and confirms its identity in both
responses before reporting access by the other user. The local scenarios are
fixtures: one intentionally exposes an object and one returns a forbidden
response. They do not establish independently reviewed ground truth.

## Outputs

For run ID `<run-id>` and data directory `data/`:

- `data/reports/<run-id>/` contains one dashboard per target.
- `data/logs/<run-id>/` contains target-specific stdout and stderr logs.
- `data/raw/<run-id>.jsonl` contains versioned request events with optional
  payload samples and response snippets, each capped at 512 UTF-8 bytes.
- `data/test_runs.csv` contains the legacy anomaly-summary rows used by the
  plotting script.

The report validator checks selected target coverage and the completed status
marker. It does not evaluate detection quality, labels, or telemetry validity.
