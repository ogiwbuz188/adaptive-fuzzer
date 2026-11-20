from pathlib import Path
import shutil
import sys


_PREMOUNTED_PREFIXES = tuple(map(Path, ("/usr", "/lib", "/lib64")))


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

        python_path, runtime_binds = self._python_mount()
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
            f"{Path(python_path).parent}:/usr/bin:/bin",
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
        for source, destination in runtime_binds:
            # bwrap does not guarantee that arbitrary host-prefix parent
            # directories exist in its new root. Create them before mounting.
            for parent in _missing_mount_parents(destination):
                command.extend(["--dir", str(parent)])
            command.extend(["--dir", str(destination)])
            command.extend(["--ro-bind", str(source), str(destination)])

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
        """Return the host interpreter path and runtime prefixes to bind.

        Mount Python at its original absolute prefix. Relocating it to a new
        path breaks Python installations whose compiled-in prefix or
        ``pyvenv.cfg`` refers to the host path (notably setup-python's toolcache).
        """
        prefix = Path(sys.prefix).resolve()
        base_prefix = Path(sys.base_prefix).resolve()
        executable = Path(sys.executable).resolve()
        if not executable.is_file():
            raise RuntimeError(f"Python executable does not exist: {executable}")
        if not executable.is_relative_to(prefix):
            raise RuntimeError("Python executable is outside its runtime prefix")

        prefixes = []
        for candidate in (base_prefix, prefix):
            if any(candidate == mounted or candidate.is_relative_to(mounted)
                   for mounted in _PREMOUNTED_PREFIXES):
                continue
            if candidate not in prefixes:
                prefixes.append(candidate)

        return str(executable), [(candidate, candidate) for candidate in prefixes]


def _missing_mount_parents(destination):
    """List destination ancestors that are not provided by existing root binds."""
    destination = Path(destination)
    parents = []
    current = destination.parent
    while current != Path("/") and not any(
        current == mounted or current.is_relative_to(mounted)
        for mounted in _PREMOUNTED_PREFIXES
    ):
        parents.append(current)
        current = current.parent
    return reversed(parents)
