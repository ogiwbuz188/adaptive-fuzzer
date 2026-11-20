import csv
from pathlib import Path

from src.execution.manifest import load_manifest


ROOT = Path(__file__).resolve().parents[1]
LABEL_PATH = ROOT / "research_benchmark" / "metadata" / "labels.csv"
REVIEW_PATH = ROOT / "research_benchmark" / "metadata" / "independent_review_template.csv"


def derive_label(benchmark):
    if benchmark.authorization_scenarios:
        vulnerable = any(
            scenario.expected_vulnerable
            for scenario in benchmark.authorization_scenarios
        )
        status = "source_derived_draft"
        note = "Source-derived from benchmark authorization scenario; not independently reviewed."
    else:
        vulnerable = True
        status = "source_derived_draft"
        note = "Source-derived draft: synthetic target belongs to a vulnerability category; not independently reviewed."

    vulnerability_class = benchmark.category
    return vulnerable, status, vulnerability_class, note


def main():
    benchmarks = load_manifest(
        ROOT / "research_benchmark" / "manifest.yaml",
        ROOT,
    )
    with LABEL_PATH.open("w", newline="", encoding="utf-8") as labels_file:
        writer = csv.DictWriter(
            labels_file,
            fieldnames=[
                "benchmark_id",
                "category",
                "expected_vulnerable",
                "vulnerability_class",
                "verification_status",
                "notes",
            ],
        )
        writer.writeheader()
        for benchmark in benchmarks:
            vulnerable, status, vulnerability_class, note = derive_label(
                benchmark
            )
            writer.writerow(
                {
                    "benchmark_id": benchmark.benchmark_id,
                    "category": benchmark.category,
                    "expected_vulnerable": str(vulnerable).lower(),
                    "vulnerability_class": vulnerability_class,
                    "verification_status": status,
                    "notes": note,
                }
            )

    with REVIEW_PATH.open("w", newline="", encoding="utf-8") as review_file:
        writer = csv.DictWriter(
            review_file,
            fieldnames=[
                "benchmark_id",
                "source_derived_label",
                "reviewed_label",
                "reviewer_id_1",
                "reviewer_id_2",
                "evidence_reference",
                "review_status",
            ],
        )
        writer.writeheader()
        for benchmark in benchmarks:
            vulnerable, _, _, _ = derive_label(benchmark)
            writer.writerow(
                {
                    "benchmark_id": benchmark.benchmark_id,
                    "source_derived_label": str(vulnerable).lower(),
                    "reviewed_label": "",
                    "reviewer_id_1": "",
                    "reviewer_id_2": "",
                    "evidence_reference": "",
                    "review_status": "pending",
                }
            )

    print(
        f"Generated {len(benchmarks)} source-derived draft labels "
        f"and review rows."
    )


if __name__ == "__main__":
    main()
