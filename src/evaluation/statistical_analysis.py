import math


def exact_binomial_test(successes, total):
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("successes must be between zero and total")
    if total == 0:
        return 1.0
    tail = sum(
        math.comb(total, value) * (0.5 ** total)
        for value in range(successes + 1)
    )
    return min(1.0, 2.0 * tail)


def paired_mcnemar_test(baseline_detections, comparison_detections):
    if set(baseline_detections) != set(comparison_detections):
        raise ValueError("paired runs must contain the same benchmark IDs")

    baseline_only = comparison_only = 0
    for benchmark_id in baseline_detections:
        baseline = bool(baseline_detections[benchmark_id])
        comparison = bool(comparison_detections[benchmark_id])
        if baseline and not comparison:
            baseline_only += 1
        elif comparison and not baseline:
            comparison_only += 1

    discordant = baseline_only + comparison_only
    p_value = exact_binomial_test(comparison_only, discordant)
    return {
        "baseline_only": baseline_only,
        "comparison_only": comparison_only,
        "discordant": discordant,
        "p_value": p_value,
    }
