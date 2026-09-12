import csv
from collections import Counter
from statistics import mean
from pathlib import Path

OUTPUT = Path("output")


def read_csv(name):
    with open(OUTPUT / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


clean = read_csv("clean_readings.csv")
bad = read_csv("bad_readings.csv")
reports = read_csv("real_time_reports.csv")
alerts = read_csv("alerts_drift_model.csv")


print("=" * 70)
print("AI WATER - REPORT DATA")
print("=" * 70)

# -------------------------------------------------
# 1. GENERAL
# -------------------------------------------------

print("\n[GENERAL]")
print("Clean records:", len(clean))
print("Bad records:", len(bad))
print("Total records:", len(clean) + len(bad))
print("Reports:", len(reports))
print("Drift alerts:", len(alerts))


# -------------------------------------------------
# 2. MODEL COUNTS
# -------------------------------------------------

print("\n[MODEL COUNTS]")

model_counts = Counter(r["model_name"] for r in clean)

for model, count in sorted(model_counts.items()):
    print(model, "=", count)


# -------------------------------------------------
# 3. STATIONS
# -------------------------------------------------

print("\n[STATIONS]")

stations = sorted(set(r["station_id"] for r in clean))

print("Active station count:", len(stations))
print("Stations:", ", ".join(stations))


# -------------------------------------------------
# 4. DATA QUALITY ERRORS
# -------------------------------------------------

print("\n[DATA QUALITY ERRORS]")

errors = Counter()

for row in bad:
    for error in row["validation_errors"].split(" | "):
        errors[error] += 1

for error, count in errors.most_common():
    print(error, "=", count)


# -------------------------------------------------
# 5. REPORT SUMMARY
# -------------------------------------------------

print("\n[REAL-TIME REPORTS]")

if reports:
    total = sum(int(r["total_records"]) for r in reports)
    clean_total = sum(int(r["clean_count"]) for r in reports)
    bad_total = sum(int(r["bad_count"]) for r in reports)

    print("Reported total records:", total)
    print("Reported clean records:", clean_total)
    print("Reported bad records:", bad_total)

    print("\nLast 5 reports:")

    for r in reports[-5:]:
        print(
            r["timestamp"],
            "| total =", r["total_records"],
            "| clean =", r["clean_count"],
            "| bad =", r["bad_count"],
            "| leak_conf =", r["avg_confidence_leak_detector"],
            "| pressure_conf =", r["avg_confidence_pressure_drop_predictor"],
            "| demand_conf =", r["avg_confidence_demand_forecaster"],
            "| leak_latency =", r["avg_response_leak_detector"],
            "| pressure_latency =", r["avg_response_pressure_drop_predictor"],
            "| demand_latency =", r["avg_response_demand_forecaster"],
            "| low_conf =", r["low_confidence_count"],
            "| stations =", r["active_stations"],
        )


# -------------------------------------------------
# 6. OVERALL MODEL STATISTICS
# -------------------------------------------------

print("\n[MODEL STATISTICS]")

for model in sorted(model_counts):

    rows = [r for r in clean if r["model_name"] == model]

    confidences = [
        float(r["confidence_score"])
        for r in rows
    ]

    latencies = [
        float(r["response_time_ms"])
        for r in rows
    ]

    print("\n", model)
    print("  count:", len(rows))
    print("  avg confidence:", round(mean(confidences), 4))
    print("  min confidence:", round(min(confidences), 4))
    print("  max confidence:", round(max(confidences), 4))
    print("  avg response time:", round(mean(latencies), 4))
    print("  min response time:", round(min(latencies), 4))
    print("  max response time:", round(max(latencies), 4))


# -------------------------------------------------
# 7. DRIFT ALERTS
# -------------------------------------------------

print("\n[DRIFT ALERTS]")

for alert in alerts:
    print(
        alert["timestamp"],
        "| model =", alert["model_name"],
        "| type =", alert["drift_type"],
        "| baseline =", alert["baseline"],
        "| window =", alert["window_average"],
        "| deviation =", alert["deviation_percent"] + "%",
        "| consecutive =", alert["consecutive_windows"],
    )


# -------------------------------------------------
# 8. DATA TIME RANGE
# -------------------------------------------------

print("\n[DATA TIME RANGE]")

timestamps = [
    r["timestamp"]
    for r in clean
    if r["timestamp"]
]

if timestamps:
    print("First:", min(timestamps))
    print("Last:", max(timestamps))


# -------------------------------------------------
# 9. CORRUPTION RATE OBSERVED
# -------------------------------------------------

print("\n[OBSERVED CORRUPTION RATE]")

total = len(clean) + len(bad)

if total:
    print(
        "Observed bad percentage:",
        round(len(bad) / total * 100, 2),
        "%"
    )


# -------------------------------------------------
# END
# -------------------------------------------------

print("\n" + "=" * 70)
print("END OF REPORT DATA")
print("=" * 70)
