from pathlib import Path
import shutil
import sys


class BubblewrapSandbox:
    def __init__(self, repository_root, data_directory, executable=None):
        if sys.platform != "linux":
            raise RuntimeError("The Bubblewrap sandbox requires Linux")

        self.repository_root = Path(repository_root).resolve()
        self.benchmark_root = self.repository_root / "research_benchmark"
        self.data_directory = Path(data_directory).resolve()
        self.executable = executable or shutil.which("bwrap")
        if not self.executable or not Path(self.executable).is_file():
            raise RuntimeError(
                "Bubblewrap is required; refusing to run benchmarks unsandboxed"
            )

        self.data_directory.mkdir(parents=True, exist_ok=True)

    def build_command(self, benchmark, seed, run_id, detector_mode):
        if not benchmark.entrypoint.is_relative_to(self.benchmark_root):
            raise ValueError("Benchmark entrypoint must remain under research_benchmark")

        python_path, runtime_bind = self._python_mount()
        target_path = (
            Path("/research_benchmark")
            / benchmark.entrypoint.relative_to(self.benchmark_root)
        )
        command = [
            self.executable,
            "--unshare-all",
            "--die-with-parent",
            "--new-session",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--dir",
            "/etc",
            "--ro-bind",
            "/etc/ssl",
            "/etc/ssl",
            "--ro-bind",
            "/etc/hosts",
            "/etc/hosts",
            "--ro-bind",
            "/etc/ld.so.cache",
            "/etc/ld.so.cache",
            "--dir",
            "/app",
            "--ro-bind",
            self.repository_root / "src",
            "/app/src",
            "--ro-bind",
            self.benchmark_root,
            "/research_benchmark",
            "--dir",
            "/workspace",
            "--bind",
            self.data_directory,
            "/workspace/data",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--chdir",
            "/workspace",
            "--clearenv",
            "--setenv",
            "PATH",
            "/runtime/bin:/usr/bin",
            "--setenv",
            "PYTHONPATH",
            "/app",
            "--setenv",
            "PYTHONNOUSERSITE",
            "1",
            "--setenv",
            "HOME",
            "/tmp",
        ]
        if runtime_bind:
            command.extend(["--ro-bind", runtime_bind[0], runtime_bind[1]])

        command.extend(
            [
                "--",
                python_path,
                "-B",
                "-m",
                "src.execution.sandbox_worker",
                "--entrypoint",
                str(target_path),
                "--benchmark-id",
                benchmark.benchmark_id,
                "--route",
                benchmark.route,
                "--method",
                benchmark.method,
                "--port",
                str(benchmark.port),
                "--runs",
                str(benchmark.runs),
                "--startup-timeout",
                str(benchmark.startup_timeout_seconds),
                "--seed",
                str(seed),
                "--run-id",
                run_id,
                "--detector-mode",
                detector_mode,
            ]
        )
        return [str(part) for part in command]

    @staticmethod
    def _python_mount():
        prefix = Path(sys.prefix).resolve()
        base_prefix = Path(sys.base_prefix).resolve()
        executable = Path(sys.executable).resolve()

        if prefix == base_prefix:
            if executable.is_relative_to(Path("/usr")):
                return str(executable), None
            if executable.is_relative_to(prefix):
                relative_executable = executable.relative_to(prefix)
                return f"/runtime/{relative_executable}", (prefix, "/runtime")
            raise RuntimeError("Python executable is outside its runtime prefix")

        if not executable.is_relative_to(prefix):
            raise RuntimeError("Python executable is outside the active virtualenv")

        relative_executable = executable.relative_to(prefix)
        return f"/runtime/{relative_executable}", (prefix, "/runtime")
