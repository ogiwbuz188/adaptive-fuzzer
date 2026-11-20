from dataclasses import dataclass
import hashlib
import ipaddress
import time
from urllib.parse import urlsplit

import requests


@dataclass(frozen=True)
class BOLAResult:
    vulnerable: bool
    evidence: dict[str, object]


class BOLAProbe:
    """Compare read access to one known object using two local user identities."""

    def __init__(
        self,
        base_url,
        owner_headers,
        other_user_headers,
        timeout=3,
    ):
        parsed_url = urlsplit(base_url)
        hostname = parsed_url.hostname
        is_loopback = hostname == "localhost"
        if hostname and not is_loopback:
            try:
                is_loopback = ipaddress.ip_address(hostname).is_loopback
            except ValueError:
                is_loopback = False

        if (
            parsed_url.scheme not in {"http", "https"}
            or not is_loopback
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.query
            or parsed_url.fragment
            or parsed_url.path not in {"", "/"}
        ):
            raise ValueError("BOLAProbe is restricted to a loopback base URL")
        if not owner_headers or not other_user_headers:
            raise ValueError("Headers for both authenticated users are required")
        normalized_owner_headers = {
            key.lower(): value for key, value in owner_headers.items()
        }
        normalized_other_headers = {
            key.lower(): value for key, value in other_user_headers.items()
        }
        if normalized_owner_headers == normalized_other_headers:
            raise ValueError("Owner and other-user credentials must be distinct")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.base_url = base_url.rstrip("/")
        self.owner_headers = dict(owner_headers)
        self.other_user_headers = dict(other_user_headers)
        self.timeout = timeout

    def probe(self, route, owned_object_id, object_parameter="id",
              object_id_field="id"):
        if owned_object_id is None:
            raise ValueError("owned_object_id is required")
        parsed_route = urlsplit(route)
        if (
            not route.startswith("/")
            or route.startswith("//")
            or parsed_route.scheme
            or parsed_route.netloc
            or parsed_route.query
            or parsed_route.fragment
        ):
            raise ValueError("route must be a relative path beginning with '/'")
        if not object_parameter or not object_id_field:
            raise ValueError("object parameter and response ID field are required")

        owner_started = time.monotonic()
        owner_response = self._request(
            route,
            owned_object_id,
            object_parameter,
            self.owner_headers,
        )
        owner_duration = time.monotonic() - owner_started
        other_user_started = time.monotonic()
        other_user_response = self._request(
            route,
            owned_object_id,
            object_parameter,
            self.other_user_headers,
        )
        other_user_duration = time.monotonic() - other_user_started

        owner_authorized = 200 <= owner_response.status_code < 300
        other_user_authorized = 200 <= other_user_response.status_code < 300
        owner_object_match = self._contains_object_id(
            owner_response,
            object_id_field,
            owned_object_id,
        )
        other_user_object_match = self._contains_object_id(
            other_user_response,
            object_id_field,
            owned_object_id,
        )
        vulnerable = (
            owner_authorized
            and owner_object_match
            and other_user_authorized
            and other_user_object_match
        )

        return BOLAResult(
            vulnerable=vulnerable,
            evidence={
                "route": route,
                "object_id": str(owned_object_id),
                "owner_status": owner_response.status_code,
                "other_user_status": other_user_response.status_code,
                "owner_duration_ms": owner_duration * 1000,
                "other_user_duration_ms": other_user_duration * 1000,
                "owner_object_match": owner_object_match,
                "other_user_object_match": other_user_object_match,
                "owner_body_sha256": self._sha256(owner_response.content),
                "other_user_body_sha256": self._sha256(
                    other_user_response.content
                ),
            },
        )

    def _request(self, route, object_id, object_parameter, headers):
        response = requests.get(
            f"{self.base_url}{route}",
            params={object_parameter: object_id},
            timeout=self.timeout,
            headers=headers,
            allow_redirects=False,
        )
        return response

    @staticmethod
    def _contains_object_id(response, field_name, object_id):
        try:
            body = response.json()
        except ValueError:
            return False

        expected = str(object_id)

        def find_id(value):
            if isinstance(value, dict):
                return any(
                    (key == field_name and str(item) == expected)
                    or find_id(item)
                    for key, item in value.items()
                )
            if isinstance(value, list):
                return any(find_id(item) for item in value)
            return False

        return find_id(body)

    @staticmethod
    def _sha256(value):
        return hashlib.sha256(value or b"").hexdigest()
