import statistics
from collections import deque


class StatisticalDetector:
    def __init__(self, z_threshold=2.5, mad_threshold=3.5, drift_threshold=0.25):
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        if mad_threshold <= 0 or drift_threshold <= 0:
            raise ValueError("MAD and drift thresholds must be positive")
        self.z_threshold = z_threshold
        self.mad_threshold = mad_threshold
        self.drift_threshold = drift_threshold
        self.baselines = {}

    def collect(self, key, response_lengths, durations, statuses,
                content_types):
        if not response_lengths:
            raise ValueError("at least one baseline sample is required")
        if not (
            len(response_lengths)
            == len(durations)
            == len(statuses)
        ):
            raise ValueError("baseline sample collections must have equal lengths")

        self.baselines[key] = {
            "length_mean": statistics.mean(response_lengths),
            "length_std": statistics.pstdev(response_lengths),
            "latency_mean": statistics.mean(durations),
            "latency_std": statistics.pstdev(durations),
            "length_median": statistics.median(response_lengths),
            "length_mad": self._mad(response_lengths),
            "latency_median": statistics.median(durations),
            "latency_mad": self._mad(durations),
            "statuses": set(statuses),
            "content_types": set(content_types),
            "length_history": deque(response_lengths, maxlen=32),
            "latency_history": deque(durations, maxlen=32),
        }

    def has_baseline(self, key):
        return key in self.baselines

    def detect(self, key, response_length, duration, status,
               content_type):
        baseline = self.baselines.get(key)
        if not baseline:
            return []

        anomalies = []

        length_z = self._zscore(
            response_length,
            baseline["length_mean"],
            baseline["length_std"],
        )
        latency_z = self._zscore(
            duration,
            baseline["latency_mean"],
            baseline["latency_std"],
        )

        if length_z > self.z_threshold and response_length > baseline["length_mean"]:
            anomalies.append("RESPONSE_SIZE_OUTLIER")
        if latency_z > self.z_threshold and duration > baseline["latency_mean"]:
            anomalies.append("LATENCY_OUTLIER")
        if (
            response_length > baseline["length_median"]
            and self._modified_z(
                response_length,
                baseline["length_median"],
                baseline["length_mad"],
            ) > self.mad_threshold
        ):
            anomalies.append("ROBUST_RESPONSE_SIZE_OUTLIER")
        if (
            duration > baseline["latency_median"]
            and self._modified_z(
                duration,
                baseline["latency_median"],
                baseline["latency_mad"],
            ) > self.mad_threshold
        ):
            anomalies.append("ROBUST_LATENCY_OUTLIER")
        if self._has_drift(baseline["length_history"], response_length):
            anomalies.append("RESPONSE_SIZE_BASELINE_DRIFT")
        if self._has_drift(baseline["latency_history"], duration):
            anomalies.append("LATENCY_BASELINE_DRIFT")
        if status not in baseline["statuses"]:
            anomalies.append("NEW_HTTP_STATUS")
        if content_type not in baseline["content_types"]:
            anomalies.append("CONTENT_TYPE_MISMATCH")

        return anomalies

    @staticmethod
    def _zscore(value, mean, std):
        if std == 0:
            return 0.0 if value == mean else float("inf")
        return abs((value - mean) / std)

    @staticmethod
    def _mad(values):
        median = statistics.median(values)
        return statistics.median(abs(value - median) for value in values)

    @classmethod
    def _modified_z(cls, value, median, mad):
        if mad == 0:
            return 0.0 if value == median else float("inf")
        return abs(0.6745 * (value - median) / mad)

    def _has_drift(self, history, value):
        if len(history) < 8:
            history.append(value)
            return False
        prior = statistics.median(history)
        history.append(value)
        if prior == 0:
            return value != prior
        return abs(value - prior) / abs(prior) >= self.drift_threshold
