import argparse
import json
from pathlib import Path


COMPONENTS = ("src/detectors/", "src/execution/")


def component_coverage(report):
    files = report.get("files")
    if not isinstance(files, dict):
        raise ValueError("Coverage report must contain a files mapping")

    summaries = [
        details.get("summary", {})
        for path, details in files.items()
        if path.startswith(COMPONENTS)
    ]
    if not summaries:
        raise ValueError("Coverage report has no detector or execution files")

    covered_lines = sum(item.get("covered_lines", 0) for item in summaries)
    total_lines = sum(item.get("num_statements", 0) for item in summaries)
    covered_branches = sum(item.get("covered_branches", 0) for item in summaries)
    total_branches = sum(item.get("num_branches", 0) for item in summaries)

    return {
        "line_percent": (
            100 * covered_lines / total_lines if total_lines else 100.0
        ),
        "branch_percent": (
            100 * covered_branches / total_branches
            if total_branches
            else 100.0
        ),
        "covered_lines": covered_lines,
        "total_lines": total_lines,
        "covered_branches": covered_branches,
        "total_branches": total_branches,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Enforce line and branch coverage for detectors and execution."
    )
    parser.add_argument("coverage_json", nargs="?", default="coverage.json")
    parser.add_argument("--minimum", type=float, default=85.0)
    args = parser.parse_args(argv)
    if not 0 <= args.minimum <= 100:
        parser.error("--minimum must be between 0 and 100")

    with Path(args.coverage_json).open(encoding="utf-8") as handle:
        report = json.load(handle)
    result = component_coverage(report)
    print(
        f"detectors+execution: lines={result['line_percent']:.2f}% "
        f"({result['covered_lines']}/{result['total_lines']}), "
        f"branches={result['branch_percent']:.2f}% "
        f"({result['covered_branches']}/{result['total_branches']})"
    )
    if min(result["line_percent"], result["branch_percent"]) < args.minimum:
        print(f"Coverage is below the required {args.minimum:.2f}%")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
