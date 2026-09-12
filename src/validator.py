from datetime import datetime


def validate_record(record):
    errors = []

    if not isinstance(record, dict):
        return ["invalid record"]

    # reading_id
    # bool is technically an int in Python, so reject it explicitly.
    reading_id = record.get("reading_id")

    if (
        isinstance(reading_id, bool)
        or not isinstance(reading_id, int)
        or reading_id <= 0
    ):
        errors.append("invalid reading_id")

    # station_id
    valid_stations = [f"ST-{i:02d}" for i in range(1, 11)]

    if record.get("station_id") not in valid_stations:
        errors.append("invalid station_id")

    # model_name
    valid_models = [
        "leak_detector",
        "pressure_drop_predictor",
        "demand_forecaster"
    ]

    model = record.get("model_name")

    if model not in valid_models:
        errors.append("invalid model_name")

    # predicted_label
    label = record.get("predicted_label")

    if model == "leak_detector":
        if label not in ["leak", "normal"]:
            errors.append("invalid predicted_label")

    elif model == "pressure_drop_predictor":
        if label not in ["drop", "stable"]:
            errors.append("invalid predicted_label")

    elif model == "demand_forecaster":
        if isinstance(label, bool) or not isinstance(label, int) or not 1 <= label <= 5000:
            errors.append("invalid predicted_label")

    # confidence_score
    confidence = record.get("confidence_score")

    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        errors.append("invalid confidence_score")

    # response_time_ms
    response_time = record.get("response_time_ms")

    if (
        isinstance(response_time, bool)
        or not isinstance(response_time, (int, float))
        or response_time <= 0
    ):
        errors.append("invalid response_time_ms")

    # timestamp
    timestamp = record.get("timestamp")

    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    except (TypeError, ValueError):
        errors.append("invalid timestamp")

    return errors