import json

from scripts.aggregate_evaluations import main


def test_aggregate_evaluations_reports_mean_and_standard_deviation(
    tmp_path,
    capsys,
):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(
        json.dumps({"metrics": {"precision": 0.2, "f1": 0.4}}),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps({"metrics": {"precision": 0.8, "f1": 0.6}}),
        encoding="utf-8",
    )

    assert main([str(first), str(second), "--json"]) == 0

    result = json.loads(capsys.readouterr().out)
    metrics = result["aggregate"]["metrics"]
    assert metrics["precision"]["mean"] == 0.5
    assert metrics["precision"]["standard_deviation"] > 0
    assert metrics["f1"]["mean"] == 0.5
