
# ============================================================
# OPTIMISED LSTM AUTOENCODER EXPORT TO INFLUXDB
# ORIGINAL SEVEN-METRIC MODEL
#
# One InfluxDB point per LSTM sequence
# Includes overall and individual metric anomaly scores
# ============================================================

import os
import time
import numpy as np
import pandas as pd

from pathlib import Path
from getpass import getpass

from influxdb_client import (
    InfluxDBClient,
    Point,
    WritePrecision
)
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException


# ============================================================
# 1. CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

# Update these to match your InfluxDB installation
INFLUX_URL = "http://192.168.0.4:8086"
INFLUX_ORG = "Capstone Group 25"
INFLUX_BUCKET = "MLCL1"

# Use a newly generated token if the previous one was exposed
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")

if not INFLUX_TOKEN:
    INFLUX_TOKEN = getpass("InfluxDB API token: ")

# Export settings
EXPORT_BATCH_SIZE = 500
TIMEOUT_MS = 120000
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3

# Main measurement
MEASUREMENT = "lstm_anomaly"

# Original LSTM results
RESULTS_DIR = (
    PROJECT_DIR
    / "LSTM_Results"
    / "Anomaly_Results"
)

# Optional original wide-format data.
# Set paths to actual filenames if available.
WIDE_FILES = {
    "Client1": PROJECT_DIR / "Client1_30d_Wide.csv",
    "Client2": PROJECT_DIR / "Client2_30d_Wide.csv",
    "Client3": PROJECT_DIR / "Client3_30d_Wide.csv",
    "Switch": PROJECT_DIR / "Switch_30d_Wide.csv"
}

# Device-specific original model metrics
DEVICE_METRICS = {
    "Client1": [
        "cpu_pct",
        "temperature_c",
        "latency_ms",
        "packet_loss_pct",
        "disk_usage_pct",
        "throughput_bytes_per_sec",
        "packet_error_rate_pct"
    ],
    "Client2": [
        "cpu_pct",
        "temperature_c",
        "latency_ms",
        "packet_loss_pct",
        "disk_usage_pct",
        "throughput_bytes_per_sec",
        "packet_error_rate_pct"
    ],
    "Client3": [
        "cpu_pct",
        "temperature_c",
        "latency_ms",
        "packet_loss_pct",
        "disk_usage_pct",
        "throughput_bytes_per_sec",
        "packet_error_rate_pct"
    ],
    "Switch": [
        "cpu_pct",
        "free_memory",
        "temperature",
        "power_supply_state"
    ]
}


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def numeric_or_none(value):
    """Convert to a finite float, or return None."""

    try:
        result = float(value)
        if np.isfinite(result):
            return result
    except (TypeError, ValueError):
        pass

    return None


def parse_anomaly_flag(value):
    """Convert saved anomaly flags to integers."""

    if isinstance(value, str):
        return int(
            value.strip().lower() in
            {"1", "true", "yes"}
        )

    if pd.isna(value):
        return 0

    return int(bool(value))


def find_results_file(device):
    """Locate previously saved original LSTM results."""

    candidates = [
        RESULTS_DIR / f"{device}_Anomaly_Results.csv",
        RESULTS_DIR / f"{device}_anomaly_results.csv"
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"No anomaly results found for {device}.\n"
        f"Searched: {candidates}"
    )


def find_error_column(columns, metric):
    """Find the saved reconstruction error for a metric."""

    candidates = [
        f"{metric}_error",
        f"{metric}_reconstruction_error",
        f"error_{metric}"
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    return None


def load_original_telemetry(device, metrics):
    """Optionally load the original wide telemetry CSV."""

    path = WIDE_FILES[device]

    if not path.exists():
        print(
            f"  Original wide CSV unavailable: {path.name}"
        )
        print(
            "  Exporting all available LSTM scores only."
        )
        return None

    df = pd.read_csv(path, low_memory=False)

    time_column = next(
        (
            col for col in ["timestamp", "_time", "time"]
            if col in df.columns
        ),
        None
    )

    if time_column is None:
        print(
            "  No valid timestamp column in original CSV."
        )
        return None

    df = df.rename(
        columns={time_column: "timestamp"}
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce"
    )

    available_metrics = [
        metric for metric in metrics
        if metric in df.columns
    ]

    df = df[
        ["timestamp"] + available_metrics
    ].copy()

    for metric in available_metrics:
        df[metric] = pd.to_numeric(
            df[metric],
            errors="coerce"
        )

    df = (
        df.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .drop_duplicates("timestamp", keep="last")
        .reset_index(drop=True)
    )

    # Rename raw columns so they cannot be confused
    # with columns already present in anomaly results.
    df = df.rename(
        columns={
            metric: f"raw_{metric}"
            for metric in available_metrics
        }
    )

    print(
        f"  Loaded original telemetry: {len(df):,} rows"
    )

    return df


# ============================================================
# 3. CONNECT TO INFLUXDB
# ============================================================

print("\n" + "=" * 65)
print("LSTM AUTOENCODER — OPTIMISED INFLUXDB EXPORT")
print("=" * 65)

print("\nServer:", INFLUX_URL)
print("Organisation:", INFLUX_ORG)
print("Bucket:", INFLUX_BUCKET)
print("Batch size:", EXPORT_BATCH_SIZE)
print("Timeout:", TIMEOUT_MS / 1000, "seconds")

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG,
    timeout=TIMEOUT_MS
)

print("\nChecking InfluxDB connection...")

if not client.ping():
    client.close()
    raise ConnectionError(
        "InfluxDB server is not responding."
    )

print("InfluxDB server is responding.")

# Validate the bucket if the token permits lookup.
try:
    bucket = client.buckets_api().find_bucket_by_name(
        INFLUX_BUCKET
    )

    if bucket is None:
        print(
            "Warning: Bucket was not found by lookup. "
            "Check the name and token permissions."
        )
    else:
        print("Destination bucket verified.")

except ApiException as exc:
    print(
        "Bucket lookup unavailable:",
        exc.status
    )
    print(
        "Continuing; write permissions will be "
        "checked when exporting."
    )

write_api = client.write_api(
    write_options=SYNCHRONOUS
)


# ============================================================
# 4. BATCH UPLOAD FUNCTION
# ============================================================

total_written = 0


def upload_batch(points, device):
    """Upload a batch, retrying temporary failures."""

    global total_written

    if not points:
        return

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=points
            )

            total_written += len(points)

            return

        except ApiException as exc:

            # Authentication, bucket, or malformed-data
            # errors should be fixed rather than retried.
            if exc.status in {400, 401, 403, 404, 422}:
                raise

            print(
                f"  {device}: HTTP error on attempt "
                f"{attempt}/{MAX_RETRIES}: {exc.status}"
            )

        except Exception as exc:

            print(
                f"  {device}: Upload attempt "
                f"{attempt}/{MAX_RETRIES} failed:"
            )
            print(" ", type(exc).__name__, str(exc)[:250])

        if attempt < MAX_RETRIES:
            time.sleep(
                RETRY_DELAY_SECONDS * attempt
            )

    raise RuntimeError(
        f"{device}: Batch failed after "
        f"{MAX_RETRIES} attempts."
    )


# ============================================================
# 5. EXPORT EACH DEVICE
# ============================================================

export_summary = []

try:

    for device, metrics in DEVICE_METRICS.items():

        print("\n" + "=" * 65)
        print(f"EXPORTING: {device}")
        print("=" * 65)

        # ----------------------------------------------------
        # 5.1 Load saved anomaly results
        # ----------------------------------------------------

        results_path = find_results_file(device)

        print("Results file:", results_path.name)

        results = pd.read_csv(
            results_path,
            low_memory=False
        )

        required_columns = [
            "timestamp",
            "reconstruction_error",
            "threshold",
            "is_anomaly"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in results.columns
        ]

        if missing_columns:
            raise ValueError(
                f"{device}: Missing columns "
                f"{missing_columns}"
            )

        results["timestamp"] = pd.to_datetime(
            results["timestamp"],
            utc=True,
            errors="coerce"
        )

        results = (
            results.dropna(subset=["timestamp"])
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last"
            )
            .reset_index(drop=True)
        )

        print(
            f"Total sequences: {len(results):,}"
        )

        # ----------------------------------------------------
        # 5.2 Identify per-metric error columns
        # ----------------------------------------------------

        error_columns = {
            metric: find_error_column(
                results.columns,
                metric
            )
            for metric in metrics
        }

        available_count = sum(
            column is not None
            for column in error_columns.values()
        )

        print(
            f"Individual metric errors: "
            f"{available_count}/{len(metrics)}"
        )

        missing_metric_errors = [
            metric
            for metric, column in error_columns.items()
            if column is None
        ]

        if missing_metric_errors:
            print(
                "WARNING — Missing metric errors:",
                missing_metric_errors
            )

        # ----------------------------------------------------
        # 5.3 Optional original metric readings
        # ----------------------------------------------------

        telemetry = load_original_telemetry(
            device,
            metrics
        )

        if telemetry is not None:

            # Match each sequence end timestamp to its
            # most recent preceding telemetry observation.
            tolerance = pd.Timedelta(
                seconds=(
                    20 if device == "Switch" else 30
                )
            )

            results = pd.merge_asof(
                results.sort_values("timestamp"),
                telemetry.sort_values("timestamp"),
                on="timestamp",
                direction="backward",
                tolerance=tolerance
            )

        # ----------------------------------------------------
        # 5.4 Create one InfluxDB point per sequence
        # ----------------------------------------------------

        print("\nUploading sequences...")

        total_sequences = len(results)

        points = []
        uploaded_device = 0
        skipped_device = 0

        for record in results.to_dict(
            orient="records"
        ):

            timestamp = pd.Timestamp(
                record["timestamp"]
            )

            error = numeric_or_none(
                record.get("reconstruction_error")
            )

            threshold = numeric_or_none(
                record.get("threshold")
            )

            if error is None or threshold is None:
                skipped_device += 1
                continue

            anomaly_flag = parse_anomaly_flag(
                record.get("is_anomaly")
            )

            severity_ratio = (
                error / threshold
                if threshold > 0 else 0.0
            )

            # -----------------------------------------------
            # ONE POINT — ALL ANOMALY INFORMATION
            # -----------------------------------------------

            point = (
                Point(MEASUREMENT)
                .tag("device_id", device)
                .tag("model", "original_lstm")
                .field(
                    "reconstruction_error",
                    error
                )
                .field(
                    "threshold",
                    threshold
                )
                .field(
                    "is_anomaly",
                    anomaly_flag
                )
                .field(
                    "severity_ratio",
                    float(severity_ratio)
                )
                .time(
                    timestamp.to_pydatetime(),
                    WritePrecision.NS
                )
            )

            # -----------------------------------------------
            # Most unusual metric
            # -----------------------------------------------

            unusual = record.get(
                "most_unusual_metric"
            )

            if pd.notna(unusual):
                point = point.field(
                    "most_unusual_metric",
                    str(unusual)
                )

            # -----------------------------------------------
            # Add every individual metric error
            # -----------------------------------------------

            for metric in metrics:

                error_column = error_columns[metric]

                if error_column is not None:

                    metric_error = numeric_or_none(
                        record.get(error_column)
                    )

                    if metric_error is not None:

                        point = point.field(
                            f"{metric}_error",
                            metric_error
                        )

                # -------------------------------------------
                # Optional original metric values
                # -------------------------------------------

                raw_column = f"raw_{metric}"

                raw_value = numeric_or_none(
                    record.get(raw_column)
                )

                if raw_value is not None:

                    point = point.field(
                        f"{metric}_value",
                        raw_value
                    )

            # Add complete sequence point
            points.append(point)

            # -----------------------------------------------
            # Upload in batches
            # -----------------------------------------------

            if len(points) >= EXPORT_BATCH_SIZE:

                batch_count = len(points)

                upload_batch(
                    points,
                    device
                )

                uploaded_device += batch_count
                points.clear()

                percent = (
                    uploaded_device
                    / total_sequences
                    * 100
                )

                print(
                    f"  {device}: "
                    f"{uploaded_device:,}/"
                    f"{total_sequences:,} "
                    f"({percent:.1f}%) uploaded"
                )

        # -----------------------------------------------
        # Upload final partial batch
        # -----------------------------------------------

        if points:

            batch_count = len(points)

            upload_batch(
                points,
                device
            )

            uploaded_device += batch_count
            points.clear()

        # -----------------------------------------------
        # Device summary
        # -----------------------------------------------

        print("\nDevice export completed:")
        print("Device:", device)
        print("Uploaded:", f"{uploaded_device:,}")
        print("Skipped:", f"{skipped_device:,}")

        export_summary.append({
            "Device": device,
            "Total_Sequences": total_sequences,
            "Uploaded": uploaded_device,
            "Skipped": skipped_device,
            "Individual_Metric_Errors": available_count
        })

finally:

    write_api.close()
    client.close()


# ============================================================
# 6. FINAL SUMMARY
# ============================================================

summary_df = pd.DataFrame(
    export_summary
)

summary_path = (
    PROJECT_DIR / "LSTM_Grafana_Export_Summary.csv"
)

summary_df.to_csv(
    summary_path,
    index=False
)

print("\n" + "=" * 65)
print("INFLUXDB EXPORT COMPLETE")
print("=" * 65)

print("\nExport summary:")
print(summary_df.to_string(index=False))

print("\nTotal points uploaded:", f"{total_written:,}")
print("Measurement:", MEASUREMENT)
print("Bucket:", INFLUX_BUCKET)
print("Summary saved:", summary_path)

print("\nResults ready for Grafana.")
