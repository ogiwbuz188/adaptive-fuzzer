
from scripts.check_benchmark_labels import check_label_completeness

from src.ground_truth import calculate_metrics, load_labels


def test_load_labels():
    labels = load_labels()
    assert "BOLA_id_enumeration" in labels
    assert labels["BOLA_id_enumeration"]["vulnerable"] is True
    assert labels["BOLA_id_enumeration"]["verification_status"] == (
        "source_derived_draft"
    )
    assert labels["absolute_path_disclosure"]["vulnerable"] is True
    assert labels["absolute_path_disclosure"]["verification_status"] == (
        "source_derived_draft"
    )
    assert labels["BOLA_id_enumeration02"]["vulnerable"] is False


def test_every_benchmark_has_a_label_row():
    benchmark_count, unassigned_count, unverified_count = (
        check_label_completeness()
    )

    assert benchmark_count == len(load_labels())
    assert unassigned_count == 0
    assert unverified_count == benchmark_count


def test_calculate_metrics():
    labels = {
        "a": {"vulnerable": True, "verification_status": "independently_verified"},
        "b": {"vulnerable": True, "verification_status": "independently_verified"},
        "c": {"vulnerable": False, "verification_status": "independently_verified"},
        "d": {"vulnerable": False, "verification_status": "independently_verified"},
    }
    metrics = calculate_metrics(labels, {"a": True, "c": True})

    assert metrics == {
        "tp": 1,
        "fp": 1,
        "tn": 1,
        "fn": 1,
        "evaluated": 4,
        "excluded": 0,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }


def test_unassigned_and_pending_labels_are_excluded_from_metrics():
    labels = {
        "pending-positive": {
            "vulnerable": True,
            "verification_status": "independent_review_pending",
        },
        "unassigned": {
            "vulnerable": None,
            "verification_status": "unreviewed",
        },
    }

    metrics = calculate_metrics(labels, {"pending-positive": True, "unassigned": True})

    assert metrics["tp"] == 0
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["evaluated"] == 0
    assert metrics["excluded"] == 2
