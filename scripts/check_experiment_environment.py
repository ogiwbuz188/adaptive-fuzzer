import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def git_output(*arguments):
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _command_output(*command):
    if not shutil.which(command[0]):
        return None
    try:
        return subprocess.run(
            list(command),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _memory_bytes():
    try:
        with open("/proc/meminfo", encoding="ascii") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


def _cpu_model():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as handle:
            for line in handle:
                if line.lower().startswith(("model name", "hardware")):
                    return line.split(":", 1)[1].strip()
    except (OSError, IndexError):
        pass
    return platform.processor() or None


def collect_environment(master_seed=None, detector_mode=None):
    try:
        pip_freeze = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"Could not capture pip freeze: {error}") from error

    source_commit = git_output("rev-parse", "HEAD")
    package_names = ("pytest", "PyYAML", "requests", "matplotlib")
    packages = {}
    for name in package_names:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None

    snapshot = {
        "source_commit": source_commit,
        "git_commit": source_commit,
        "git_dirty": bool(git_output("status", "--porcelain")),
        "python_version": sys.version,
        "python": sys.version,
        "pip_freeze": pip_freeze,
        "os_kernel": platform.release(),
        "platform": platform.platform(),
        "bubblewrap_version": _command_output("bwrap", "--version"),
        "bubblewrap": shutil.which("bwrap"),
        "restler": shutil.which("restler") or shutil.which("Restler"),
        "packages": packages,
        "cpu": {
            "count": os.cpu_count(),
            "model": _cpu_model(),
        },
        "memory_bytes": _memory_bytes(),
    }
    if master_seed is not None:
        snapshot["master_seed"] = master_seed
    if detector_mode is not None:
        snapshot["detector_mode"] = detector_mode
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write a reproducible experiment environment snapshot.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--master-seed", type=int)
    parser.add_argument("--detector-mode")
    args = parser.parse_args(argv)

    snapshot = collect_environment(args.master_seed, args.detector_mode)
    print(json.dumps(snapshot, indent=2, sort_keys=True) if args.json else "\n".join(
        f"{key}={value}" for key, value in snapshot.items()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
