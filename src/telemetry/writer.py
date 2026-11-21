import json
from pathlib import Path
import threading

from .schema import TelemetryEvent


class TelemetryWriter:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def append(self, event):
        if not isinstance(event, TelemetryEvent):
            raise TypeError("event must be a TelemetryEvent")
        serialized = json.dumps(event.as_dict(), sort_keys=True)
        with self.lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(serialized + "\n")


def write_run_manifest(path, run_id, metadata):
    """Record environment metadata for a run without discarding earlier runs."""
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with _manifest_lock:
        if manifest_path.exists():
            with manifest_path.open(encoding="utf-8") as handle:
                document = json.load(handle)
            if not isinstance(document, dict) or not isinstance(
                document.get("runs"), dict
            ):
                raise ValueError(f"Invalid run manifest structure: {manifest_path}")
        else:
            document = {"schema_version": 1, "runs": {}}
        document["runs"][str(run_id)] = metadata
        temporary_path = manifest_path.with_suffix(
            manifest_path.suffix + ".tmp"
        )
        temporary_path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(manifest_path)


_manifest_lock = threading.Lock()
