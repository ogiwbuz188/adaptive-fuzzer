
from collections import deque

import requests
import pytest

from src.fuzzer import AdvancedBehavioralFuzzer
from src.detectors.statistical import StatisticalDetector


def test_collect_baseline_and_detect_new_status():
    detector = StatisticalDetector(z_threshold=2.5)
    detector.collect(
        ("POST", "/api/v1/test"),
        [100, 101, 99],
        [0.1, 0.11, 0.09],
        [200, 200, 200],
        ["application/json"],
    )

    anomalies = detector.detect(
        ("POST", "/api/v1/test"),
        100,
        0.1,
        500,
        "application/json",
    )

    assert anomalies == ["NEW_HTTP_STATUS"]


def test_detector_does_not_flag_lower_response_values_as_outliers():
    detector = StatisticalDetector(z_threshold=2.5)
    detector.collect(
        ("POST", "/api/v1/test"),
        [100, 101, 99],
        [0.1, 0.11, 0.09],
        [200, 200, 200],
        ["application/json"],
    )

    anomalies = detector.detect(
        ("POST", "/api/v1/test"),
        1,
        0.001,
        200,
        "application/json",
    )

    assert anomalies == []


def test_fuzzer_delegates_statistical_checks_to_detector():
    fuzzer = AdvancedBehavioralFuzzer("http://127.0.0.1:9000")
    key = ("GET", "/api/v1/test")
    fuzzer.statistical_detector.collect(
        key,
        [10, 10, 10],
        [0.1, 0.1, 0.1],
        [200, 200, 200],
        ["application/json"],
    )
    response = requests.Response()
    response.status_code = 500
    response.headers["Content-Type"] = "application/json"
    response._content = b'{"ok":false}'

    fuzzer.analyze(
        response,
        1.0,
        "GET",
        "http://127.0.0.1:9000/api/v1/test",
        {},
    )

    finding_types = {finding["type"] for finding in fuzzer.findings}
    assert {
        "RESPONSE_SIZE_OUTLIER",
        "LATENCY_OUTLIER",
        "NEW_HTTP_STATUS",
    }.issubset(finding_types)


def test_detector_rejects_empty_or_mismatched_baselines():
    detector = StatisticalDetector()

    with pytest.raises(ValueError, match="at least one"):
        detector.collect("empty", [], [], [], [])
    with pytest.raises(ValueError, match="equal lengths"):
        detector.collect("mismatched", [1], [], [200], [])


def test_detector_validates_thresholds_and_missing_baselines():
    with pytest.raises(ValueError, match="z_threshold"):
        StatisticalDetector(z_threshold=0)
    with pytest.raises(ValueError, match="MAD and drift"):
        StatisticalDetector(mad_threshold=0)
    with pytest.raises(ValueError, match="MAD and drift"):
        StatisticalDetector(drift_threshold=0)

    detector = StatisticalDetector()
    assert detector.detect("unknown", 1, 0.1, 200, "text/plain") == []
    assert not detector.has_baseline("unknown")


def test_detector_flags_robust_outliers_drift_and_content_type_changes():
    detector = StatisticalDetector()
    key = ("GET", "/api/v1/test")
    detector.collect(
        key,
        [100] * 8,
        [0.1] * 8,
        [200] * 8,
        ["application/json"],
    )

    anomalies = detector.detect(
        key,
        150,
        0.3,
        200,
        "text/plain",
    )

    assert {
        "RESPONSE_SIZE_OUTLIER",
        "ROBUST_RESPONSE_SIZE_OUTLIER",
        "RESPONSE_SIZE_BASELINE_DRIFT",
        "LATENCY_OUTLIER",
        "ROBUST_LATENCY_OUTLIER",
        "LATENCY_BASELINE_DRIFT",
        "CONTENT_TYPE_MISMATCH",
    }.issubset(anomalies)


def test_detector_drift_handles_zero_baseline_and_modified_z():
    detector = StatisticalDetector()

    assert detector._has_drift(deque([0] * 8), 1)
    assert not detector._has_drift(deque([0] * 8), 0)
    assert detector._modified_z(110, 100, 10) == pytest.approx(0.6745)


def test_fingerprint_detector_is_opt_in_and_separate_from_statistics():
    statistical_only = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        detector_mode="statistical",
    )
    combined = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        detector_mode="statistical+fingerprint",
    )

    for fuzzer in (statistical_only, combined):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"ok":true}'
        for _ in range(12):
            fuzzer.analyze(
                response,
                0.1,
                "GET",
                "http://127.0.0.1:9000/api/v1/items",
                {},
            )

    statistical_findings = {
        finding["type"] for finding in statistical_only.findings
    }
    combined_findings = {finding["type"] for finding in combined.findings}
    assert "INPUT_IGNORED_OR_FILTERED" not in statistical_findings
    assert "INPUT_IGNORED_OR_FILTERED" in combined_findings


def test_semantic_only_mode_flags_only_http_500_or_stack_traces():
    fuzzer = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        detector_mode="semantic-only",
    )
    fuzzer.statistical_detector.collect(
        ("GET", "/api/v1/items"),
        [10, 10, 10],
        [0.1, 0.1, 0.1],
        [200, 200, 200],
        ["text/plain"],
    )
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Length"] = "1000"
    response._content = b"Traceback (most recent call last)"

    fuzzer.analyze(
        response,
        0.1,
        "GET",
        "http://127.0.0.1:9000/api/v1/items",
        {},
    )
    assert {
        finding["type"] for finding in fuzzer.findings
    } == {"STACK_OR_FATAL_TRACE"}

    response.status_code = 500
    response._content = b""
    fuzzer.analyze(
        response,
        0.1,
        "GET",
        "http://127.0.0.1:9000/api/v1/items",
        {},
    )
    assert {
        finding["type"] for finding in fuzzer.findings
    } == {"STACK_OR_FATAL_TRACE", "500_INTERNAL_SERVER_ERROR"}


def test_seed_reproduces_mutation_sequence():
    first = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        seed=23,
    )
    second = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        seed=23,
    )

    assert [first.mutate("seed") for _ in range(12)] == [
        second.mutate("seed") for _ in range(12)
    ]
