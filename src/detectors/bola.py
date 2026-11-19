from dataclasses import dataclass
import requests


@dataclass(frozen=True)
class BOLAResult:
    vulnerable: bool
    evidence: dict


class BOLAProbe:
    def __init__(
        self,
        base_url,
        owner_headers,
        unauthorized_headers,
        timeout=3,
    ):
        self.base_url = base_url.rstrip("/")
        self.owner_headers = owner_headers
        self.unauthorized_headers = unauthorized_headers
        self.timeout = timeout

    def probe(self, route, method="GET", owned_object_id=None,
              object_parameter="id"):
        owner_payload = {
            object_parameter: owned_object_id,
        } if owned_object_id is not None else None

        unauthorized_payload = dict(owner_payload or {})

        owner_response = self._request(
            method,
            route,
            owner_payload,
            self.owner_headers,
        )
        unauthorized_response = self._request(
            method,
            route,
            unauthorized_payload,
            self.unauthorized_headers,
        )

        owner_authorized = 200 <= owner_response.status_code < 300
        unauthorized_success = 200 <= unauthorized_response.status_code < 300

        vulnerable = owner_authorized and unauthorized_success

        return BOLAResult(
            vulnerable=vulnerable,
            evidence={
                "route": route,
                "object_id": owned_object_id,
                "owner_status": owner_response.status_code,
                "unauthorized_status": unauthorized_response.status_code,
                "owner_body_sha256": self._sha256(owner_response.content),
                "unauthorized_body_sha256": self._sha256(
                    unauthorized_response.content
                ),
                "owner_body": owner_response.text[:500],
                "unauthorized_body": unauthorized_response.text[:500],
            },
        )

    def _request(self, method, route, payload, headers):
        kwargs = {
            "timeout": self.timeout,
            "headers": headers,
        }

        if method.upper() in {"POST", "PUT", "PATCH"}:
            kwargs["json"] = payload or {}
        else:
            kwargs["params"] = payload or {}

        return requests.request(method, f"{self.base_url}{route}", **kwargs)

    @staticmethod
    def _sha256(value):
        import hashlib
        return hashlib.sha256(value or b"").hexdigest()
