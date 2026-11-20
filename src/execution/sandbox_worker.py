import argparse
import subprocess
import sys
import time
from pathlib import Path

import requests

from src.detectors.bola import BOLAProbe
from src.execution.manifest import load_manifest
from src.fuzzer import AdvancedBehavioralFuzzer
from src.telemetry.schema import TelemetryEvent
from src.telemetry.writer import TelemetryWriter


def _wait_and_discover(fuzzer, process, port, route, method, timeout):
    spec_url = f"http://127.0.0.1:{port}/swagger.json"
    deadline = time.monotonic() + timeout
    last_error = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Benchmark process exited with status {process.returncode}"
            )
        try:
            response = requests.get(spec_url, timeout=0.5)
        except requests.RequestException as error:
            last_error = error
            time.sleep(0.1)
            continue

        if response.status_code == 200:
            fuzzer.discover_via_spec(spec_url)
            return
        break

    if process.poll() is not None:
        raise RuntimeError(
            f"Benchmark process exited with status {process.returncode}"
        )
    if last_error and time.monotonic() >= deadline:
        raise RuntimeError(f"Benchmark did not become ready: {last_error}")

    blueprint = {
        "query": ["id"] if method == "GET" else [],
        "body_properties": (
            {} if method == "GET" else {"data": {"type": "string"}}
        ),
    }
    fuzzer.endpoints = [
        {
            "path": route,
            "method": method,
            "blueprint": blueprint,
        }
    ]
    fuzzer._collect_baseline(method, route, blueprint)


def _stop_process(process):
    if process.poll() is None:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _run_authorization_scenarios(fuzzer, benchmark, telemetry_writer):
    for scenario in benchmark.authorization_scenarios:
        probe = BOLAProbe(
            fuzzer.base_url,
            scenario.owner_headers,
            scenario.other_user_headers,
        )
        result = probe.probe(
            scenario.route,
            owned_object_id=scenario.owned_object_id,
            object_parameter=scenario.object_parameter,
            object_id_field=scenario.object_id_field,
        )

        if result.vulnerable:
            fuzzer.log_anomaly(
                "BOLA_CROSS_USER_ACCESS",
                result.evidence["other_user_status"],
                "GET",
                scenario.route,
                scenario.owned_object_id,
                result.evidence,
            )

        for principal, role, status_key, duration_key, outcome, anomalies in (
            (
                scenario.owner_identity,
                "owner",
                "owner_status",
                "owner_duration_ms",
                "owner_object_confirmed"
                if result.evidence["owner_object_match"]
                else "owner_object_not_confirmed",
                [],
            ),
            (
                scenario.other_user_identity,
                "other",
                "other_user_status",
                "other_user_duration_ms",
                "cross_user_access"
                if result.evidence["other_user_object_match"]
                else "access_denied",
                ["BOLA_CROSS_USER_ACCESS"] if result.vulnerable else [],
            ),
        ):
            telemetry_writer.append(
                TelemetryEvent.create(
                    run_id=fuzzer.run_id,
                    benchmark_id=fuzzer.benchmark_id,
                    request_id=(
                        f"{fuzzer.run_id}-{scenario.scenario_id}-{role}"
                    ),
                    seed=fuzzer.seed,
                    detector_mode=fuzzer.detector_mode,
                    method="GET",
                    route=scenario.route,
                    status=result.evidence[status_key],
                    duration_ms=result.evidence[duration_key],
                    outcome=outcome,
                    anomalies=anomalies,
                    principal=principal,
                )
            )

        if result.vulnerable != scenario.expected_vulnerable:
            raise RuntimeError(
                f"Authorization scenario {scenario.scenario_id} expected "
                f"vulnerable={scenario.expected_vulnerable}, observed "
                f"{result.vulnerable}"
            )


def run_target(args):
    if not Path(args.entrypoint).is_file():
        raise FileNotFoundError(args.entrypoint)

    data_root = Path("data")
    logs_directory = data_root / "logs" / args.run_id
    reports_directory = data_root / "reports" / args.run_id
    raw_directory = data_root / "raw"
    logs_directory.mkdir(parents=True, exist_ok=True)
    reports_directory.mkdir(parents=True, exist_ok=True)
    raw_directory.mkdir(parents=True, exist_ok=True)

    fuzzer = AdvancedBehavioralFuzzer(
        base_url=f"http://127.0.0.1:{args.port}",
        max_workers=1,
        seed=args.seed,
        benchmark_id=args.benchmark_id,
        run_id=args.run_id,
        detector_mode=args.detector_mode,
        telemetry_writer=TelemetryWriter(
            raw_directory / f"{args.run_id}.jsonl"
        ),
    )
    benchmark = next(
        item
        for item in load_manifest("/research_benchmark/manifest.yaml", "/")
        if item.benchmark_id == args.benchmark_id
    )
    stdout_path = logs_directory / f"{args.benchmark_id}.out"
    stderr_path = logs_directory / f"{args.benchmark_id}.err"
    error = None

    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            [sys.executable, "-B", args.entrypoint],
            stdout=stdout,
            stderr=stderr,
        )
        try:
            _wait_and_discover(
                fuzzer,
                process,
                args.port,
                args.route,
                args.method,
                args.startup_timeout,
            )
            fuzzer.run_fuzz_session(total_runs=args.runs)
            _run_authorization_scenarios(
                fuzzer,
                benchmark,
                fuzzer.telemetry_writer,
            )
            if process.poll() not in (None, 0):
                raise RuntimeError(
                    f"Benchmark process exited with status {process.returncode}"
                )
        except Exception as failure:
            error = failure
            fuzzer.log_anomaly(
                "RUN_FAILED",
                0,
                args.method,
                args.route,
                "RUN",
                repr(failure),
            )
        finally:
            _stop_process(process)

    fuzzer.generate_web_dashboard(
        reports_directory / f"{args.benchmark_id}_dashboard.html",
        run_status="failed" if error else "completed",
    )
    if error:
        print(f"Benchmark failed: {error}", file=sys.stderr)
        return 1
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--runs", required=True, type=int)
    parser.add_argument("--startup-timeout", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--detector-mode",
        required=True,
        choices=["statistical", "statistical+fingerprint"],
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run_target(parse_args()))
