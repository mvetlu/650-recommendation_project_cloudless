import csv
import psycopg2
import statistics

OUTPUT_CSV = "system_comparison_metrics.csv"

DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": ""  # or your password
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
    errors = sum(1 for r in rows if r[1] is False)

    latencies.sort()
    total = len(latencies)

    def percentile(p):
        index = int(total * p)
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

    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
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
    print("Local non-cloud metrics appended to system_comparison_metrics.csv")
    print(metrics)
