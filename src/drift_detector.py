from collections import defaultdict


class DriftDetector:
    """
    Baseline-relative drift detector.

    Strategy:
    - First baseline_size valid records build a fixed baseline.
    - After the baseline, records are grouped into independent windows.
    - A window is evaluated only when it is complete.
    - Drift requires the configured deviation threshold
      for a number of consecutive windows.
    - The latest completed window result is stored so that
      the receiver can report exactly what triggered drift.
    """

    MODEL_CONFIG = {
        "leak_detector": {
            "metric": "confidence_score",
            "direction": "down",
        },
        "demand_forecaster": {
            "metric": "response_time_ms",
            "direction": "up",
        },
    }

    def __init__(
        self,
        baseline_size=60,
        window_size=20,
        threshold=0.15,
        persistence=3,
    ):
        self.baseline_size = baseline_size
        self.window_size = window_size
        self.threshold = threshold
        self.persistence = persistence

        # Keep complete history for analysis and reporting.
        self.history = defaultdict(list)

        # Fixed baseline for each configured model.
        self.baselines = {}

        # Records received after the baseline and not yet
        # included in a completed window.
        self.window_buffers = defaultdict(list)

        # Number of consecutive drift windows.
        self.window_counters = defaultdict(int)

        # Current drift state for each model.
        self.drift_states = defaultdict(bool)

        # Information about the latest completed window.
        self.latest_window_results = {}

    def add_record(self, record):
        model = record["model_name"]

        self.history[model].append(record)

        # Models without a configured drift metric are simply stored.
        if model not in self.MODEL_CONFIG:
            return

        # Build the baseline exactly once.
        if model not in self.baselines:
            if len(self.history[model]) >= self.baseline_size:
                metric = self.MODEL_CONFIG[model]["metric"]

                baseline_records = self.history[model][:self.baseline_size]

                self.baselines[model] = (
                    sum(record[metric] for record in baseline_records)
                    / self.baseline_size
                )

            return

        # Add the record to the current post-baseline window.
        self.window_buffers[model].append(record)

        # Do not evaluate incomplete windows.
        if len(self.window_buffers[model]) < self.window_size:
            return

        # Evaluate exactly one completed window.
        window = self.window_buffers[model][:self.window_size]

        # Remove the completed window.
        self.window_buffers[model] = (
            self.window_buffers[model][self.window_size:]
        )

        metric = self.MODEL_CONFIG[model]["metric"]

        window_average = (
            sum(record[metric] for record in window)
            / len(window)
        )

        baseline = self.baselines[model]
        direction = self.MODEL_CONFIG[model]["direction"]

        if baseline <= 0:
            self.window_counters[model] = 0
            self.drift_states[model] = False

            self.latest_window_results[model] = {
                "baseline": baseline,
                "window_average": window_average,
                "deviation": 0.0,
                "deviation_percent": 0.0,
                "consecutive_windows": 0,
                "is_drift": False,
            }

            return

        if direction == "down":
            deviation = (baseline - window_average) / baseline
        else:
            deviation = (window_average - baseline) / baseline

        if deviation >= self.threshold:
            self.window_counters[model] += 1
        else:
            self.window_counters[model] = 0

        is_drift = (
            self.window_counters[model] >= self.persistence
        )

        self.drift_states[model] = is_drift

        # Store the exact result of the completed window.
        self.latest_window_results[model] = {
            "baseline": baseline,
            "window_average": window_average,
            "deviation": deviation,
            "deviation_percent": deviation * 100,
            "consecutive_windows": self.window_counters[model],
            "is_drift": is_drift,
        }

    def get_model_history(self, model_name):
        return self.history[model_name]

    def get_baseline(self, model_name):
        return self.baselines.get(model_name)

    def get_latest_window_result(self, model_name):
        """
        Return information about the latest completed window.

        Returns None if no complete post-baseline window
        has been evaluated yet.
        """
        return self.latest_window_results.get(model_name)

    def average_confidence(self, model_name):
        records = self.history[model_name]

        if not records:
            return 0

        return (
            sum(record["confidence_score"] for record in records)
            / len(records)
        )

    def average_response_time(self, model_name):
        records = self.history[model_name]

        if not records:
            return 0

        return (
            sum(record["response_time_ms"] for record in records)
            / len(records)
        )

    def detect_drift(self, model_name):
        return self.drift_states[model_name]

    def detect_confidence_drift(self, model_name, threshold=0.15):
        """
        Backward-compatible API.

        Confidence drift is only applicable to leak_detector.
        """

        if model_name != "leak_detector":
            return False

        return self.drift_states[model_name]

    def detect_latency_drift(self, model_name, threshold=2.0):
        """
        Backward-compatible API.

        Latency drift is only applicable to demand_forecaster.
        """

        if model_name != "demand_forecaster":
            return False

        return self.drift_states[model_name]