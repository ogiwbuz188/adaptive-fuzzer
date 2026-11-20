from pathlib import Path

from src.execution.manifest import load_manifest
from src.ground_truth import load_labels


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "research_benchmark"


def check_label_completeness():
    benchmarks = load_manifest(
        ROOT / "research_benchmark" / "manifest.yaml",
        ROOT,
    )
    benchmark_ids = {benchmark.benchmark_id for benchmark in benchmarks}
    source_ids = {
        path.stem
        for path in BENCHMARK_ROOT.rglob("*.py")
        if path.name != "__init__.py"
    }
    labels = load_labels(BENCHMARK_ROOT / "metadata" / "labels.csv")
    label_ids = set(labels)
    if source_ids != benchmark_ids:
        raise ValueError(
            f"Manifest/source mismatch: {len(source_ids - benchmark_ids)} "
            f"unlisted sources, {len(benchmark_ids - source_ids)} missing sources"
        )
    missing = benchmark_ids - label_ids
    unexpected = label_ids - benchmark_ids

    if missing or unexpected:
        raise ValueError(
            f"Label coverage mismatch: {len(missing)} missing, "
            f"{len(unexpected)} unexpected"
        )

    for benchmark in benchmarks:
        for scenario in benchmark.authorization_scenarios:
            label = labels.get(benchmark.benchmark_id)
            if (
                label is not None
                and label["vulnerable"] is not None
                and label["vulnerable"] != scenario.expected_vulnerable
            ):
                raise ValueError(
                    f"BOLA label/manifest mismatch for "
                    f"{benchmark.benchmark_id}: label="
                    f"{label['vulnerable']}, manifest="
                    f"{scenario.expected_vulnerable}"
                )

    unassigned = sum(label["vulnerable"] is None for label in labels.values())
    unverified = sum(
        label["verification_status"] != "independently_verified"
        for label in labels.values()
    )
    return len(benchmark_ids), unassigned, unverified


if __name__ == "__main__":
    benchmark_count, unassigned_count, unverified_count = (
        check_label_completeness()
    )
    print(
        f"Label rows cover all {benchmark_count} benchmarks; "
        f"{unassigned_count} are unassigned and "
        f"{unverified_count} are not independently verified."
    )
