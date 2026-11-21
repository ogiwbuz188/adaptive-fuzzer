import json

import pytest

from src.telemetry.schema import TelemetryEvent
from src.telemetry.writer import TelemetryWriter, write_run_manifest


def test_request_events_are_versioned_and_written_as_jsonl(tmp_path):
    output = tmp_path / "raw" / "events.jsonl"
    writer = TelemetryWriter(output)
    event = TelemetryEvent.create(
        run_id="run-1",
        benchmark_id="target-1",
        request_id="run-1-000001",
        seed=7,
        detector_mode="statistical",
        method="get",
        route="/api/v1/items",
        status=200,
        duration_ms=12.5,
        outcome="normal",
        anomalies=[],
    )

    writer.append(event)

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema_version"] == 2
    assert record["run_id"] == "run-1"
    assert record["benchmark_id"] == "target-1"
    assert record["request_id"] == "run-1-000001"
    assert record["method"] == "GET"
    assert record["payload_sample"] is None
    assert record["response_snippet"] is None


def test_telemetry_samples_are_limited_to_512_utf8_bytes():
    event = TelemetryEvent.create(
        run_id="run-1",
        benchmark_id="target-1",
        request_id="request-1",
        seed=7,
        detector_mode="statistical",
        method="POST",
        route="/api/v1/items",
        status=500,
        duration_ms=12.5,
        outcome="anomaly",
        anomalies=["SERVER_ERROR"],
        payload_sample="é" * 400,
        response_snippet=b"x" * 700,
    )

    record = event.as_dict()
    assert len(record["payload_sample"].encode("utf-8")) <= 512
    assert len(record["response_snippet"].encode("utf-8")) == 512


def test_run_manifest_preserves_metadata_for_multiple_runs(tmp_path):
    output = tmp_path / "run_manifest.json"

    write_run_manifest(output, "seed-1", {"master_seed": 1})
    write_run_manifest(output, "seed-2", {"master_seed": 2})

    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["runs"] == {
        "seed-1": {"master_seed": 1},
        "seed-2": {"master_seed": 2},
    }


def test_telemetry_rejects_missing_identifiers_and_negative_durations():
    with pytest.raises(ValueError, match="identifiers"):
        TelemetryEvent.create(
            run_id="",
            benchmark_id="target-1",
            request_id="request-1",
            seed=1,
            detector_mode="statistical",
            method="GET",
            route="/items",
            status=200,
            duration_ms=1,
            outcome="normal",
            anomalies=[],
        )

    with pytest.raises(ValueError, match="non-negative"):
        TelemetryEvent.create(
            run_id="run-1",
            benchmark_id="target-1",
            request_id="request-1",
            seed=1,
            detector_mode="statistical",
            method="GET",
            route="/items",
            status=200,
            duration_ms=-1,
            outcome="normal",
            anomalies=[],
        )
