import argparse
import json
from pathlib import Path
import statistics


def _summarize_metrics(results):
    metric_names = set.intersection(
        *(set(item["result"]["metrics"]) for item in results)
    )
    summary = {}
    for name in sorted(metric_names):
        values = [item["result"]["metrics"][name] for item in results]
        if not all(isinstance(value, (int, float)) for value in values):
            continue
        summary[name] = {
            "mean": statistics.mean(values),
            "standard_deviation": (
                statistics.stdev(values) if len(values) > 1 else 0.0
            ),
        }
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Aggregate evaluate_run.py JSON outputs for multiple seeds.",
    )
    parser.add_argument("files", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    aggregated = []
    for name in args.files:
        path = Path(name)
        with path.open(encoding="utf-8") as handle:
            aggregated.append({"file": str(path), "result": json.load(handle)})

    output = {
        "runs": aggregated,
        "aggregate": {"metrics": _summarize_metrics(aggregated)},
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for item in output["runs"]:
            metrics = item["result"]["metrics"]
            print(
                f"{item['file']}: precision={metrics['precision']:.4f} "
                f"recall={metrics['recall']:.4f} f1={metrics['f1']:.4f}"
            )
        for name, values in output["aggregate"]["metrics"].items():
            print(
                f"mean {name}={values['mean']:.4f} "
                f"std={values['standard_deviation']:.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
