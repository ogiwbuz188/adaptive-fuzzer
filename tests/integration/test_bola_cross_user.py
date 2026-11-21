from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from urllib.parse import parse_qs, urlsplit

import pytest

from src.detectors.bola import BOLAProbe


@contextmanager
def local_object_service(
    other_user_can_read=False,
    generic_success=False,
    other_object_id=42,
):
    observed_requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlsplit(self.path).query)
            user = self.headers.get("Authorization")
            observed_requests.append((user, query.get("id", [None])[0]))

            path = urlsplit(self.path).path
            if path == "/api/v1/redirect":
                self.send_response(302)
                self.send_header("Location", "https://redirect.invalid/")
                self.end_headers()
                return
            if path != "/api/v1/objects":
                status, body = 404, {"error": "not found"}
            elif user == "Bearer owner":
                status, body = 200, {"id": "42", "value": "owner's object"}
            elif user == "Bearer other" and other_user_can_read:
                status = 200
                body = {"message": "ok"} if generic_success else {
                    "id": str(other_object_id),
                    "value": "owner's object",
                }
            else:
                status, body = 403, {"error": "forbidden"}

            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format_string, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", observed_requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def build_probe(base_url):
    return BOLAProbe(
        base_url,
        {"Authorization": "Bearer owner"},
        {"Authorization": "Bearer other"},
    )


def test_known_object_is_compared_for_owner_then_other_authenticated_user():
    with local_object_service(other_user_can_read=True) as (base_url, observed):
        result = build_probe(base_url).probe(
            "/api/v1/objects",
            owned_object_id=42,
        )

    assert result.vulnerable is True
    assert result.evidence["owner_object_match"] is True
    assert result.evidence["other_user_object_match"] is True
    assert observed == [
        ("Bearer owner", "42"),
        ("Bearer other", "42"),
    ]


def test_denied_other_user_access_is_not_reported_as_bola():
    with local_object_service() as (base_url, _):
        result = build_probe(base_url).probe(
            "/api/v1/objects",
            owned_object_id=42,
        )

    assert result.vulnerable is False
    assert result.evidence["owner_object_match"] is True
    assert result.evidence["other_user_status"] == 403
    assert result.evidence["other_user_object_match"] is False


def test_generic_success_response_does_not_prove_object_access():
    with local_object_service(
        other_user_can_read=True,
        generic_success=True,
    ) as (base_url, _):
        result = build_probe(base_url).probe(
            "/api/v1/objects",
            owned_object_id=42,
        )

    assert result.vulnerable is False
    assert result.evidence["other_user_status"] == 200
    assert result.evidence["other_user_object_match"] is False


def test_access_to_a_different_object_does_not_prove_bola():
    with local_object_service(
        other_user_can_read=True,
        other_object_id=43,
    ) as (base_url, _):
        result = build_probe(base_url).probe(
            "/api/v1/objects",
            owned_object_id=42,
        )

    assert result.vulnerable is False
    assert result.evidence["other_user_object_match"] is False


def test_probe_does_not_follow_redirects():
    with local_object_service(other_user_can_read=True) as (base_url, _):
        result = build_probe(base_url).probe(
            "/api/v1/redirect",
            owned_object_id=42,
        )

    assert result.vulnerable is False
    assert result.evidence["owner_status"] == 302
    assert result.evidence["other_user_status"] == 302


def test_probe_requires_distinct_user_credentials_and_known_object():
    with pytest.raises(ValueError, match="distinct"):
        BOLAProbe(
            "http://localhost",
            {"Authorization": "Bearer same"},
            {"Authorization": "Bearer same"},
        )
    with pytest.raises(ValueError, match="distinct"):
        BOLAProbe(
            "http://localhost",
            {"Authorization": "Bearer same"},
            {"authorization": "Bearer same"},
        )

    probe = build_probe("http://localhost")
    with pytest.raises(ValueError, match="owned_object_id"):
        probe.probe("/api/v1/objects", owned_object_id=None)
    with pytest.raises(ValueError, match="route"):
        probe.probe("https://example.com/api/items", owned_object_id=42)
    with pytest.raises(ValueError, match="object parameter"):
        probe.probe(
            "/api/v1/objects",
            owned_object_id=42,
            object_parameter="",
        )

    with pytest.raises(ValueError, match="Headers for both"):
        BOLAProbe("http://localhost", {}, {"Authorization": "Bearer other"})
    with pytest.raises(ValueError, match="timeout"):
        BOLAProbe(
            "http://localhost",
            {"Authorization": "Bearer owner"},
            {"Authorization": "Bearer other"},
            timeout=0,
        )


def test_probe_refuses_non_loopback_targets():
    with pytest.raises(ValueError, match="loopback"):
        BOLAProbe(
            "https://example.com",
            {"Authorization": "Bearer owner"},
            {"Authorization": "Bearer other"},
        )


def test_object_id_can_be_confirmed_inside_response_arrays():
    class Response:
        def json(self):
            return {"objects": [{"id": "42"}]}

    assert BOLAProbe._contains_object_id(Response(), "id", 42)
