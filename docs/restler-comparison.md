# RESTler comparison protocol

RESTler is not distributed with this repository and is not required by the
default test suite. The repository therefore cannot claim a RESTler comparison
until a compatible RESTler executable and generated configuration are supplied.

To prepare a controlled comparison:

1. Record the environment with
   `python -m scripts.check_experiment_environment --json`.
2. Run every target on the same inventory, seed set, time budget, and host.
3. Preserve raw RESTler logs and its exact configuration in a run-ID directory.
4. Map each RESTler finding explicitly through
   `research_benchmark/metadata/restler_mapping_template.csv`.
5. Convert the mapping with
   `python -m scripts.convert_restler_findings <mapping.csv> --json-output <output.json>`.
6. Compare against independently verified labels using
   `python -m scripts.evaluate_run --json <run-id>`.

Do not map RESTler console text or HTTP anomalies to vulnerabilities without
an explicit finding-to-benchmark mapping. Console text alone is not a
ground-truth result.
