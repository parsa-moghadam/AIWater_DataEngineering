import json


def test_valid_json():
    line = '{"reading_id": 1, "station_id": "ST-01"}'

    record = json.loads(line)

    assert record["reading_id"] == 1
    assert record["station_id"] == "ST-01"

    print("VALID JSON: PASS")


def test_invalid_json():
    line = '{"reading_id": 1, "station_id": "ST-01"'

    try:
        json.loads(line)
        print("INVALID JSON: FAIL")

    except json.JSONDecodeError:
        print("INVALID JSON: PASS")


test_valid_json()
test_invalid_json()