from src.evaluation import exact_binomial_test, paired_mcnemar_test


def test_exact_binomial_test_is_valid_for_discordant_pairs():
    assert exact_binomial_test(3, 10) > 0.0
    assert exact_binomial_test(5, 10) == 1.0


def test_paired_mcnemar_test():
    baseline = {"a": True, "b": False, "c": False, "d": True}
    comparison = {"a": True, "b": True, "c": False, "d": False}

    result = paired_mcnemar_test(baseline, comparison)

    assert result["baseline_only"] == 1
    assert result["comparison_only"] == 1
    assert result["discordant"] == 2
