from dataclasses import asdict, dataclass
from datetime import datetime, timezone


def _truncate_sample(value, limit=512):
    if value is None:
        return None
    if isinstance(value, bytes):
        encoded = value[:limit]
    else:
        encoded = str(value).encode("utf-8")[:limit]
    return encoded.decode("utf-8", errors="ignore")


@dataclass(frozen=True)
class TelemetryEvent:
    run_id: str
    benchmark_id: str
    request_id: str
    seed: int
    detector_mode: str
    method: str
    route: str
    status: int
    duration_ms: float
    outcome: str
    anomalies: tuple[str, ...]
    timestamp: str
    principal: str | None = None
    payload_sample: str | None = None
    response_snippet: str | None = None
    schema_version: int = 2

    @classmethod
    def create(
        cls,
        run_id,
        benchmark_id,
        request_id,
        seed,
        detector_mode,
        method,
        route,
        status,
        duration_ms,
        outcome,
        anomalies,
        principal=None,
        payload_sample=None,
        response_snippet=None,
    ):
        if not all((run_id, benchmark_id, request_id, method, route, outcome)):
            raise ValueError("Telemetry event identifiers and outcome are required")
        if not isinstance(status, int):
            raise ValueError("status must be an integer")
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")

        return cls(
            run_id=str(run_id),
            benchmark_id=str(benchmark_id),
            request_id=str(request_id),
            seed=int(seed),
            detector_mode=str(detector_mode),
            method=str(method).upper(),
            route=str(route),
            status=status,
            duration_ms=float(duration_ms),
            outcome=str(outcome),
            anomalies=tuple(sorted(set(anomalies))),
            timestamp=datetime.now(timezone.utc).isoformat(),
            principal=principal,
            payload_sample=_truncate_sample(payload_sample),
            response_snippet=_truncate_sample(response_snippet),
        )

    def as_dict(self):
        record = asdict(self)
        record["anomalies"] = list(self.anomalies)
        return record
