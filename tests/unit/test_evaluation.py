import json

import pytest

from src.evaluation import (
    EvaluationError,
    detections_from_telemetry,
    evaluate_verified_predictions,
)


def test_evaluation_refuses_incomplete_ground_truth():
    labels = {
        "a": {"vulnerable": None, "class": "A", "verification_status": "unreviewed"},
    }

    with pytest.raises(EvaluationError, match="incomplete|unassigned|verified"):
        evaluate_verified_predictions(labels, {"a": True})


def test_evaluation_returns_confusion_and_category_metrics():
    labels = {
        "a": {"vulnerable": True, "class": "A", "verification_status": "independently_verified"},
        "b": {"vulnerable": False, "class": "A", "verification_status": "independently_verified"},
        "c": {"vulnerable": False, "class": "B", "verification_status": "independently_verified"},
    }

    result = evaluate_verified_predictions(
        labels,
        {"a": True, "b": True, "c": False},
    )

    assert result["confusion_matrix"] == {"tp": 1, "fp": 1, "tn": 1, "fn": 0}
    assert result["metrics"]["precision"] == 0.5
    assert result["metrics"]["recall"] == 1.0
    assert result["per_category"]["A"]["f1"] == pytest.approx(2 / 3)
    assert result["missing_predictions"] == []


def test_detections_from_telemetry_ignores_infrastructure_anomalies(tmp_path):
    path = tmp_path / "run.jsonl"
    events = [
        {"run_id": "run", "benchmark_id": "a", "anomalies": ["500_INTERNAL_SERVER_ERROR"]},
        {"run_id": "run", "benchmark_id": "b", "anomalies": ["RUN_FAILED"]},
        {"run_id": "run", "benchmark_id": "c", "anomalies": ["CONNECTION_ERROR"]},
    ]
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    detections, counts = detections_from_telemetry(path, run_id="run")

    assert detections == {"a": True}
    assert counts == {"500_INTERNAL_SERVER_ERROR": 1}


def test_detections_from_telemetry_can_include_negative_targets(tmp_path):
    path = tmp_path / "run.jsonl"
    events = [
        {"run_id": "run", "benchmark_id": "a", "anomalies": []},
        {"run_id": "run", "benchmark_id": "b", "anomalies": ["RUN_FAILED"]},
    ]
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    detections, _ = detections_from_telemetry(
        path,
        run_id="run",
        include_negatives=True,
    )

    assert detections == {"a": False, "b": False}
