import argparse
import csv
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert explicit RESTler benchmark mappings to detections.",
    )
    parser.add_argument("mapping_csv")
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)

    detections = {}
    finding_count = 0
    with Path(args.mapping_csv).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            benchmark_id = row["benchmark_id"].strip()
            evidence = row["evidence_reference"].strip()
            restler_finding = row["restler_finding_id"].strip()
            status = row["finding_status"].strip().lower()
            if not benchmark_id or not evidence or not restler_finding:
                raise ValueError(
                    "RESTler mappings require benchmark_id, finding_id, and evidence"
                )
            if status not in {"detected", "not_detected"}:
                raise ValueError(
                    f"Invalid finding_status for {benchmark_id}: {status}"
                )
            detections[benchmark_id] = status == "detected"
            finding_count += 1

    if not detections:
        raise ValueError("RESTler mapping is empty")
    document = {
        "tool": "RESTler",
        "finding_count": finding_count,
        "detections": detections,
    }
    serialized = json.dumps(document, indent=2, sort_keys=True)
    if args.json_output:
        Path(args.json_output).write_text(serialized, encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
