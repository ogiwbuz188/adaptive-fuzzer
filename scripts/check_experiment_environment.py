import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys


def git_output(*arguments):
    try:
        return subprocess.run(
            ["git", *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write a reproducible experiment environment snapshot.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    packages = {}
    for name in ("pytest", "PyYAML", "requests", "matplotlib"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None

    snapshot = {
        "git_commit": git_output("rev-parse", "HEAD"),
        "git_dirty": bool(git_output("status", "--porcelain")),
        "python": sys.version,
        "platform": platform.platform(),
        "bubblewrap": shutil.which("bwrap"),
        "restler": shutil.which("restler") or shutil.which("Restler"),
        "packages": packages,
    }
    print(json.dumps(snapshot, indent=2, sort_keys=True) if args.json else "\n".join(
        f"{key}={value}" for key, value in snapshot.items()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
