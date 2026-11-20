import argparse
import json
from pathlib import Path

from src.evaluation import (
    EvaluationError,
    detections_from_telemetry,
    evaluate_verified_predictions,
)
from src.ground_truth import load_labels


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate a benchmark run against verified ground truth."
    )
    parser.add_argument("run_id")
    parser.add_argument(
        "--data-directory",
        default=str(ROOT / "data"),
    )
    parser.add_argument(
        "--labels",
        default=str(
            ROOT / "research_benchmark" / "metadata" / "labels.csv"
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    telemetry_path = (
        Path(args.data_directory).resolve() / "raw" / f"{args.run_id}.jsonl"
    )
    detections, anomaly_counts = detections_from_telemetry(
        telemetry_path,
        run_id=args.run_id,
        include_negatives=True,
    )
    evaluation = evaluate_verified_predictions(
        load_labels(args.labels),
        detections,
    )
    evaluation["anomaly_counts"] = anomaly_counts

    if args.json:
        print(json.dumps(evaluation, indent=2, sort_keys=True))
    else:
        metrics = evaluation["metrics"]
        print(
            f"Evaluated={evaluation['evaluated']} "
            f"TP={metrics['tp']} FP={metrics['fp']} "
            f"TN={metrics['tn']} FN={metrics['fn']}"
        )
        print(
            f"precision={metrics['precision']:.4f} "
            f"recall={metrics['recall']:.4f} "
            f"f1={metrics['f1']:.4f}"
        )
        if evaluation["missing_predictions"]:
            print(
                "Targets with no anomaly: "
                + ", ".join(evaluation["missing_predictions"])
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvaluationError as error:
        print(f"Evaluation refused: {error}")
        raise SystemExit(2)
