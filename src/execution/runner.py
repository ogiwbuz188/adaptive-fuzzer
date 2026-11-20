from dataclasses import dataclass
import html
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
import uuid

from .manifest import Benchmark
from .sandbox import BubblewrapSandbox


@dataclass(frozen=True)
class RunResult:
    benchmark_id: str
    exit_code: int
    duration_seconds: float
    timed_out: bool

    @property
    def succeeded(self):
        return self.exit_code == 0 and not self.timed_out


class BenchmarkRunner:
    def __init__(
        self,
        repository_root,
        data_directory,
        memory_limit_bytes=1_073_741_824,
        cpu_limit_seconds=60,
        file_limit_bytes=104_857_600,
    ):
        self.repository_root = Path(repository_root).resolve()
        self.data_directory = Path(data_directory).resolve()
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.sandbox = BubblewrapSandbox(
            self.repository_root,
            self.data_directory,
        )
        self.memory_limit_bytes = memory_limit_bytes
        self.cpu_limit_seconds = cpu_limit_seconds
        self.file_limit_bytes = file_limit_bytes
        self.cgroup_root = Path("/sys/fs/cgroup")
        self.cgroup_directory = None

    def _create_cgroup(self, run_id, benchmark_id):
        if not (self.cgroup_root / "cgroup.controllers").is_file():
            return None
        try:
            parent = self.cgroup_root / "adaptive-fuzzer"
            parent.mkdir(parents=True, exist_ok=True)
            directory = parent / (
                f"{run_id}-{benchmark_id}-{uuid.uuid4().hex[:8]}"
            )
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "memory.max").write_text(
                str(self.memory_limit_bytes),
                encoding="ascii",
            )
            quota = min(self.cpu_limit_seconds, 60) * 1000
            (directory / "cpu.max").write_text(
                f"{quota} 100000",
                encoding="ascii",
            )
            (directory / "pids.max").write_text("128", encoding="ascii")
            return directory
        except (OSError, PermissionError):
            return None

    def _attach_cgroup(self, directory, process):
        if directory is None:
            return
        try:
            (directory / "cgroup.procs").write_text(
                str(process.pid),
                encoding="ascii",
            )
        except (OSError, PermissionError) as error:
            raise RuntimeError(
                f"Could not attach benchmark process to cgroup: {error}"
            )

    def run(self, benchmark, seed, run_id, detector_mode):
        if not isinstance(benchmark, Benchmark):
            raise TypeError("benchmark must be a Benchmark")

        logs_directory = self.data_directory / "logs" / run_id
        reports_directory = self.data_directory / "reports" / run_id
        logs_directory.mkdir(parents=True, exist_ok=True)
        reports_directory.mkdir(parents=True, exist_ok=True)
        stdout_path = logs_directory / f"{benchmark.benchmark_id}.out"
        stderr_path = logs_directory / f"{benchmark.benchmark_id}.err"
        report_path = reports_directory / (
            f"{benchmark.benchmark_id}_dashboard.html"
        )

        command = self.sandbox.build_command(
            benchmark,
            seed,
            run_id,
            detector_mode,
        )
        started = time.monotonic()
        timed_out = False

        try:
            with stdout_path.open("wb") as stdout, stderr_path.open(
                "wb"
            ) as stderr:
                cgroup_directory = self._create_cgroup(
                    run_id,
                    benchmark.benchmark_id,
                )
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=self.repository_root,
                        stdout=stdout,
                        stderr=stderr,
                        start_new_session=True,
                        preexec_fn=self._set_resource_limits,
                    )
                    self._attach_cgroup(cgroup_directory, process)
                    try:
                        exit_code = process.wait(
                            timeout=benchmark.timeout_seconds
                        )
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        self._stop_process_group(process)
                        exit_code = process.returncode or 124
                finally:
                    if cgroup_directory is not None:
                        try:
                            cgroup_directory.rmdir()
                        except (OSError, PermissionError):
                            pass
        except OSError as error:
            exit_code = 127
            stderr_path.write_text(str(error), encoding="utf-8")

        duration = time.monotonic() - started
        if exit_code != 0 and not report_path.exists():
            self.write_failure_report(
                report_path,
                benchmark.benchmark_id,
                "Timed out" if timed_out else f"Runner exited with status {exit_code}",
            )

        return RunResult(
            benchmark_id=benchmark.benchmark_id,
            exit_code=exit_code,
            duration_seconds=duration,
            timed_out=timed_out,
        )

    def _set_resource_limits(self):
        cpu_seconds = min(self.cpu_limit_seconds, 60)
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cpu_seconds, cpu_seconds + 1),
        )
        resource.setrlimit(
            resource.RLIMIT_AS,
            (self.memory_limit_bytes, self.memory_limit_bytes),
        )
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (self.file_limit_bytes, self.file_limit_bytes),
        )
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    @staticmethod
    def _stop_process_group(process):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

    @staticmethod
    def write_failure_report(path, benchmark_id, message):
        report = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="run-status" content="failed">
<title>Benchmark run failed: {html.escape(benchmark_id)}</title></head>
<body><h1>Benchmark run failed</h1>
<p>Benchmark: {html.escape(benchmark_id)}</p>
<pre>{html.escape(message)}</pre></body></html>
"""
        Path(path).write_text(report, encoding="utf-8")
