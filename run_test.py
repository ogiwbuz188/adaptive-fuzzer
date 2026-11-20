import argparse
import hashlib
from pathlib import Path
import re
import sys
import uuid

from scripts.validate_dataset import validate_reports
from src.execution.manifest import load_manifest
from src.execution.runner import BenchmarkRunner


ROOT = Path(__file__).resolve().parent


def _seed_for_benchmark(master_seed, benchmark_id):
    value = f"{master_seed}:{benchmark_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:4], "big")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run manifest targets in per-benchmark Bubblewrap sandboxes."
    )
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "research_benchmark" / "manifest.yaml"),
    )
    parser.add_argument("--data-directory", default=str(ROOT / "data"))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--run-id", default=uuid.uuid4().hex)
    parser.add_argument("--benchmark-id", action="append")
    parser.add_argument("--max-targets", type=int)
    parser.add_argument(
        "--detector-mode",
        choices=["statistical", "statistical+fingerprint"],
        default="statistical",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    if args.seed < 0:
        raise ValueError("seed must be non-negative")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id) or args.run_id in {
        ".",
        "..",
    }:
        raise ValueError("run-id may contain only letters, digits, '.', '_' and '-'")
    if args.max_targets is not None and args.max_targets <= 0:
        raise ValueError("max-targets must be positive")

    benchmarks = load_manifest(args.manifest, ROOT)
    if args.benchmark_id:
        requested = set(args.benchmark_id)
        known = {benchmark.benchmark_id for benchmark in benchmarks}
        unknown = requested - known
        if unknown:
            raise ValueError(f"Unknown benchmark ID(s): {', '.join(sorted(unknown))}")
        benchmarks = [
            benchmark
            for benchmark in benchmarks
            if benchmark.benchmark_id in requested
        ]
    if args.max_targets is not None:
        benchmarks = benchmarks[: args.max_targets]

    print(
        f"Run {args.run_id}: seed={args.seed}, detector={args.detector_mode}, "
        f"targets={len(benchmarks)}"
    )
    runner = BenchmarkRunner(ROOT, args.data_directory)
    results = []
    for benchmark in benchmarks:
        seed = _seed_for_benchmark(args.seed, benchmark.benchmark_id)
        result = runner.run(
            benchmark,
            seed=seed,
            run_id=args.run_id,
            detector_mode=args.detector_mode,
        )
        results.append(result)
        print(
            f"{benchmark.benchmark_id}: "
            f"{'completed' if result.succeeded else 'failed'} "
            f"(exit={result.exit_code}, "
            f"duration={result.duration_seconds:.2f}s, seed={seed})"
        )

    report_directory = (
        Path(args.data_directory) / "reports" / args.run_id
    )
    try:
        report_count = validate_reports(benchmarks, report_directory)
        print(f"Validated {report_count} completed reports for run {args.run_id}.")
    except ValueError as error:
        print(f"Report validation failed: {error}", file=sys.stderr)
        return 1

    return 0 if all(result.succeeded for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
