import csv

REPORT_FILE = "output/real_time_reports.csv"

FIELDS = [
    "timestamp",
    "total_records",
    "clean_count",
    "bad_count",
    "avg_confidence_leak_detector",
    "avg_confidence_pressure_drop_predictor",
    "avg_confidence_demand_forecaster",
    "avg_response_leak_detector",
    "avg_response_pressure_drop_predictor",
    "avg_response_demand_forecaster",
    "low_confidence_count",
    "active_stations",
]


def save_report(report):
    with open(REPORT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if file.tell() == 0:
            writer.writeheader()

        writer.writerow(report) 