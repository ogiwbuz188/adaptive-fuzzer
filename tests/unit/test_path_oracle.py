from types import SimpleNamespace

import pytest

from src.detectors.path_oracle import PathTraversalOracle
from src.fuzzer import AdvancedBehavioralFuzzer


def test_oracle_matches_exact_canary_in_bytes_or_text():
    oracle = PathTraversalOracle("per-run-canary")

    assert oracle.detect(b"file contents: per-run-canary")
    assert oracle.detect("file contents: per-run-canary")
    assert not oracle.detect(b"generic server error")
    assert not oracle.detect(b"per-run-canarv")


@pytest.mark.parametrize("token", ["", None, 12])
def test_oracle_requires_a_non_empty_string(token):
    with pytest.raises(ValueError, match="non-empty string"):
        PathTraversalOracle(token)


def test_fuzzer_logs_canary_disclosure_in_all_detector_modes():
    fuzzer = AdvancedBehavioralFuzzer(
        "http://127.0.0.1:9000",
        seed=1,
        detector_mode="semantic-only",
        path_canary_token="per-run-canary",
    )
    response = SimpleNamespace(
        text="per-run-canary",
        content=b"per-run-canary",
        status_code=200,
        headers={"Content-Type": "text/plain"},
    )

    fuzzer.analyze(response, 0.01, "POST", "http://127.0.0.1:9000/path", {})

    assert [finding["type"] for finding in fuzzer.findings] == [
        "PATH_TRAVERSAL_CANARY"
    ]
