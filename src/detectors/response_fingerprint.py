import hashlib
from collections import Counter


class ResponseFingerprintDetector:
    def __init__(self, minimum_samples=12, dominant_ratio=0.80):
        self.minimum_samples = minimum_samples
        self.dominant_ratio = dominant_ratio
        self.signatures = {}

    def detect(self, key, status, content):
        signature = (
            status,
            hashlib.sha256(content or b"").hexdigest(),
        )
        counter = self.signatures.setdefault(key, Counter())
        counter[signature] += 1

        total = sum(counter.values())
        dominant_count = counter.most_common(1)[0][1]

        if (
            total >= self.minimum_samples
            and dominant_count / total > self.dominant_ratio
        ):
            return ["INPUT_IGNORED_OR_FILTERED"]

        return []
