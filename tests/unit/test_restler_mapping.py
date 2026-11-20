import json

import pytest

from scripts.convert_restler_findings import main


def test_restler_mapping_requires_explicit_evidence(tmp_path, capsys):
    mapping = tmp_path / "mapping.csv"
    mapping.write_text(
        "benchmark_id,restler_finding_id,finding_status,evidence_reference\n"
        "BOLA_id_enumeration,F-1,detected,restler-report/finding-1.json\n",
        encoding="utf-8",
    )
    output = tmp_path / "detections.json"

    assert main([str(mapping), "--json-output", str(output)]) == 0
    document = json.loads(output.read_text(encoding="utf-8"))

    assert document["tool"] == "RESTler"
    assert document["detections"] == {"BOLA_id_enumeration": True}


def test_restler_mapping_rejects_missing_evidence(tmp_path):
    mapping = tmp_path / "mapping.csv"
    mapping.write_text(
        "benchmark_id,restler_finding_id,finding_status,evidence_reference\n"
        "BOLA_id_enumeration,F-1,detected,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evidence"):
        main([str(mapping)])
