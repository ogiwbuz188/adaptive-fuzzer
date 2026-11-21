from dataclasses import replace
from pathlib import Path

import pytest

from src.execution.manifest import load_manifest
from src.execution.sandbox import BubblewrapSandbox, _missing_mount_parents


ROOT = Path(__file__).resolve().parents[2]


def _benchmark():
    return next(
        benchmark
        for benchmark in load_manifest(
            ROOT / "research_benchmark" / "manifest.yaml",
            ROOT,
        )
        if benchmark.benchmark_id == "missing_type_casts"
    )


def _sandbox(tmp_path, monkeypatch):
    executable = tmp_path / "bwrap"
    executable.touch()
    monkeypatch.setattr(
        BubblewrapSandbox,
        "_python_mount",
        staticmethod(lambda: ("/usr/bin/python3", [])),
    )
    return BubblewrapSandbox(
        ROOT,
        tmp_path / "data",
        executable=executable,
    )


def test_command_keeps_target_and_data_in_sandbox(tmp_path, monkeypatch):
    sandbox = _sandbox(tmp_path, monkeypatch)

    command = sandbox.build_command(
        _benchmark(),
        seed=17,
        run_id="sandbox-unit",
        detector_mode="statistical",
    )

    assert "--unshare-all" in command
    assert "--die-with-parent" in command
    assert "--tmpfs" in command
    assert "/tmp" in command
    assert str(tmp_path / "data") in command
    assert "/research_benchmark/Boundary_Condition_Crises" not in command
    assert any(part.endswith("missing_type_casts.py") for part in command)
    assert "--detector-mode" in command


def test_path_traversal_command_mounts_per_run_canary(tmp_path, monkeypatch):
    sandbox = _sandbox(tmp_path, monkeypatch)
    benchmark = replace(_benchmark(), category="Injection_Path_Traversals")

    command = sandbox.build_command(
        benchmark,
        seed=17,
        run_id="path-canary",
        detector_mode="statistical",
    )

    separator = command.index("--")
    canary_mount = command.index(str(sandbox.canary_path)) - 1
    assert command[canary_mount:canary_mount + 3] == [
        "--ro-bind",
        str(sandbox.canary_path),
        "/tmp/canary_secret.txt",
    ]
    assert canary_mount < separator
    assert command[separator + 1:].count("--canary-token") == 1
    assert command[command.index("--canary-token") + 1] == sandbox.canary_token
    assert sandbox.canary_path.read_text(encoding="utf-8") == sandbox.canary_token


def test_command_rejects_entrypoint_outside_benchmark_tree(
    tmp_path,
    monkeypatch,
):
    sandbox = _sandbox(tmp_path, monkeypatch)
    benchmark = replace(_benchmark(), entrypoint=tmp_path / "outside.py")

    with pytest.raises(ValueError, match="remain under research_benchmark"):
        sandbox.build_command(benchmark, 1, "run", "statistical")


def test_sandbox_refuses_missing_bubblewrap(tmp_path):
    with pytest.raises(RuntimeError, match="Bubblewrap is required"):
        BubblewrapSandbox(ROOT, tmp_path / "data", executable="/missing/bwrap")


def test_sandbox_refuses_non_linux_platform(tmp_path, monkeypatch):
    monkeypatch.setattr("src.execution.sandbox.sys.platform", "win32")

    with pytest.raises(RuntimeError, match="requires Linux"):
        BubblewrapSandbox(ROOT, tmp_path / "data", executable="/missing/bwrap")


def test_missing_mount_parents_respects_existing_root_binds():
    assert list(_missing_mount_parents("/opt/python/bin/python")) == [
        Path("/opt"),
        Path("/opt/python"),
        Path("/opt/python/bin"),
    ]
    assert list(_missing_mount_parents("/usr/local/bin/python")) == []
