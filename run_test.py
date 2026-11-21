import argparse
import hashlib
from pathlib import Path
import re
import sys
import uuid

from scripts.validate_dataset import validate_reports
from scripts.check_experiment_environment import collect_environment
from src.execution.manifest import load_manifest
from src.execution.runner import BenchmarkRunner
from src.telemetry.writer import write_run_manifest


ROOT = Path(__file__).resolve().parent


def _seed_for_benchmark(master_seed, benchmark_id):
    value = f"{master_seed}:{benchmark_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:4], "big")


def _parse_seed_token(value):
    try:
        if "," in value:
            return [int(seed) for seed in value.split(",")]
        return int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "seeds must be comma-separated or space-separated integers"
        ) from error


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
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=_parse_seed_token,
        help="Run the selected benchmark set independently for each seed.",
    )
    parser.add_argument("--run-id", default=uuid.uuid4().hex)
    parser.add_argument("--benchmark-id", action="append")
    parser.add_argument("--max-targets", type=int)
    parser.add_argument(
        "--detector-mode",
        choices=[
            "semantic-only",
            "statistical",
            "statistical+fingerprint",
        ],
        default="statistical",
    )
    return parser.parse_args(argv)


def _parse_seeds(values):
    seeds = [
        seed
        for item in values
        for seed in (
            item
            if isinstance(item, list)
            else [int(value) for value in str(item).split(",")]
        )
    ]
    if not seeds:
        raise ValueError("at least one seed is required")
    return seeds


def main(argv=None):
    args = _parse_args(argv)
    master_seeds = _parse_seeds(args.seeds) if args.seeds is not None else [args.seed]
    if any(seed < 0 for seed in master_seeds):
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

    runner = BenchmarkRunner(ROOT, args.data_directory)
    overall_succeeded = True
    for master_seed in master_seeds:
        run_id = args.run_id
        if len(master_seeds) > 1:
            run_id = f"{args.run_id}-seed-{master_seed}"

        environment = collect_environment(master_seed, args.detector_mode)
        write_run_manifest(
            Path(args.data_directory) / "run_manifest.json",
            run_id,
            environment,
        )
        print(
            f"Run {run_id}: seed={master_seed}, "
            f"detector={args.detector_mode}, targets={len(benchmarks)}"
        )
        results = []
        for benchmark in benchmarks:
            seed = _seed_for_benchmark(master_seed, benchmark.benchmark_id)
            result = runner.run(
                benchmark,
                seed=seed,
                run_id=run_id,
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
            Path(args.data_directory) / "reports" / run_id
        )
        try:
            report_count = validate_reports(benchmarks, report_directory)
            print(
                f"Validated {report_count} completed reports "
                f"for run {run_id}."
            )
        except ValueError as error:
            print(f"Report validation failed: {error}", file=sys.stderr)
            overall_succeeded = False
            continue

        if not all(result.succeeded for result in results):
            overall_succeeded = False

    return 0 if overall_succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
