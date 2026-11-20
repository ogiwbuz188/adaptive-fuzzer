
from pathlib import Path

from run_test import _seed_for_benchmark
from src.execution.manifest import load_manifest


def test_manifest_contains_all_targets_with_explicit_routes():
    root = Path(__file__).resolve().parents[2]
    benchmarks = load_manifest(
        root / "research_benchmark" / "manifest.yaml",
        root,
    )

    assert len(benchmarks) == 100
    missing_type_casts = next(
        item for item in benchmarks
        if item.benchmark_id == "missing_type_casts"
    )
    assert missing_type_casts.route == "/api/v1/validate-cast"
    assert missing_type_casts.method == "POST"
    assert missing_type_casts.runs == 40
    assert missing_type_casts.entrypoint.is_file()


def test_target_seed_is_stable_and_target_specific():
    seed = _seed_for_benchmark(9, "missing_type_casts")

    assert seed == _seed_for_benchmark(9, "missing_type_casts")
    assert seed != _seed_for_benchmark(9, "BOLA_id_enumeration")
