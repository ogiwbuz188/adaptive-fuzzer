# Ground truth and labels

`research_benchmark/metadata/labels.csv` contains one row for each of the 100
manifest benchmark IDs. Row coverage is a metadata consistency check, not
evidence that the labels themselves are correct.

Current status:

- All 100 targets have source-derived draft labels.
- Source-derived labels are preliminary and not independent verification.
- The independent-review template contains one row for every target.
- No target is marked `independently_verified` until two distinct reviewers
  approve it with an evidence reference.

[`calculate_metrics`](../src/ground_truth.py) includes a row only when it has an assigned
expected label and `verification_status` is exactly
`independently_verified`. It reports evaluated and excluded counts alongside
the confusion-matrix values and metrics. With the current file, all 100 rows
are excluded; the returned numeric metric values must not be interpreted as
measured accuracy.

The two owner-versus-other-user BOLA targets are useful executable fixtures:
one permits cross-user access and one rejects it. Their expected behavior is
defined by the synthetic programs and manifest scenarios; this is not
independent verification of the benchmark labels. Do not change their review
status without a documented independent assessment.

To check manifest/label row coverage and allowed label values:

```bash
python -m scripts.check_benchmark_labels
```

Passing this consistency check does not verify expected outcomes or produce a
research-ready ground-truth set.
