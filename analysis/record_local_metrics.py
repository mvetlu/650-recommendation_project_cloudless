def compute_metrics(rows):
    latencies = [float(r[0]) for r in rows if r[0] is not None]
    total = len(latencies)

    if total == 0:
        return {
            "avg_latency": 0,
            "min_latency": 0,
            "max_latency": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
            "count": 0,
            "error_rate": 0,
            "recovery_time_sec": "N/A",
            "uptime": "0%"
        }

    # correct boolean test
    errors = sum(1 for r in rows if not r[1])

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
        "uptime": f"{100 - round(errors / total * 100, 2)}%"
    }
