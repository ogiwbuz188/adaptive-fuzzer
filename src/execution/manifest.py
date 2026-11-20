from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class AuthorizationScenario:
    scenario_id: str
    route: str
    owner_identity: str
    other_user_identity: str
    owned_object_id: str
    object_parameter: str
    object_id_field: str
    owner_headers: dict[str, str]
    other_user_headers: dict[str, str]
    expected_vulnerable: bool


@dataclass(frozen=True)
class Benchmark:
    benchmark_id: str
    category: str
    entrypoint: Path
    route: str
    method: str
    port: int
    runs: int
    startup_timeout_seconds: int
    timeout_seconds: int
    authorization_scenarios: tuple[AuthorizationScenario, ...] = ()


def load_manifest(path, repository_root):
    manifest_path = Path(path)
    if not manifest_path.is_absolute():
        manifest_path = Path(repository_root) / manifest_path

    with manifest_path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict) or document.get("version") != 1:
        raise ValueError("Manifest must be a version 1 mapping")

    entries = document.get("benchmarks")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Manifest must contain at least one benchmark")

    repository_root = Path(repository_root).resolve()
    benchmark_root = repository_root / "research_benchmark"
    benchmarks = []
    seen_ids = set()
    seen_entrypoints = set()

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each benchmark manifest entry must be a mapping")

        benchmark_id = entry.get("id")
        category = entry.get("category")
        entrypoint = entry.get("entrypoint")
        route = entry.get("route")
        method = entry.get("method")
        if not all(
            isinstance(value, str) and value
            for value in (benchmark_id, category, entrypoint, route, method)
        ):
            raise ValueError("Benchmark entries require id, category, entrypoint, route, and method")
        if benchmark_id in seen_ids:
            raise ValueError(f"Duplicate benchmark ID: {benchmark_id}")
        if not route.startswith("/"):
            raise ValueError(f"Route for {benchmark_id} must start with '/'")
        method = method.upper()
        if method not in {"GET", "POST", "PUT", "DELETE"}:
            raise ValueError(f"Unsupported method for {benchmark_id}: {method}")
        scenarios = entry.get("authorization_scenarios", [])
        if not isinstance(scenarios, list):
            raise ValueError(
                f"authorization_scenarios for {benchmark_id} must be a list"
            )

        target = (repository_root / entrypoint).resolve()
        if not target.is_relative_to(benchmark_root) or not target.is_file():
            raise ValueError(f"Invalid benchmark entrypoint for {benchmark_id}")
        if target.suffix != ".py":
            raise ValueError(f"Benchmark entrypoint must be Python: {benchmark_id}")

        seen_ids.add(benchmark_id)
        seen_entrypoints.add(target)
        scenarios = tuple(
            _load_authorization_scenario(scenario, benchmark_id)
            for scenario in scenarios
        )
        port = _positive_int(entry, "port", benchmark_id)
        if port > 65535:
            raise ValueError(f"port for {benchmark_id} must be at most 65535")
        benchmarks.append(
            Benchmark(
                benchmark_id=str(benchmark_id),
                category=str(category),
                entrypoint=target,
                route=route,
                method=method,
                port=port,
                runs=_positive_int(entry, "runs", benchmark_id),
                startup_timeout_seconds=_positive_int(
                    entry,
                    "startup_timeout_seconds",
                    benchmark_id,
                ),
                timeout_seconds=_positive_int(
                    entry,
                    "timeout_seconds",
                    benchmark_id,
                ),
                authorization_scenarios=scenarios,
            )
        )

    if len(seen_entrypoints) != len(benchmarks):
        raise ValueError("Manifest contains duplicate benchmark entrypoints")
    return benchmarks


def _positive_int(entry, key, benchmark_id):
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} for {benchmark_id} must be a positive integer")
    return value


def _load_authorization_scenario(scenario, benchmark_id):
    required = (
        "scenario_id",
        "route",
        "owner_identity",
        "other_user_identity",
        "owned_object_id",
        "object_parameter",
        "object_id_field",
        "owner_headers",
        "other_user_headers",
        "expected_vulnerable",
    )
    if not isinstance(scenario, dict) or any(
        scenario.get(key) in (None, "") for key in required
    ):
        raise ValueError(f"Incomplete authorization scenario for {benchmark_id}")
    if scenario["owner_identity"] == scenario["other_user_identity"]:
        raise ValueError(f"Scenario identities must differ for {benchmark_id}")
    if not isinstance(scenario["expected_vulnerable"], bool):
        raise ValueError(
            f"Scenario expected_vulnerable must be boolean for {benchmark_id}"
        )
    if not scenario["route"].startswith("/"):
        raise ValueError(f"Scenario route must start with '/' for {benchmark_id}")
    if not isinstance(scenario["owner_headers"], dict) or not isinstance(
        scenario["other_user_headers"],
        dict,
    ):
        raise ValueError(f"Scenario headers must be mappings for {benchmark_id}")
    if {
        key.lower(): value
        for key, value in scenario["owner_headers"].items()
    } == {
        key.lower(): value
        for key, value in scenario["other_user_headers"].items()
    }:
        raise ValueError(
            f"Scenario credentials must be distinct for {benchmark_id}"
        )

    return AuthorizationScenario(
        scenario_id=str(scenario["scenario_id"]),
        route=str(scenario["route"]),
        owner_identity=str(scenario["owner_identity"]),
        other_user_identity=str(scenario["other_user_identity"]),
        owned_object_id=str(scenario["owned_object_id"]),
        object_parameter=str(scenario["object_parameter"]),
        object_id_field=str(scenario["object_id_field"]),
        owner_headers={
            str(key): str(value)
            for key, value in scenario["owner_headers"].items()
        },
        other_user_headers={
            str(key): str(value)
            for key, value in scenario["other_user_headers"].items()
        },
        expected_vulnerable=scenario["expected_vulnerable"],
    )
