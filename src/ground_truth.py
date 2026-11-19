import csv
from pathlib import Path


def load_labels(path="research_benchmark/metadata/labels.csv"):
    labels = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            benchmark_id = row["benchmark_id"]
            labels[benchmark_id] = {
                "vulnerable": row["expected_vulnerable"].lower() == "true",
                "class": row["vulnerability_class"],
                "verification_status": row["verification_status"],
            }

    if not labels:
        raise RuntimeError("Ground-truth label file is empty")

    return labels


def calculate_metrics(labels, detections):
    tp = fp = tn = fn = 0

    for benchmark_id, label in labels.items():
        actual = label["vulnerable"]
        predicted = detections.get(benchmark_id, False)

        if actual and predicted:
            tp += 1
        elif not actual and predicted:
            fp += 1
        elif not actual and not predicted:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
