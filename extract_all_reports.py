import csv
from pathlib import Path


REPORT_FILE = Path("output/real_time_reports.csv")


with open(REPORT_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    reports = list(reader)


print("=" * 80)
print("AI WATER - ALL REAL-TIME REPORTS")
print("=" * 80)

print("Total reports:", len(reports))
print()

for i, r in enumerate(reports, start=1):

    print(
        f"{i},"
        f"{r['timestamp']},"
        f"{r['total_records']},"
        f"{r['clean_count']},"
        f"{r['bad_count']},"
        f"{r['avg_confidence_leak_detector']},"
        f"{r['avg_confidence_pressure_drop_predictor']},"
        f"{r['avg_confidence_demand_forecaster']},"
        f"{r['avg_response_leak_detector']},"
        f"{r['avg_response_pressure_drop_predictor']},"
        f"{r['avg_response_demand_forecaster']},"
        f"{r['low_confidence_count']},"
        f"{r['active_stations']}"
    )

print()
print("=" * 80)
print("END OF ALL REPORTS")
print("=" * 80)