from scripts.check_component_coverage import component_coverage


def test_component_coverage_aggregates_only_requested_paths():
    report = {
        "files": {
            "src/detectors/statistical.py": {
                "summary": {
                    "covered_lines": 9,
                    "num_statements": 10,
                    "covered_branches": 8,
                    "num_branches": 10,
                }
            },
            "src/execution/runner.py": {
                "summary": {
                    "covered_lines": 8,
                    "num_statements": 10,
                    "covered_branches": 9,
                    "num_branches": 10,
                }
            },
            "src/fuzzer.py": {
                "summary": {
                    "covered_lines": 0,
                    "num_statements": 100,
                    "covered_branches": 0,
                    "num_branches": 100,
                }
            },
        }
    }

    result = component_coverage(report)

    assert result["line_percent"] == 85
    assert result["branch_percent"] == 85
    assert result["covered_lines"] == 17
    assert result["covered_branches"] == 17
