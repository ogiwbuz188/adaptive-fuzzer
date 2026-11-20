
from pathlib import Path

import pytest

from scripts.validate_dataset import validate_reports
from src.execution.manifest import load_manifest
from src.fuzzer import AdvancedBehavioralFuzzer


def test_dashboard_is_written_with_escaped_content(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fuzzer = AdvancedBehavioralFuzzer("http://127.0.0.1:9000")
    fuzzer.log_anomaly(
        "<script>",
        500,
        "POST",
        "/api/v1/test",
        "<payload>",
        "<evidence>",
    )

    report = tmp_path / "report.html"
    fuzzer.generate_web_dashboard(report)

    document = report.read_text(encoding="utf-8")
    assert "&lt;script&gt;" in document
    assert "<script>" not in document


def test_report_coverage_requires_every_manifest_target_to_complete(tmp_path):
    root = Path(__file__).resolve().parents[2]
    benchmarks = load_manifest(
        root / "research_benchmark" / "manifest.yaml",
        root,
    )[:2]
    for benchmark in benchmarks:
        (tmp_path / f"{benchmark.benchmark_id}_dashboard.html").write_text(
            '<meta name="run-status" content="completed">',
            encoding="utf-8",
        )

    assert validate_reports(benchmarks, tmp_path) == 2

    (tmp_path / f"{benchmarks[1].benchmark_id}_dashboard.html").unlink()
    with pytest.raises(ValueError, match="missing"):
        validate_reports(benchmarks, tmp_path)
