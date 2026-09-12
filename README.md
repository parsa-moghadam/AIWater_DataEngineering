# AIWater Data Engineering

Data Engineering implementation for the AIWater smart water network monitoring challenge.

## 1. Project Overview

This project implements the data engineering layer of a simulated smart water network.

Three AI models continuously generate predictions:

* `leak_detector`
* `pressure_drop_predictor`
* `demand_forecaster`

The AI models themselves are provided by the challenge and are not trained in this project.

The responsibility of this project is to receive the model output stream over TCP, handle TCP message framing, parse and validate JSON records, separate valid and invalid data, store the results, generate real-time reports, detect model behavior drift, and generate an analytical PDF report.

The overall processing pipeline is:

```text
TCP Stream
    ↓
Receive
    ↓
Buffer / Framing
    ↓
JSON Parsing
    ↓
Validation
    ↓
Clean / Bad Storage
    ↓
Real-Time Reporting
    ↓
Drift Detection
    ↓
Drift Alerts
    ↓
Analytical PDF Report
```

---

## 2. Technologies

* Python 3
* TCP sockets
* JSON
* CSV
* ReportLab
* Python standard library
* Threading on the provided stream server

ReportLab is used for generating the analytical PDF report.

---

## 3. Project Structure

```text
AIWater_DataEngineering/
│
├── water_ai_stream_server.py
├── README.md
│
├── src/
│   ├── main.py
│   ├── receiver.py
│   ├── validator.py
│   ├── storage.py
│   ├── reporter.py
│   ├── drift_detector.py
│   └── drift_alerts.py
│
├── tests/
│   ├── test_buffer.py
│   ├── test_json_handling.py
│   ├── test_validator.py
│   └── test_drift_detector.py
│
└── output/
    ├── clean_readings.csv
    ├── bad_readings.csv
    ├── real_time_reports.csv
    ├── alerts_drift_model.csv
    └── report.pdf
```

### Source files

#### `water_ai_stream_server.py`

Provided simulation server.

It generates newline-delimited JSON records and sends them through TCP on:

```text
localhost:9034
```

The server sends approximately one record every `0.025` seconds.

The server also injects a randomized share of corrupted records. The exact corruption probability is selected for each run and printed by the server at startup.

The server contains controlled model-behavior changes that are used to evaluate drift detection.

#### `src/main.py`

Entry point for the receiver application.

#### `src/receiver.py`

Main data ingestion pipeline.

Responsibilities include:

* TCP connection
* byte reception
* buffering
* newline-based record framing
* JSON parsing
* validation
* clean/bad routing
* statistics collection
* real-time reporting
* drift detection
* drift alert generation

#### `src/validator.py`

Validates the structure and values of incoming records.

#### `src/storage.py`

Stores valid and invalid records in CSV files.

#### `src/reporter.py`

Writes 20-second real-time reports to:

```text
output/real_time_reports.csv
```

#### `src/drift_detector.py`

Implements baseline-relative drift detection using fixed baselines, windows, deviation thresholds, and persistence.

#### `src/drift_alerts.py`

Writes detected drift events to:

```text
output/alerts_drift_model.csv
```

---

## 4. Input Data

Each valid record contains:

```text
reading_id
station_id
model_name
predicted_label
confidence_score
response_time_ms
timestamp
```

### `reading_id`

Must be a positive integer.

### `station_id`

Must be one of:

```text
ST-01
ST-02
...
ST-10
```

### `model_name`

Supported models:

```text
leak_detector
pressure_drop_predictor
demand_forecaster
```

### `predicted_label`

For `leak_detector`:

```text
leak
normal
```

For `pressure_drop_predictor`:

```text
drop
stable
```

For `demand_forecaster`:

```text
integer between 1 and 5000
```

### `confidence_score`

Must be numeric and within:

```text
0 <= confidence_score <= 1
```

### `response_time_ms`

Must be a positive numeric value.

### `timestamp`

Must follow the expected timestamp format:

```text
YYYY-MM-DD HH:MM:SS.mmm
```

---

## 5. TCP Buffering and Framing

TCP is a byte stream and does not guarantee that one `recv()` call corresponds to exactly one application record.

The receiver therefore maintains an internal buffer.

Incoming data is appended to the buffer and complete records are extracted using the newline character:

```text
\n
```

Only complete records are processed.

If the final part of a message is incomplete, it remains in the buffer until more data arrives.

This prevents incorrect parsing when:

* one JSON record is split across multiple TCP packets
* multiple JSON records arrive in a single packet
* a record is partially received

---

## 6. JSON Error Handling

Each complete line is parsed as JSON.

Invalid JSON is not allowed to terminate the receiver.

Instead, the receiver:

1. Counts the record as bad.
2. Creates a bad-record entry.
3. Stores the error as:

```text
invalid_json
```

4. Continues processing subsequent records.

This allows malformed records to be isolated without stopping the ingestion pipeline.

---

## 7. Validation and Data Quality

Records that contain valid JSON but violate the data rules are separated from clean records.

Validation errors are stored in:

```text
output/bad_readings.csv
```

The validation error reasons are stored in the:

```text
validation_errors
```

column.

Valid records are stored in:

```text
output/clean_readings.csv
```

Only valid records are used for:

* real-time statistics
* active station counting
* drift detection

This prevents invalid data from influencing analytical results.

---

## 8. Real-Time Reporting

A report is generated every 20 seconds.

The report contains:

* total records
* clean records
* bad records
* average confidence for each model
* average response time for each model
* number of low-confidence predictions
* number of active stations

Low confidence is defined as:

```text
confidence_score < 0.5
```

Reports are appended to:

```text
output/real_time_reports.csv
```

The reporting statistics are reset after each 20-second reporting window.

If the receiver is stopped in the middle of a reporting interval, the incomplete final interval is not written as a complete 20-second report.

---

## 9. Drift Detection

Drift detection is implemented without machine learning.

The implementation uses:

* a fixed baseline
* post-baseline windows
* relative deviation
* persistence across consecutive windows

### Baseline

The first 60 valid records for each configured model are used to establish the baseline.

The baseline is fixed and is not updated when drift occurs.

### Window

After the baseline is established, records are grouped into windows of:

```text
20 records
```

Only complete windows are evaluated.

### Threshold

The configured relative deviation threshold is:

```text
15%
```

### Persistence

A drift condition must remain above the threshold for:

```text
3 consecutive windows
```

before an alert is generated.

This reduces the risk of generating alerts from isolated abnormal observations.

---

## 10. Drift Rules

### `leak_detector`

The monitored metric is:

```text
confidence_score
```

Drift condition:

```text
confidence decreases by at least 15%
relative to the fixed baseline
```

The condition must persist for 3 consecutive windows.

Alert type:

```text
confidence
```

### `demand_forecaster`

The monitored metric is:

```text
response_time_ms
```

Drift condition:

```text
response time increases by at least 15%
relative to the fixed baseline
```

The condition must persist for 3 consecutive windows.

Alert type:

```text
latency
```

### `pressure_drop_predictor`

No drift rule is currently configured for this model.

It is still included in:

* validation
* storage
* real-time reporting

but it does not currently generate drift alerts.

---

## 11. Drift Alerts

Detected drift events are stored in:

```text
output/alerts_drift_model.csv
```

Each alert contains:

* timestamp
* model name
* drift type
* baseline
* triggering window average
* deviation percentage
* number of consecutive drift windows
* message

The alert uses the metrics from the latest completed window that actually triggered the drift state rather than using a cumulative historical average.

This makes the alert directly traceable to the observation that caused the drift state.

---

## 12. Testing

The project contains tests for:

### TCP Buffering

```text
COMPLETE RECORD: PASS
SPLIT RECORD: PASS
MULTIPLE RECORDS: PASS
PARTIAL LAST RECORD: PASS
```

### JSON Handling

```text
VALID JSON: PASS
INVALID JSON: PASS
```

### Validation

The validator test suite checks:

* valid records
* invalid station IDs
* invalid confidence scores
* multiple validation errors
* invalid demand labels
* invalid pressure-model labels
* non-dictionary input
* rejection of boolean numeric values

All current validation tests pass.

### Drift Detection

The drift detector tests cover:

* history
* average confidence
* average response time
* baseline creation
* fixed baseline behavior
* confidence drift persistence
* absence of confidence drift
* latency drift persistence
* absence of latency drift
* absence of a drift rule for the pressure model

All current drift detector tests pass.

### Full Test Result

The complete current test suite contains:

```text
23/23 PASS
```

Tests are executed using Python module execution:

```powershell
python -m tests.test_buffer
python -m tests.test_json_handling
python -m tests.test_validator
python -m tests.test_drift_detector
```

---

## 13. Real Execution

The receiver was executed against the provided TCP stream server for more than six minutes, satisfying the challenge requirement for evaluating the drift cycle.

For the verified execution used in this project, the server reported:

```text
Corruption rate for this run: 2.55%
```

The receiver did not assume a fixed corruption rate.

The execution generated:

```text
output/clean_readings.csv
output/bad_readings.csv
output/real_time_reports.csv
output/alerts_drift_model.csv
```

The generated data includes valid and invalid records, periodic real-time reports, and drift alerts.

---

## 14. Verified Real-Run Results

The verified execution produced:

```text
Clean records: 15,847
Bad records: 314
Real-time reports: 21 complete reports
Drift alerts: 3
Active stations observed: 10
```

The clean data contained records from all three models.

Verified clean-record model counts were:

```text
pressure_drop_predictor: 5305
demand_forecaster:       5277
leak_detector:           5265
```

### Bad-record validation results

The bad records contained the following validation error categories:

```text
invalid confidence_score: 314
invalid response_time_ms: 314
invalid predicted_label: 161
invalid model_name: 115
invalid reading_id: 103
invalid station_id: 72
invalid timestamp: 63
```

The values above are counts of validation-error occurrences. A single bad record may contain more than one error.

### Drift alerts

The verified execution generated:

```text
2026-09-09 22:06:01
leak_detector
confidence
baseline = 0.8580
window_average = 0.6887
deviation = 19.73%
consecutive_windows = 3
```

```text
2026-09-09 22:06:51
demand_forecaster
latency
baseline = 82.5533 ms
window_average = 105.1250 ms
deviation = 27.34%
consecutive_windows = 3
```

```text
2026-09-09 22:11:00
leak_detector
confidence
baseline = 0.8580
window_average = 0.7063
deviation = 17.69%
consecutive_windows = 3
```

These results demonstrate that the detector generated alerts only after the configured persistence requirement was satisfied.

No drift alert was generated for `pressure_drop_predictor` during this execution.

---

## 15. Real-Time Monitoring Results

The system generated 21 complete 20-second reports during the verified execution.

The reports demonstrate three important behaviors.

### Normal operation

During normal periods, the average response time of the demand forecaster remained approximately around 80 ms.

The leak detector confidence also remained around its normal operating range.

### Leak-detector confidence drift

During the confidence-drift phase, the reported average leak-detector confidence decreased significantly.

Examples from the real-time reports include:

```text
22:05:42 → 0.8154
22:06:02 → 0.7352
22:06:22 → 0.6516
22:06:42 → 0.5639
```

This change corresponds to the confidence drift injected by the provided simulation server.

### Demand-forecaster latency drift

During the latency-drift phase, the demand forecaster response time increased:

```text
22:07:02 → 108.89 ms
22:07:22 → 168.03 ms
22:07:42 → 223.80 ms
22:08:02 → 162.18 ms
```

After the drift phase, the response time returned toward the normal range around 80 ms.

This supports the conclusion that the detector was monitoring model behavior rather than simply counting bad records.

---

## 16. Active Stations

The verified real-time reports consistently observed:

```text
active_stations = 10
```

This indicates that all ten simulated stations:

```text
ST-01 through ST-10
```

participated in the clean data during the monitored reporting periods.

---

## 17. Important Reporting Detail

The number of records represented by the 20-second reports may be lower than the total number of records stored in:

```text
clean_readings.csv
bad_readings.csv
```

This is expected because the receiver writes reports for completed 20-second reporting windows.

If the receiver is stopped in the middle of a reporting window, the remaining partial interval is not automatically written as a complete 20-second report.

Therefore:

```text
CSV record totals != necessarily the sum of complete report windows
```

This does not indicate data loss in CSV storage.

The CSV files contain the records processed before shutdown, while the reporting file contains only completed reporting intervals.

---

## 18. Design Assumptions

The following are implementation decisions made for this challenge:

1. The first 60 valid records per configured model are used as the drift baseline.
2. The baseline remains fixed during the run.
3. Drift evaluation uses 20-record windows.
4. A relative deviation of 15% is considered significant.
5. Three consecutive drift windows are required before an alert.
6. Only valid records participate in drift detection.
7. Only complete windows are evaluated.
8. `pressure_drop_predictor` currently has no configured drift rule.
9. Real-time reports are generated every 20 seconds.
10. The provided server is treated as the source of truth for the input stream and its randomized corruption behavior.
11. The current implementation is designed for the challenge-scale stream and is not presented as a production distributed architecture.
12. The analytical PDF is generated from the stored CSV outputs produced by the execution.

These values are engineering assumptions for the implementation and are not claims that the supplied AI models were retrained or modified.

---

# 19. Analytical Questions

## 19.1 Scaling from 50 to 50,000 records/second

The current Python + CSV implementation is appropriate for the challenge-scale stream of approximately 40 records/second.

At 50 records/second, the architecture is relatively lightweight and CSV storage can be sufficient for a small simulation.

At 50,000 records/second, however, synchronous per-record CSV writes would become a major bottleneck.

Potential bottlenecks include:

* synchronous file I/O
* opening and closing files for individual records
* CSV serialization
* single-process processing
* memory pressure from buffering
* contention when multiple streams write to the same storage
* limited horizontal scalability

A production-scale architecture should separate ingestion, processing, and storage.

A possible architecture is:

```text
TCP / Network Sources
        ↓
Load Balancer
        ↓
Durable Message Queue
        ↓
Stream Processing Workers
        ↓
Validation / Enrichment
        ↓
Scalable Storage
        ↓
Analytics / Monitoring
```

The message queue provides buffering between ingestion and downstream processing.

Processing can then be horizontally scaled by adding additional workers.

For storage, a database or distributed analytical storage system would be more appropriate than individual CSV writes.

Additional optimizations could include:

* batch writes
* asynchronous I/O
* connection pooling
* partitioned storage
* compression
* backpressure
* monitoring
* horizontal scaling

Therefore, Python itself is not necessarily the main limitation at 50,000 records/second. The larger concern is the architecture around synchronous processing and local CSV storage.

---

## 19.2 Multiple Simultaneous Streams

If each AI model or source provides an independent TCP stream, the ingestion layer should process the streams concurrently.

The important design principle is:

```text
One stream must not block unrelated streams.
```

Possible approaches include:

### Thread-based approach

Each connection can be assigned to an independent worker thread.

This is relatively simple and can work for a limited number of streams.

### Asynchronous I/O

An asynchronous socket implementation can handle many concurrent network connections efficiently.

### Multiple worker processes

For higher CPU utilization and stronger isolation, multiple worker processes can be used.

### Durable queue

A more scalable design is:

```text
Stream 1 ─┐
Stream 2 ─┼→ Ingestion → Durable Queue → Workers
Stream 3 ─┘
```

This allows downstream processing to scale independently from the number of network connections.

The current challenge server already accepts multiple TCP client connections, but the receiver implementation is intentionally focused on the single-stream challenge workflow.

---

## 19.3 Preventing Data Loss

The current implementation writes processed records directly to CSV files.

For a production system with strong durability requirements, this would not be sufficient by itself.

A more reliable architecture would use a durable queue:

```text
Producer
   ↓
Durable Queue
   ↓
Consumer
   ↓
Processing
   ↓
Durable Storage
```

The queue should persist messages to durable storage.

Acknowledgements can be used so that a message is acknowledged only after the required processing and persistence steps succeed.

For example:

```text
Receive
   ↓
Persist to durable queue
   ↓
Process
   ↓
Write to durable storage
   ↓
ACK
```

If the consumer crashes before the acknowledgement, the message can be replayed.

Checkpointing and replay mechanisms can also help recover from:

* network disconnection
* receiver crash
* worker failure
* storage failure

For critical systems, additional mechanisms such as replication, idempotent writes, and monitoring would be required.

---

## 19.4 Noise vs Drift

Not every unusual observation represents model drift.

Natural variation may occur in:

* water demand
* network pressure
* model response time
* model confidence

A single abnormal value should therefore not automatically trigger a drift alert.

The implemented detector reduces false positives through:

```text
Fixed baseline
      +
Window averaging
      +
Relative deviation
      +
Consecutive-window persistence
```

This approach means that an isolated abnormal observation does not immediately generate an alert.

A persistent change in behavior is more likely to pass all four conditions.

### Why persistence matters

For example, suppose one window temporarily has low confidence.

If the next windows return to normal, the consecutive-window counter is reset.

Therefore, a temporary fluctuation does not automatically become a drift event.

### Production improvements

A production monitoring system could further improve this distinction using:

* model-specific baselines
* station-aware baselines
* time-of-day seasonality
* rolling statistical thresholds
* robust statistics
* adaptive thresholds
* separate data-quality monitoring
* separate model-performance monitoring

The current implementation deliberately uses a simple and explainable statistical approach because the challenge does not require machine-learning-based drift detection.

---

## 20. Conclusion

The implemented system satisfies the main data-engineering requirements of the AIWater challenge.

The pipeline successfully:

```text
Receives TCP data
      ↓
Frames newline-delimited records
      ↓
Parses JSON
      ↓
Validates records
      ↓
Separates clean and bad data
      ↓
Stores results
      ↓
Generates 20-second reports
      ↓
Detects persistent model drift
      ↓
Stores drift alerts
      ↓
Produces analytical output
```

The verified execution demonstrated:

```text
15,847 clean records
314 bad records
21 complete real-time reports
3 drift alerts
10 active stations
```

The real data also demonstrated the expected simulated drift behavior:

* confidence degradation in `leak_detector`
* latency increase in `demand_forecaster`
* stable behavior in `pressure_drop_predictor`

The project therefore demonstrates a complete challenge-scale data engineering pipeline from TCP ingestion through validation, storage, monitoring, drift detection, and analytical reporting.

---

## 21. Running the Project

### Step 1 — Start the stream server

Open a PowerShell terminal in the project directory:

```powershell
python .\water_ai_stream_server.py
```

The server listens on:

```text
localhost:9034
```

Drift injection is enabled by default.

### Step 2 — Start the receiver

Open another PowerShell terminal in the same project directory:

```powershell
python -m src.main
```

The receiver connects to the server and begins processing the stream.

### Step 3 — Allow the system to run

For complete drift-cycle evaluation, allow the system to run for at least six minutes.

The output CSV files are written to:

```text
output/
```

### Step 4 — Stop the receiver

Use:

```text
Ctrl + C
```

when the required execution period has been completed.

---

## 22. Output Files

### `clean_readings.csv`

Contains successfully validated records.

### `bad_readings.csv`

Contains invalid records and their validation errors.

### `real_time_reports.csv`

Contains periodic 20-second monitoring reports.

### `alerts_drift_model.csv`

Contains detected persistent drift events.

### `report.pdf`

Contains the analytical report generated from the execution results.

---

## 23. Submission

The final submission should contain the source code, tests, documentation, and required output artifacts.

Temporary Python cache directories such as:

```text
__pycache__/
```

should not be included in the final ZIP/RAR submission.

The final archive should contain the project in a structure similar to:

```text
AIWater_DataEngineering/
├── water_ai_stream_server.py
├── README.md
├── src/
├── tests/
└── output/
    ├── clean_readings.csv
    ├── bad_readings.csv
    ├── real_time_reports.csv
    ├── alerts_drift_model.csv
    └── report.pdf
```

The final ZIP/RAR should also contain any required project documentation and execution artifacts.

---

## 24. Project Status

Current implementation status:

```text
TCP receiving                  DONE
TCP buffering/framing          DONE
JSON parsing                   DONE
Data validation                DONE
Clean/bad separation           DONE
CSV storage                    DONE
20-second reporting            DONE
Drift detection                DONE
Drift alert storage            DONE
Unit/functional tests          DONE
Real stream execution          DONE
6+ minute execution            DONE
README                          DONE
Analytical PDF                 PENDING
Final archive                   PENDING
```
