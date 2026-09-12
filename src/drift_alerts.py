import csv
import time


ALERT_FILE = "output/alerts_drift_model.csv"

FIELDS = [
    "timestamp",
    "model_name",
    "drift_type",
    "baseline",
    "window_average",
    "deviation_percent",
    "consecutive_windows",
    "message",
]


def save_drift_alert(
    model_name,
    drift_type,
    baseline,
    window_average,
    deviation_percent,
    consecutive_windows,
    message,
):
    with open(
        ALERT_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        if file.tell() == 0:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "model_name": model_name,
                "drift_type": drift_type,
                "baseline": round(baseline, 4),
                "window_average": round(window_average, 4),
                "deviation_percent": round(
                    deviation_percent,
                    2,
                ),
                "consecutive_windows": consecutive_windows,
                "message": message,
            }
        )