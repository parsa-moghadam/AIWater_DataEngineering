import csv


CLEAN_FILE = "output/clean_readings.csv"
BAD_FILE = "output/bad_readings.csv"

FIELDS = [
    "reading_id",
    "station_id",
    "model_name",
    "predicted_label",
    "confidence_score",
    "response_time_ms",
    "timestamp",
]


def save_clean(record):
    with open(CLEAN_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if file.tell() == 0:
            writer.writeheader()

        writer.writerow(record)


def save_bad(record, errors):
    row = record.copy()
    row["validation_errors"] = " | ".join(errors)

    fields = FIELDS + ["validation_errors"]

    with open(BAD_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)

        if file.tell() == 0:
            writer.writeheader()

        writer.writerow(row)