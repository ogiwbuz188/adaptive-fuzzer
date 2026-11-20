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
