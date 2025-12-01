import csv
import time
import requests
import statistics

OUTPUT_CSV = "system_comparison_metrics.csv"

API_URL = "http://3.129.17.219/recommend/1"
 


def measure_cloud_metrics(n_requests=500):
    latencies = []
    errors = 0

    print(f"Running {n_requests} requests against: {API_URL}")

    for i in range(n_requests):
        start = time.time()

        try:
            response = requests.get(API_URL, timeout=3)
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                latencies.append(duration_ms)
            else:
                errors += 1

        except Exception:
            errors += 1

    if not latencies:
        return None

    latencies.sort()

    def percentile(p):
        index = int(len(latencies) * p) - 1
        return latencies[max(index, 0)]

    return {
        "avg_latency": round(statistics.mean(latencies), 2),
        "min_latency": round(min(latencies), 2),
        "max_latency": round(max(latencies), 2),
        "p95": round(percentile(0.95), 2),
        "p99": round(percentile(0.99), 2),
        "count": len(latencies),
        "error_rate": round(errors / (n_requests) * 100, 2),
        "recovery_time_sec": "Auto (AWS handles restarts)",
        "uptime": f"{100 - round(errors / n_requests * 100, 2)}%"
    }


def append_to_csv(metrics):
    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cloud_ec2",
            metrics["avg_latency"],
            metrics["min_latency"],
            metrics["max_latency"],
            metrics["count"],
            metrics["error_rate"],
            metrics["recovery_time_sec"],
            metrics["uptime"]
        ])


if __name__ == "__main__":
    m = measure_cloud_metrics()
    if m:
        append_to_csv(m)
        print("Cloud EC2 metrics appended to system_comparison_metrics.csv")
        print("Metrics:", m)
    else:
        print("No successful cloud requests! Check API URL.")
