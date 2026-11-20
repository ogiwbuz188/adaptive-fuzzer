import argparse
import json
from pathlib import Path


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

    if args.json:
        print(json.dumps(aggregated, indent=2, sort_keys=True))
    else:
        for item in aggregated:
            metrics = item["result"]["metrics"]
            print(
                f"{item['file']}: precision={metrics['precision']:.4f} "
                f"recall={metrics['recall']:.4f} f1={metrics['f1']:.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
