from src.drift_detector import DriftDetector


def make_record(
    model_name,
    confidence_score,
    response_time_ms
):
    return {
        "reading_id": 1,
        "station_id": "ST-01",
        "model_name": model_name,
        "predicted_label": "normal",
        "confidence_score": confidence_score,
        "response_time_ms": response_time_ms,
        "timestamp": "2026-09-09 17:00:00.000",
    }


def test_history():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4,
        persistence=3
    )

    for _ in range(6):
        detector.add_record(
            make_record(
                "leak_detector",
                0.9,
                40
            )
        )

    history = detector.get_model_history(
        "leak_detector"
    )

    assert len(history) == 6

    print("HISTORY: PASS")


def test_average_confidence():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4
    )

    values = [0.8, 0.9, 0.7, 0.8]

    for value in values:
        detector.add_record(
            make_record(
                "leak_detector",
                value,
                40
            )
        )

    average = detector.average_confidence(
        "leak_detector"
    )

    assert abs(average - 0.8) < 0.0001

    print("AVERAGE CONFIDENCE: PASS")


def test_average_response_time():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4
    )

    values = [40, 50, 60, 50]

    for value in values:
        detector.add_record(
            make_record(
                "pressure_drop_predictor",
                0.8,
                value
            )
        )

    average = detector.average_response_time(
        "pressure_drop_predictor"
    )

    assert abs(average - 50) < 0.0001

    print("AVERAGE RESPONSE TIME: PASS")


def test_baseline():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4
    )

    values = [
        0.8,
        0.9,
        0.7,
        0.8
    ]

    for value in values:
        detector.add_record(
            make_record(
                "leak_detector",
                value,
                40
            )
        )

    baseline = detector.get_baseline(
        "leak_detector"
    )

    assert abs(baseline - 0.8) < 0.0001

    print("BASELINE: PASS")


def test_baseline_is_fixed():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4
    )

    baseline_values = [
        0.8,
        0.9,
        0.7,
        0.8
    ]

    for value in baseline_values:
        detector.add_record(
            make_record(
                "leak_detector",
                value,
                40
            )
        )

    for _ in range(4):
        detector.add_record(
            make_record(
                "leak_detector",
                0.2,
                40
            )
        )

    baseline = detector.get_baseline(
        "leak_detector"
    )

    assert abs(baseline - 0.8) < 0.0001

    print("FIXED BASELINE: PASS")


def test_confidence_drift_requires_persistence():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4,
        threshold=0.15,
        persistence=3
    )

    # Baseline = 0.8
    for value in [
        0.8,
        0.9,
        0.7,
        0.8
    ]:
        detector.add_record(
            make_record(
                "leak_detector",
                value,
                40
            )
        )

    # Window 1: drift
    for _ in range(4):
        detector.add_record(
            make_record(
                "leak_detector",
                0.6,
                40
            )
        )

    assert not detector.detect_confidence_drift(
        "leak_detector"
    )

    # Window 2: drift
    for _ in range(4):
        detector.add_record(
            make_record(
                "leak_detector",
                0.6,
                40
            )
        )

    assert not detector.detect_confidence_drift(
        "leak_detector"
    )

    # Window 3: drift
    for _ in range(4):
        detector.add_record(
            make_record(
                "leak_detector",
                0.6,
                40
            )
        )

    assert detector.detect_confidence_drift(
        "leak_detector"
    )

    print("CONFIDENCE DRIFT + PERSISTENCE: PASS")


def test_no_confidence_drift():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4,
        threshold=0.15,
        persistence=3
    )

    for value in [
        0.8,
        0.9,
        0.7,
        0.8
    ]:
        detector.add_record(
            make_record(
                "leak_detector",
                value,
                40
            )
        )

    for _ in range(12):
        detector.add_record(
            make_record(
                "leak_detector",
                0.75,
                40
            )
        )

    assert not detector.detect_confidence_drift(
        "leak_detector"
    )

    print("NO CONFIDENCE DRIFT: PASS")


def test_latency_drift_requires_persistence():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4,
        threshold=0.15,
        persistence=3
    )

    # Baseline = 50
    for _ in range(4):
        detector.add_record(
            make_record(
                "demand_forecaster",
                0.8,
                50
            )
        )

    # Window 1: 100 ms
    for _ in range(4):
        detector.add_record(
            make_record(
                "demand_forecaster",
                0.8,
                100
            )
        )

    assert not detector.detect_latency_drift(
        "demand_forecaster"
    )

    # Window 2: 100 ms
    for _ in range(4):
        detector.add_record(
            make_record(
                "demand_forecaster",
                0.8,
                100
            )
        )

    assert not detector.detect_latency_drift(
        "demand_forecaster"
    )

    # Window 3: 100 ms
    for _ in range(4):
        detector.add_record(
            make_record(
                "demand_forecaster",
                0.8,
                100
            )
        )

    assert detector.detect_latency_drift(
        "demand_forecaster"
    )

    print("LATENCY DRIFT + PERSISTENCE: PASS")


def test_no_latency_drift():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4,
        threshold=0.15,
        persistence=3
    )

    for _ in range(4):
        detector.add_record(
            make_record(
                "demand_forecaster",
                0.8,
                50
            )
        )

        for _ in range(12):
            detector.add_record(
             make_record(
            "demand_forecaster",
            0.8,
            55
        )
    )
    assert not detector.detect_latency_drift(
        "demand_forecaster"
    )

    print("NO LATENCY DRIFT: PASS")


def test_pressure_model_has_no_drift_rule():
    detector = DriftDetector(
        baseline_size=4,
        window_size=4
    )

    for _ in range(20):
        detector.add_record(
            make_record(
                "pressure_drop_predictor",
                0.2,
                200
            )
        )

    assert not detector.detect_drift(
        "pressure_drop_predictor"
    )

    assert not detector.detect_confidence_drift(
        "pressure_drop_predictor"
    )

    assert not detector.detect_latency_drift(
        "pressure_drop_predictor"
    )

    print("PRESSURE MODEL NO DRIFT RULE: PASS")


test_history()
test_average_confidence()
test_average_response_time()
test_baseline()
test_baseline_is_fixed()
test_confidence_drift_requires_persistence()
test_no_confidence_drift()
test_latency_drift_requires_persistence()
test_no_latency_drift()
test_pressure_model_has_no_drift_rule()