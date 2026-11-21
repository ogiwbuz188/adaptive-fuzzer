import pytest

from run_test import _parse_args, _parse_seeds
from scripts.check_experiment_environment import collect_environment


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["1,2,3,4,5"], [1, 2, 3, 4, 5]),
        (["1", "2", "3"], [1, 2, 3]),
        (["1,2", "3"], [1, 2, 3]),
    ],
)
def test_parse_seeds_accepts_comma_and_space_separated_values(values, expected):
    assert _parse_seeds(values) == expected


def test_run_test_cli_accepts_documented_comma_separated_seeds():
    args = _parse_args(["--seeds", "1,2,3,4,5"])

    assert _parse_seeds(args.seeds) == [1, 2, 3, 4, 5]


def test_environment_snapshot_includes_run_provenance():
    snapshot = collect_environment(7, "statistical")

    assert snapshot["source_commit"]
    assert snapshot["python_version"]
    assert isinstance(snapshot["pip_freeze"], list)
    assert snapshot["os_kernel"]
    assert snapshot["master_seed"] == 7
    assert snapshot["detector_mode"] == "statistical"
    assert "count" in snapshot["cpu"]
    assert "memory_bytes" in snapshot
