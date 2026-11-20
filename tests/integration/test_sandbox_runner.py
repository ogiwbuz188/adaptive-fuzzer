from dataclasses import replace
from pathlib import Path
import shutil
import sys

import pytest

from src.execution.manifest import load_manifest
from src.execution.runner import BenchmarkRunner


@pytest.mark.skipif(
    sys.platform != "linux" or shutil.which("bwrap") is None,
    reason="Bubblewrap integration test requires Linux and bwrap",
)
def test_target_and_fuzzer_run_inside_bounded_sandbox(tmp_path):
    root = Path(__file__).resolve().parents[2]
    benchmark = next(
        item
        for item in load_manifest(root / "research_benchmark" / "manifest.yaml", root)
        if item.benchmark_id == "missing_type_casts"
    )
    benchmark = replace(benchmark, runs=1, timeout_seconds=30)
    runner = BenchmarkRunner(root, tmp_path / "data")

    result = runner.run(
        benchmark,
        seed=17,
        run_id="sandbox-test",
        detector_mode="statistical",
    )

    report = (
        tmp_path
        / "data"
        / "reports"
        / "sandbox-test"
        / "missing_type_casts_dashboard.html"
    )
    events = (
        tmp_path
        / "data"
        / "raw"
        / "sandbox-test.jsonl"
    )
    assert result.succeeded
    assert '<meta name="run-status" content="completed">' in report.read_text(
        encoding="utf-8"
    )
    assert events.is_file()
    assert '"seed": 17' in events.read_text(encoding="utf-8")
