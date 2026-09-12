from src.validator import validate_record


def make_valid_record():
    return {
        "reading_id": 1,
        "station_id": "ST-01",
        "model_name": "leak_detector",
        "predicted_label": "normal",
        "confidence_score": 0.9,
        "response_time_ms": 40,
        "timestamp": "2026-09-09 05:00:00.000",
    }


def test_valid_record():
    record = make_valid_record()

    assert validate_record(record) == []

    print("VALID RECORD: PASS")


def test_invalid_station_and_confidence():
    record = make_valid_record()

    record["station_id"] = "ST-99"
    record["confidence_score"] = 1.5

    errors = validate_record(record)

    assert "invalid station_id" in errors
    assert "invalid confidence_score" in errors

    print("INVALID STATION + CONFIDENCE: PASS")


def test_multiple_errors():
    record = {
        "reading_id": -10,
        "station_id": "UNKNOWN",
        "model_name": "unknown_model",
        "predicted_label": "wrong",
        "confidence_score": -0.5,
        "response_time_ms": -20,
        "timestamp": "wrong timestamp",
    }

    errors = validate_record(record)

    expected_errors = [
        "invalid reading_id",
        "invalid station_id",
        "invalid model_name",
        "invalid confidence_score",
        "invalid response_time_ms",
        "invalid timestamp",
    ]

    for error in expected_errors:
        assert error in errors

    print("MULTIPLE ERRORS: PASS")


def test_invalid_demand_label():
    record = make_valid_record()

    record["model_name"] = "demand_forecaster"
    record["predicted_label"] = 5001

    errors = validate_record(record)

    assert "invalid predicted_label" in errors

    print("INVALID DEMAND LABEL: PASS")


def test_invalid_pressure_label():
    record = make_valid_record()

    record["model_name"] = "pressure_drop_predictor"
    record["predicted_label"] = "leak"

    errors = validate_record(record)

    assert "invalid predicted_label" in errors

    print("INVALID PRESSURE LABEL: PASS")


def test_non_dict_record():
    errors = validate_record("not a record")

    assert errors == ["invalid record"]

    print("NON-DICT RECORD: PASS")


def test_boolean_numeric_values_are_rejected():
    record = make_valid_record()

    record["reading_id"] = True
    record["confidence_score"] = False
    record["response_time_ms"] = True

    errors = validate_record(record)

    assert "invalid reading_id" in errors
    assert "invalid confidence_score" in errors
    assert "invalid response_time_ms" in errors

    print("BOOLEAN NUMERIC VALUES: PASS")


test_valid_record()
test_invalid_station_and_confidence()
test_multiple_errors()
test_invalid_demand_label()
test_invalid_pressure_label()
test_non_dict_record()
test_boolean_numeric_values_are_rejected()