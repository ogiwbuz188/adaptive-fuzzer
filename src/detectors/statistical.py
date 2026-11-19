import statistics


class StatisticalDetector:
    def __init__(self, z_threshold=2.5):
        self.z_threshold = z_threshold
        self.baselines = {}

    def collect(self, key, response_lengths, durations, statuses,
                content_types):
        self.baselines[key] = {
            "length_mean": statistics.mean(response_lengths),
            "length_std": statistics.pstdev(response_lengths),
            "latency_mean": statistics.mean(durations),
            "latency_std": statistics.pstdev(durations),
            "statuses": set(statuses),
            "content_types": set(content_types),
        }

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
            return abs(value - mean) / (mean + 1)
        return abs((value - mean) / std)
