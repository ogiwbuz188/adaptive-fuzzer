import pytest
import yaml

from src.execution.manifest import load_manifest


def _entry(entrypoint="research_benchmark/target.py"):
    return {
        "id": "target",
        "category": "synthetic",
        "entrypoint": entrypoint,
        "route": "/api/items",
        "method": "GET",
        "port": 9000,
        "runs": 1,
        "startup_timeout_seconds": 1,
        "timeout_seconds": 1,
    }


def _write_manifest(tmp_path, entries):
    root = tmp_path / "repo"
    benchmark_root = root / "research_benchmark"
    benchmark_root.mkdir(parents=True)
    (benchmark_root / "target.py").write_text("", encoding="utf-8")
    manifest_path = root / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump({"version": 1, "benchmarks": entries}),
        encoding="utf-8",
    )
    return root, manifest_path


def test_manifest_loads_relative_path_and_normalizes_method(tmp_path):
    root, manifest_path = _write_manifest(tmp_path, [_entry()])

    benchmarks = load_manifest(manifest_path, root)

    assert benchmarks[0].method == "GET"
    assert benchmarks[0].entrypoint == (root / "research_benchmark" / "target.py")
    assert benchmarks[0].authorization_scenarios == ()


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ([], "version 1 mapping"),
        ({"version": 2, "benchmarks": [_entry()]}, "version 1 mapping"),
        ({"version": 1, "benchmarks": []}, "at least one benchmark"),
    ],
)
def test_manifest_rejects_invalid_document_root(tmp_path, document, message):
    root, manifest_path = _write_manifest(tmp_path, [_entry()])
    manifest_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_manifest(manifest_path, root)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"method": "PATCH"}, "Unsupported method"),
        ({"route": "relative"}, "must start with"),
        ({"port": 65536}, "at most 65535"),
        ({"runs": True}, "must be a positive integer"),
    ],
)
def test_manifest_rejects_invalid_target_values(tmp_path, updates, message):
    entry = _entry()
    entry.update(updates)
    root, manifest_path = _write_manifest(tmp_path, [entry])

    with pytest.raises(ValueError, match=message):
        load_manifest(manifest_path, root)


def test_manifest_rejects_duplicate_ids_and_entrypoints(tmp_path):
    root, manifest_path = _write_manifest(
        tmp_path,
        [_entry(), {**_entry(), "entrypoint": "research_benchmark/other.py"}],
    )
    (root / "research_benchmark" / "other.py").write_text(
        "",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate benchmark ID"):
        load_manifest(manifest_path, root)

    entries = [_entry(), {**_entry(), "id": "other"}]
    root, manifest_path = _write_manifest(tmp_path / "duplicate", entries)
    with pytest.raises(ValueError, match="duplicate benchmark entrypoints"):
        load_manifest(manifest_path, root)


def test_manifest_rejects_entrypoints_outside_benchmark_tree(tmp_path):
    root, manifest_path = _write_manifest(
        tmp_path,
        [_entry("../outside.py")],
    )
    (root / "outside.py").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid benchmark entrypoint"):
        load_manifest(manifest_path, root)


def test_manifest_rejects_invalid_authorization_scenario(tmp_path):
    scenario = {
        "scenario_id": "same-user",
        "route": "/api/items",
        "owner_identity": "user",
        "other_user_identity": "user",
        "owned_object_id": "1",
        "object_parameter": "id",
        "object_id_field": "id",
        "owner_headers": {"Authorization": "Bearer owner"},
        "other_user_headers": {"Authorization": "Bearer other"},
        "expected_vulnerable": False,
    }
    entry = {**_entry(), "authorization_scenarios": [scenario]}
    root, manifest_path = _write_manifest(tmp_path, [entry])

    with pytest.raises(ValueError, match="identities must differ"):
        load_manifest(manifest_path, root)

    scenario["owner_identity"] = "owner"
    scenario["route"] = "relative"
    manifest_path.write_text(
        yaml.safe_dump({"version": 1, "benchmarks": [entry]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Scenario route"):
        load_manifest(manifest_path, root)
