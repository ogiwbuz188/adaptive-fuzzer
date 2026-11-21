from pathlib import Path

from scripts.generate_source_derived_labels import derive_label
from src.execution.manifest import load_manifest


def test_source_derived_label_derivation():
    root = Path(__file__).resolve().parents[2]
    benchmarks = load_manifest(
        root / "research_benchmark" / "manifest.yaml",
        root,
    )
    vulnerable, status, _, _ = derive_label(
        next(
            benchmark
            for benchmark in benchmarks
            if benchmark.benchmark_id == "BOLA_id_enumeration"
        )
    )
    assert vulnerable is True
    assert status == "source_derived_draft"


def test_negative_bola_source_label():
    root = Path(__file__).resolve().parents[2]
    benchmarks = load_manifest(
        root / "research_benchmark" / "manifest.yaml",
        root,
    )
    vulnerable, _, _, _ = derive_label(
        next(
            benchmark
            for benchmark in benchmarks
            if benchmark.benchmark_id == "BOLA_id_enumeration02"
        )
    )
    assert vulnerable is False
