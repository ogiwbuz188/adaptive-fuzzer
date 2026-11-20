import csv
from pathlib import Path
import runpy


def test_plotting_script_writes_charts_to_documented_directory(
    tmp_path,
    monkeypatch,
):
    source = (
        Path(__file__).resolve().parents[2]
        / "notebook"
        / "generate_plots.py"
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    with (tmp_path / "data" / "test_runs.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["Time", "Anomaly Group", "Status", "Context Route", "Payload Trigger"]
        )
        writer.writerow(
            ["2026-01-01 00:00:00", "500_INTERNAL_SERVER_ERROR", 500, "POST /test", "{}"]
        )
        writer.writerow(
            ["2026-01-01 00:00:01", "LATENCY_OUTLIER", 200, "POST /test", "{}"]
        )

    runpy.run_path(str(source), run_name="__main__")

    assert (tmp_path / "notebook" / "anomaly_distribution.png").is_file()
    assert (tmp_path / "notebook" / "telemetry_timeline.png").is_file()
