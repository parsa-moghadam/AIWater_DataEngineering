import socket
import json
import time
from collections import defaultdict

from .validator import validate_record
from .storage import save_clean, save_bad
from .reporter import save_report
from .drift_detector import DriftDetector
from .drift_alerts import save_drift_alert


HOST = "localhost"
PORT = 9034


def run_receiver():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    print("Receiver JSON error handling is ready.")
    print("Connected to server!")

    buffer = ""

    # -------------------------------------------------------------
    # Report statistics
    # -------------------------------------------------------------

    report_start_time = time.time()

    total_records = 0
    clean_count = 0
    bad_count = 0
    low_confidence_count = 0

    confidence_by_model = defaultdict(list)
    response_by_model = defaultdict(list)

    # Stations seen in the current 20-second reporting window
    active_stations = set()

    # -------------------------------------------------------------
    # Drift detector
    # -------------------------------------------------------------

    drift_detector = DriftDetector(
        baseline_size=60,
        window_size=20,
        threshold=0.15,
        persistence=3,
    )

    # Prevent repeated alerts while the same drift remains active
    drift_alert_state = {}

    # -------------------------------------------------------------
    # Main receive loop
    # -------------------------------------------------------------

    while True:
        data = client.recv(4096)

        if not data:
            break

        buffer += data.decode("utf-8")

        # TCP does not preserve record boundaries.
        # Process only complete newline-delimited records.
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)

            if not line.strip():
                continue

            # -----------------------------------------------------
            # JSON parsing
            # -----------------------------------------------------

            try:
                record = json.loads(line)

            except json.JSONDecodeError:
                total_records += 1
                bad_count += 1

                bad_record = {
                    "reading_id": "",
                    "station_id": "",
                    "model_name": "",
                    "predicted_label": "",
                    "confidence_score": "",
                    "response_time_ms": "",
                    "timestamp": "",
                }

                save_bad(
                    bad_record,
                    ["invalid_json"]
                )

                print("BAD: invalid JSON")

            else:
                total_records += 1

                # -------------------------------------------------
                # Validation
                # -------------------------------------------------

                errors = validate_record(record)

                if errors:
                    bad_count += 1

                    save_bad(
                        record,
                        errors
                    )

                    print("BAD:", errors)

                else:
                    clean_count += 1

                    # Only valid records enter statistics
                    # and drift detection.
                    active_stations.add(
                        record["station_id"]
                    )

                    model_name = record["model_name"]

                    # -------------------------------------------------
                    # Drift detection
                    # -------------------------------------------------

                    drift_detector.add_record(record)

                    # -------------------------------------------------
                    # leak_detector
                    # Confidence decrease
                    # -------------------------------------------------

                    if model_name == "leak_detector":

                        confidence_drift = (
                            drift_detector.detect_confidence_drift(
                                "leak_detector"
                            )
                        )

                        confidence_key = (
                            "leak_detector",
                            "confidence"
                        )

                        if confidence_drift:

                            if not drift_alert_state.get(
                                confidence_key,
                                False
                            ):

                                window_result = (
                                    drift_detector.get_latest_window_result(
                                        "leak_detector"
                                    )
                                )

                                if window_result is not None:

                                    save_drift_alert(
                                        model_name="leak_detector",
                                        drift_type="confidence",
                                        baseline=window_result["baseline"],
                                        window_average=window_result["window_average"],
                                        deviation_percent=window_result["deviation_percent"],
                                        consecutive_windows=window_result["consecutive_windows"],
                                        message="Confidence drift detected",
                                    )

                                    print(
                                        "DRIFT ALERT:",
                                        "leak_detector",
                                        window_result,
                                    )

                                    drift_alert_state[
                                        confidence_key
                                    ] = True

                        else:
                            drift_alert_state[
                                confidence_key
                            ] = False

                    # -------------------------------------------------
                    # demand_forecaster
                    # Latency increase
                    # -------------------------------------------------

                    elif model_name == "demand_forecaster":

                        latency_drift = (
                            drift_detector.detect_latency_drift(
                                "demand_forecaster"
                            )
                        )

                        latency_key = (
                            "demand_forecaster",
                            "latency"
                        )

                        if latency_drift:

                            if not drift_alert_state.get(
                                latency_key,
                                False
                            ):

                                window_result = (
                                    drift_detector.get_latest_window_result(
                                        "demand_forecaster"
                                    )
                                )

                                if window_result is not None:

                                    save_drift_alert(
                                        model_name="demand_forecaster",
                                        drift_type="latency",
                                        baseline=window_result["baseline"],
                                        window_average=window_result["window_average"],
                                        deviation_percent=window_result["deviation_percent"],
                                        consecutive_windows=window_result["consecutive_windows"],
                                        message="Latency drift detected",
                                    )

                                    print(
                                        "DRIFT ALERT:",
                                        "demand_forecaster",
                                        window_result,
                                    )

                                    drift_alert_state[
                                        latency_key
                                    ] = True

                        else:
                            drift_alert_state[
                                latency_key
                            ] = False

                    # -------------------------------------------------
                    # Statistics
                    # -------------------------------------------------

                    confidence_by_model[
                        model_name
                    ].append(
                        record["confidence_score"]
                    )

                    response_by_model[
                        model_name
                    ].append(
                        record["response_time_ms"]
                    )

                    if record["confidence_score"] < 0.5:
                        low_confidence_count += 1

                    save_clean(record)

                    print("CLEAN:", record)

            # ---------------------------------------------------------
            # Generate report every 20 seconds
            # ---------------------------------------------------------

            if time.time() - report_start_time >= 20:

                report = {
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                    "total_records": total_records,

                    "clean_count": clean_count,

                    "bad_count": bad_count,

                    "avg_confidence_leak_detector": (
                        sum(
                            confidence_by_model[
                                "leak_detector"
                            ]
                        )
                        / len(
                            confidence_by_model[
                                "leak_detector"
                            ]
                        )
                        if confidence_by_model[
                            "leak_detector"
                        ]
                        else 0
                    ),

                    "avg_confidence_pressure_drop_predictor": (
                        sum(
                            confidence_by_model[
                                "pressure_drop_predictor"
                            ]
                        )
                        / len(
                            confidence_by_model[
                                "pressure_drop_predictor"
                            ]
                        )
                        if confidence_by_model[
                            "pressure_drop_predictor"
                        ]
                        else 0
                    ),

                    "avg_confidence_demand_forecaster": (
                        sum(
                            confidence_by_model[
                                "demand_forecaster"
                            ]
                        )
                        / len(
                            confidence_by_model[
                                "demand_forecaster"
                            ]
                        )
                        if confidence_by_model[
                            "demand_forecaster"
                        ]
                        else 0
                    ),

                    "avg_response_leak_detector": (
                        sum(
                            response_by_model[
                                "leak_detector"
                            ]
                        )
                        / len(
                            response_by_model[
                                "leak_detector"
                            ]
                        )
                        if response_by_model[
                            "leak_detector"
                        ]
                        else 0
                    ),

                    "avg_response_pressure_drop_predictor": (
                        sum(
                            response_by_model[
                                "pressure_drop_predictor"
                            ]
                        )
                        / len(
                            response_by_model[
                                "pressure_drop_predictor"
                            ]
                        )
                        if response_by_model[
                            "pressure_drop_predictor"
                        ]
                        else 0
                    ),

                    "avg_response_demand_forecaster": (
                        sum(
                            response_by_model[
                                "demand_forecaster"
                            ]
                        )
                        / len(
                            response_by_model[
                                "demand_forecaster"
                            ]
                        )
                        if response_by_model[
                            "demand_forecaster"
                        ]
                        else 0
                    ),

                    "low_confidence_count": (
                        low_confidence_count
                    ),

                    "active_stations": len(
                        active_stations
                    ),
                }

                save_report(report)

                print(
                    "REPORT:",
                    report
                )

                # Reset the 20-second reporting window
                report_start_time = time.time()

                total_records = 0
                clean_count = 0
                bad_count = 0
                low_confidence_count = 0

                confidence_by_model.clear()
                response_by_model.clear()
                active_stations.clear()