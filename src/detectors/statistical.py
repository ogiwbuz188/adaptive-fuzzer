import statistics


class StatisticalDetector:
    def __init__(self, z_threshold=2.5):
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        self.z_threshold = z_threshold
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
            "statuses": set(statuses),
            "content_types": set(content_types),
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

        if length_z > self.z_threshold:
            anomalies.append("RESPONSE_SIZE_OUTLIER")
        if latency_z > self.z_threshold:
            anomalies.append("LATENCY_OUTLIER")
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
