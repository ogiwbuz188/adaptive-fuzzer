import csv
from pathlib import Path
import argparse

from src.ground_truth import load_labels


ROOT = Path(__file__).resolve().parents[1]
LABEL_PATH = ROOT / "research_benchmark" / "metadata" / "labels.csv"
REVIEW_PATH = ROOT / "research_benchmark" / "metadata" / "independent_review_template.csv"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Promote human-reviewed labels only from a completed review CSV.",
    )
    parser.add_argument(
        "--review",
        default=str(REVIEW_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(LABEL_PATH),
    )
    args = parser.parse_args(argv)

    labels = load_labels(LABEL_PATH)
    category_by_id = {}
    with LABEL_PATH.open(newline="", encoding="utf-8") as label_file:
        for row in csv.DictReader(label_file):
            category_by_id[row["benchmark_id"]] = row["category"]
    promoted = 0
    with Path(args.review).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["review_status"].strip().lower() != "approved":
                continue
            benchmark_id = row["benchmark_id"].strip()
            if benchmark_id not in labels:
                raise ValueError(f"Unknown benchmark ID: {benchmark_id}")
            reviewed = row["reviewed_label"].strip().lower()
            reviewer_1 = row["reviewer_id_1"].strip()
            reviewer_2 = row["reviewer_id_2"].strip()
            evidence = row["evidence_reference"].strip()
            if reviewed not in {"true", "false"}:
                raise ValueError(
                    f"Invalid independent label for {benchmark_id}"
                )
            if not reviewer_1 or not reviewer_2 or reviewer_1 == reviewer_2:
                raise ValueError(
                    f"Two distinct reviewers are required for {benchmark_id}"
                )
            if not evidence:
                raise ValueError(
                    f"Evidence reference is required for {benchmark_id}"
                )
            labels[benchmark_id]["vulnerable"] = reviewed == "true"
            labels[benchmark_id]["verification_status"] = (
                "independently_verified"
            )
            labels[benchmark_id]["notes"] = (
                f"Independently reviewed by {reviewer_1} and {reviewer_2}; "
                f"evidence: {evidence}"
            )
            promoted += 1

    fieldnames = [
        "benchmark_id",
        "category",
        "expected_vulnerable",
        "vulnerability_class",
        "verification_status",
        "notes",
    ]
    with Path(args.output).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for benchmark_id, label in labels.items():
            writer.writerow(
                {
                    "benchmark_id": benchmark_id,
                    "category": category_by_id[benchmark_id],
                    "expected_vulnerable": (
                        ""
                        if label["vulnerable"] is None
                        else str(label["vulnerable"]).lower()
                    ),
                    "vulnerability_class": label["class"],
                    "verification_status": label["verification_status"],
                    "notes": label["notes"],
                }
            )

    print(f"Promoted {promoted} independently reviewed labels.")


if __name__ == "__main__":
    main()
