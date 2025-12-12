import psycopg2
import os
import csv
import statistics
from psycopg2.extras import RealDictCursor
from datetime import datetime


DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": os.getenv("DB_PASSWORD", "")
}

OUTPUT_CSV = "system_comparison_metrics.csv"
TEST_NAME = "local_non_cloud"


def compute_metrics(rows):
    latencies = [float(r["latency_ms"]) for r in rows if r["latency_ms"] is not None]
    total_requests = len(rows)
    successful_requests = len(latencies)

    if total_requests == 0 or successful_requests == 0:
        return None

    errors = sum(1 for r in rows if not r["success"])
    latencies.sort()

    def percentile(p):
        index = int(p * (successful_requests - 1))
        return latencies[index]

    error_rate = round(errors / total_requests * 100, 2)

    return {
        "avg_latency_ms": round(statistics.mean(latencies), 3),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "records": total_requests,
        "error_rate_percent": error_rate,
        "recovery_time_sec": "N/A (local server has no auto-recovery)",
        "uptime_percent": round(100 - error_rate, 2)
    }


def fetch_local_rows():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("""
        SELECT latency_ms, success
        FROM local_requests
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def append_to_csv(metrics):
    file_exists = os.path.isfile(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "test_name",
                "avg_latency_ms",
                "min_latency_ms",
                "max_latency_ms",
                "records",
                "error_rate_percent",
                "recovery_time_sec",
                "uptime_percent"
            ])

        writer.writerow([
            TEST_NAME,
            metrics["avg_latency_ms"],
            metrics["min_latency_ms"],
            metrics["max_latency_ms"],
            metrics["records"],
            metrics["error_rate_percent"],
            metrics["recovery_time_sec"],
            metrics["uptime_percent"]
        ])

if __name__ == "__main__":
    rows = fetch_local_rows()
    metrics = compute_metrics(rows)

    if metrics:
        append_to_csv(metrics)
        print("Local metrics written to system_comparison_metrics.csv")
        print("Metrics:", metrics)
    else:
        print("No local metrics found. Did you run the load test?")
