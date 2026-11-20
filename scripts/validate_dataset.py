import argparse
from pathlib import Path

from src.execution.manifest import load_manifest


ROOT = Path(__file__).resolve().parents[1]


def validate_reports(benchmarks, report_directory):
    report_directory = Path(report_directory)
    expected = {
        f"{benchmark.benchmark_id}_dashboard.html"
        for benchmark in benchmarks
    }
    actual = {
        path.name
        for path in report_directory.glob("*_dashboard.html")
    }
    missing = expected - actual
    unexpected = actual - expected
    incomplete = []

    for report_name in expected & actual:
        content = (report_directory / report_name).read_text(encoding="utf-8")
        if '<meta name="run-status" content="completed">' not in content:
            incomplete.append(report_name)

    if missing or unexpected or incomplete:
        raise ValueError(
            "Report coverage failed: "
            f"{len(missing)} missing, {len(unexpected)} unexpected, "
            f"{len(incomplete)} incomplete"
        )
    return len(expected)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "research_benchmark" / "manifest.yaml"),
    )
    parser.add_argument("--data-directory", default=str(ROOT / "data"))
    args = parser.parse_args(argv)

    benchmarks = load_manifest(args.manifest, ROOT)
    report_directory = (
        Path(args.data_directory) / "reports" / args.run_id
    )
    count = validate_reports(benchmarks, report_directory)
    print(f"Validated {count} completed benchmark reports for {args.run_id}.")
    return count


if __name__ == "__main__":
    main()
