import argparse
from pathlib import Path
import uuid

import run_test


DETECTOR_MODES = (
    "semantic-only",
    "statistical",
    "statistical+fingerprint",
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run the synthetic benchmark under all detector modes using "
            "the same seeds and manifest budgets."
        )
    )
    parser.add_argument("--seeds", nargs="+", required=True)
    parser.add_argument(
        "--manifest",
        default=str(
            Path(__file__).resolve().parents[1]
            / "research_benchmark"
            / "manifest.yaml"
        ),
    )
    parser.add_argument(
        "--data-directory",
        default=str(Path(__file__).resolve().parents[1] / "data"),
    )
    parser.add_argument("--run-id", default=f"ablation-{uuid.uuid4().hex}")
    parser.add_argument("--benchmark-id", action="append")
    parser.add_argument("--max-targets", type=int)
    args = parser.parse_args(argv)

    succeeded = True
    for mode in DETECTOR_MODES:
        command = [
            "--manifest",
            args.manifest,
            "--data-directory",
            args.data_directory,
            "--run-id",
            f"{args.run_id}-{mode.replace('+', '-')}",
            "--detector-mode",
            mode,
            "--seeds",
            *args.seeds,
        ]
        if args.max_targets is not None:
            command.extend(["--max-targets", str(args.max_targets)])
        for benchmark_id in args.benchmark_id or []:
            command.extend(["--benchmark-id", benchmark_id])

        print(f"Starting detector ablation mode: {mode}", flush=True)
        succeeded = run_test.main(command) == 0 and succeeded

    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
