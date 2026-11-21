from scripts import run_detector_ablation


def test_ablation_runs_all_modes_with_identical_seeds(monkeypatch):
    runs = []
    monkeypatch.setattr(
        run_detector_ablation.run_test,
        "main",
        lambda arguments: runs.append(arguments) or 0,
    )

    assert run_detector_ablation.main(
        [
            "--seeds",
            "1,2,3",
            "--run-id",
            "ablation-test",
            "--max-targets",
            "2",
        ]
    ) == 0

    assert len(runs) == 3
    assert [arguments[arguments.index("--detector-mode") + 1] for arguments in runs] == [
        "semantic-only",
        "statistical",
        "statistical+fingerprint",
    ]
    assert all(
        arguments[arguments.index("--seeds") + 1] == "1,2,3"
        for arguments in runs
    )
    assert all(
        arguments[arguments.index("--max-targets") + 1] == "2"
        for arguments in runs
    )
    run_ids = [
        arguments[arguments.index("--run-id") + 1] for arguments in runs
    ]
    assert run_ids == [
        "ablation-test-semantic-only",
        "ablation-test-statistical",
        "ablation-test-statistical-fingerprint",
    ]
