
from src.detectors.response_fingerprint import ResponseFingerprintDetector


def test_dominant_response_is_filtered():
    detector = ResponseFingerprintDetector(minimum_samples=3, dominant_ratio=0.75)

    assert detector.detect("GET /items", 200, b'{"ok":true}') == []
    assert detector.detect("GET /items", 200, b'{"ok":true}') == []
    result = detector.detect("GET /items", 200, b'{"ok":true}')

    assert result == ["INPUT_IGNORED_OR_FILTERED"]
