class PathTraversalOracle:
    """Detect disclosure of a per-run synthetic canary in a response body."""

    def __init__(self, canary_token):
        if not isinstance(canary_token, str) or not canary_token:
            raise ValueError("canary_token must be a non-empty string")
        self._canary = canary_token.encode("utf-8")

    def detect(self, response_body):
        if isinstance(response_body, str):
            response_body = response_body.encode("utf-8")
        if not isinstance(response_body, bytes):
            raise TypeError("response_body must be bytes or text")
        return self._canary in response_body
