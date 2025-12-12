import statistics

def compute_metrics(rows):
    """
    rows format:
    r[0] -> latency_ms (float or None)
    r[1] -> success (boolean)
    """

    latencies = [float(r[0]) for r in rows if r[0] is not None]
    total_requests = len(rows)
    successful_requests = len(latencies)

    if total_requests == 0 or successful_requests == 0:
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

    errors = sum(1 for r in rows if not r[1])

    latencies.sort()

    def percentile(p):
        # statistically safer percentile index
        index = int(p * (successful_requests - 1))
        return latencies[index]

    error_rate = round(errors / total_requests * 100, 2)

    return {
        "avg_latency": round(statistics.mean(latencies), 2),
        "min_latency": round(min(latencies), 2),
        "max_latency": round(max(latencies), 2),
        "p50": round(percentile(0.50), 2),
        "p95": round(percentile(0.95), 2),
        "p99": round(percentile(0.99), 2),
        "count": successful_requests,
        "error_rate": error_rate,
        "recovery_time_sec": "N/A",
        "uptime": f"{100 - error_rate}%"
    }
