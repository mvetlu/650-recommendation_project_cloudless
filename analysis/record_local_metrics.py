import csv
import psycopg2
import statistics
import os

OUTPUT_CSV = "system_comparison_metrics.csv"

DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": ""   # add if needed
}


def fetch_local_requests():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT latency_ms, success
        FROM local_requests
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def compute_metrics(rows):
    latencies = [float(r[0]) for r in rows]
    total = len(latencies)

    # count errors (boolean or int)
    errors = sum(1 for r in rows if (r[1] == False or r[1] == 0))

    latencies.sort()

    def percentile(p):
        index = min(int(total * p), total - 1)
        return latencies[index]

    return {
        "avg_latency": round(statistics.mean(latencies), 2),
        "min_latency": round(min(latencies), 2),
        "max_latency": round(max(latencies), 2),
        "p50": round(percentile(0.50), 2),
        "p95": round(percentile(0.95), 2),
        "p99": round(percentile(0.99), 2),
        "count": total,
        "error_rate": round(errors / total * 100, 2),
        "recovery_time_sec": "N/A",
        "uptime": "0%"
    }


def write_to_csv(data):
    headers = [
        "test_name",
        "avg_latency_ms",
        "min_latency_ms",
        "max_latency_ms",
        "records",
        "error_rate_percent",
        "recovery_time_sec",
        "uptime_percent"
    ]

    write_header = not os.path.exists(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(headers)
        writer.writerow([
            "local_non_cloud",
            data["avg_latency"],
            data["min_latency"],
            data["max_latency"],
            data["count"],
            data["error_rate"],
            data["recovery_time_sec"],
            data["uptime"]
        ])


if __name__ == "__main__":
    rows = fetch_local_requests()
    metrics = compute_metrics(rows)
    write_to_csv(metrics)
    print("Local non-cloud metrics appended!")
    print(metrics)
