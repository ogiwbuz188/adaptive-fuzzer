from pathlib import Path
import resource
import signal
import subprocess
from types import SimpleNamespace

import pytest

from src.execution.manifest import load_manifest
from src.execution.runner import BenchmarkRunner


ROOT = Path(__file__).resolve().parents[2]


class _FakeSandbox:
    def __init__(self, repository_root, data_directory):
        self.command = ["bwrap", "--unshare-all"]

    def build_command(self, benchmark, seed, run_id, detector_mode):
        return self.command


def _runner(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.execution.runner.BubblewrapSandbox",
        _FakeSandbox,
    )
    return BenchmarkRunner(ROOT, tmp_path / "data")


def _benchmark():
    return next(
        benchmark
        for benchmark in load_manifest(
            ROOT / "research_benchmark" / "manifest.yaml",
            ROOT,
        )
        if benchmark.benchmark_id == "missing_type_casts"
    )


def test_create_cgroup_sets_resource_limits(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    runner.cgroup_root = tmp_path / "cgroup"
    runner.cgroup_root.mkdir()
    (runner.cgroup_root / "cgroup.controllers").touch()

    directory = runner._create_cgroup("run", "target")

    assert directory is not None
    assert (directory / "memory.max").read_text() == "1073741824"
    assert (directory / "cpu.max").read_text() == "60000 100000"
    assert (directory / "pids.max").read_text() == "128"


def test_create_cgroup_is_optional_when_v2_is_unavailable(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    runner.cgroup_root = tmp_path / "missing-cgroup"

    assert runner._create_cgroup("run", "target") is None


def test_attach_cgroup_writes_process_id_or_raises(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    directory = tmp_path / "cgroup"
    directory.mkdir()
    (directory / "cgroup.procs").touch()
    process = SimpleNamespace(pid=123)

    runner._attach_cgroup(directory, process)
    assert (directory / "cgroup.procs").read_text() == "123"
    runner._attach_cgroup(None, process)

    with pytest.raises(RuntimeError, match="Could not attach"):
        runner._attach_cgroup(tmp_path / "missing", process)


def test_set_resource_limits_applies_all_expected_limits(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(
        "src.execution.runner.resource.setrlimit",
        lambda kind, limits: calls.append((kind, limits)),
    )

    runner._set_resource_limits()

    assert calls == [
        (resource.RLIMIT_CPU, (60, 61)),
        (resource.RLIMIT_AS, (1_073_741_824, 1_073_741_824)),
        (resource.RLIMIT_FSIZE, (104_857_600, 104_857_600)),
        (resource.RLIMIT_NOFILE, (128, 128)),
        (resource.RLIMIT_CORE, (0, 0)),
    ]


def test_run_returns_success_for_zero_exit(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    runner._create_cgroup = lambda run_id, benchmark_id: None
    process = SimpleNamespace(pid=123, returncode=0, wait=lambda timeout: 0)
    monkeypatch.setattr(
        "src.execution.runner.subprocess.Popen",
        lambda *args, **kwargs: process,
    )

    result = runner.run(
        _benchmark(),
        seed=3,
        run_id="runner-success",
        detector_mode="statistical",
    )

    assert result.succeeded
    assert not result.timed_out


def test_run_writes_timeout_report(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    runner._create_cgroup = lambda run_id, benchmark_id: None

    def timeout_wait(timeout):
        raise subprocess.TimeoutExpired("bwrap", timeout)

    process = SimpleNamespace(pid=123, returncode=-15, wait=timeout_wait)
    monkeypatch.setattr(
        "src.execution.runner.subprocess.Popen",
        lambda *args, **kwargs: process,
    )
    monkeypatch.setattr(
        runner,
        "_stop_process_group",
        lambda process: None,
    )

    result = runner.run(
        _benchmark(),
        seed=3,
        run_id="runner-timeout",
        detector_mode="statistical",
    )

    report = (
        tmp_path
        / "data"
        / "reports"
        / "runner-timeout"
        / "missing_type_casts_dashboard.html"
    )
    assert result.timed_out
    assert "Timed out" in report.read_text(encoding="utf-8")


def test_run_reports_spawn_errors(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    runner._create_cgroup = lambda run_id, benchmark_id: None

    def fail_to_spawn(*args, **kwargs):
        raise OSError("sandbox unavailable")

    monkeypatch.setattr(
        "src.execution.runner.subprocess.Popen",
        fail_to_spawn,
    )

    result = runner.run(
        _benchmark(),
        seed=3,
        run_id="runner-spawn-error",
        detector_mode="statistical",
    )

    error_log = (
        tmp_path / "data" / "logs" / "runner-spawn-error"
        / "missing_type_casts.err"
    )
    assert result.exit_code == 127
    assert "sandbox unavailable" in error_log.read_text(encoding="utf-8")


def test_stop_process_group_escalates_after_timeout(monkeypatch):
    signals = []
    waits = []

    def wait(timeout=None):
        waits.append(timeout)
        if len(waits) == 1:
            raise subprocess.TimeoutExpired("bwrap", timeout)

    process = SimpleNamespace(pid=123, wait=wait)
    monkeypatch.setattr(
        "src.execution.runner.os.killpg",
        lambda pid, sig: signals.append((pid, sig)),
    )

    BenchmarkRunner._stop_process_group(process)

    assert signals == [
        (123, signal.SIGTERM),
        (123, signal.SIGKILL),
    ]
    assert waits == [2, None]


def test_stop_process_group_tolerates_process_already_exited(monkeypatch):
    process = SimpleNamespace(pid=123, wait=lambda timeout=None: 0)

    def missing_process(pid, sig):
        raise ProcessLookupError

    monkeypatch.setattr(
        "src.execution.runner.os.killpg",
        missing_process,
    )

    BenchmarkRunner._stop_process_group(process)


@pytest.mark.parametrize("nonempty", [False, True])
def test_run_tolerates_cgroup_cleanup_outcomes(
    tmp_path,
    monkeypatch,
    nonempty,
):
    runner = _runner(tmp_path, monkeypatch)
    directory = tmp_path / "cgroup"
    directory.mkdir()
    if nonempty:
        (directory / "busy").touch()
    runner._create_cgroup = lambda run_id, benchmark_id: directory
    runner._attach_cgroup = lambda cgroup, process: None
    process = SimpleNamespace(pid=123, returncode=0, wait=lambda timeout: 0)
    monkeypatch.setattr(
        "src.execution.runner.subprocess.Popen",
        lambda *args, **kwargs: process,
    )

    result = runner.run(
        _benchmark(),
        seed=3,
        run_id=f"runner-cleanup-{nonempty}",
        detector_mode="statistical",
    )

    assert result.succeeded
    assert directory.exists() is nonempty


def test_failure_report_escapes_untrusted_text(tmp_path):
    output = tmp_path / "failure.html"

    BenchmarkRunner.write_failure_report(
        output,
        "target<script>",
        "<failure>",
    )

    report = output.read_text(encoding="utf-8")
    assert "target&lt;script&gt;" in report
    assert "&lt;failure&gt;" in report
