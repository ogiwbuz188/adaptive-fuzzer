import json
import math
from pathlib import Path


INFRASTRUCTURE_ANOMALIES = {
    "CONNECTION_ERROR",
    "CONNECTION_DATA_FAULT",
    "RUN_FAILED",
}


class EvaluationError(ValueError):
    pass


def _wilson_interval(successes, total, confidence=0.95):
    if total == 0:
        return (0.0, 0.0)
    z = 1.96 if confidence == 0.95 else 1.0
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (
        proportion + z * z / (2 * total)
    ) / denominator
    radius = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total
            + z * z / (4 * total * total)
        )
        / denominator
    )
    return (max(0.0, centre - radius), min(1.0, centre + radius))


def detections_from_telemetry(path, run_id=None, include_negatives=False):
    detections = {}
    anomaly_counts = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise EvaluationError(
                    f"Invalid telemetry JSON at {path}:{line_number}"
                ) from error
            if run_id is not None and event.get("run_id") != run_id:
                continue
            benchmark_id = event.get("benchmark_id")
            if not benchmark_id:
                continue
            if include_negatives:
                detections.setdefault(benchmark_id, False)
            anomalies = {
                str(item)
                for item in event.get("anomalies", [])
                if str(item) not in INFRASTRUCTURE_ANOMALIES
            }
            if anomalies:
                detections[benchmark_id] = True
                for anomaly in anomalies:
                    anomaly_counts[anomaly] = (
                        anomaly_counts.get(anomaly, 0) + 1
                    )
    return detections, anomaly_counts


def evaluate_verified_predictions(labels, detections):
    unassigned = [
        benchmark_id
        for benchmark_id, label in labels.items()
        if label.get("vulnerable") is None
    ]
    unverified = [
        benchmark_id
        for benchmark_id, label in labels.items()
        if label.get("verification_status") != "independently_verified"
    ]
    if unassigned or unverified:
        raise EvaluationError(
            "Cannot calculate accuracy: "
            f"{len(unassigned)} labels are unassigned and "
            f"{len(unverified)} labels are not independently verified"
        )

    missing = set(labels) - set(detections)
    missing_telemetry = [
        benchmark_id
        for benchmark_id in labels
        if benchmark_id not in detections
    ]
    if missing_telemetry:
        raise EvaluationError(
            "Cannot calculate accuracy: missing telemetry predictions for "
            f"{len(missing_telemetry)} benchmark(s): "
            + ", ".join(sorted(missing_telemetry))
        )

    tp = fp = tn = fn = 0
    categories = {}
    for benchmark_id, label in labels.items():
        actual = label["vulnerable"]
        predicted = bool(detections.get(benchmark_id, False))
        category = str(label.get("class") or "unclassified")
        category_metrics = categories.setdefault(
            category,
            {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        )

        if actual and predicted:
            tp += 1
            category_metrics["tp"] += 1
        elif not actual and predicted:
            fp += 1
            category_metrics["fp"] += 1
        elif not actual and not predicted:
            tn += 1
            category_metrics["tn"] += 1
        else:
            fn += 1
            category_metrics["fn"] += 1

    overall = _classification_metrics(tp, fp, tn, fn)
    per_category = {
        category: _classification_metrics(
            values["tp"],
            values["fp"],
            values["tn"],
            values["fn"],
        )
        for category, values in sorted(categories.items())
    }
    return {
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
        "metrics": overall,
        "per_category": per_category,
        "evaluated": len(labels),
        "missing_predictions": sorted(missing),
    }


def _classification_metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": 1.0 - specificity,
        "specificity": specificity,
        "precision_ci95": list(_wilson_interval(tp, tp + fp)),
        "recall_ci95": list(_wilson_interval(tp, tp + fn)),
    }
