import csv
import re

INPUT_FILE = "results/baseline_metrics.md"
OUTPUT_CSV = "system_comparison_metrics.csv"

def parse_markdown_metrics():
    with open(INPUT_FILE, "r") as f:
        lines = f.readlines()

    metrics_rows = []
    
    for line in lines:

        if "|" in line and "Latency" not in line and "Load Level" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 7:  
                metrics_rows.append(parts)

    if not metrics_rows:
        raise ValueError("No valid metric rows found in baseline_metrics.md")

    
    load_level, users, p50, p95, p99, throughput, error_rate = metrics_rows[-1]

    def strip_ms(s):
        return s.replace("ms", "").replace(" ", "").strip()

    return {
        "avg_latency": strip_ms(p50),
        "min_latency": strip_ms(p50),   
        "max_latency": strip_ms(p99),
        "count": users,
        "error_rate": error_rate.replace("%", "").strip(),
        "recovery_time_sec": "N/A (local server has no auto-recovery)",
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

    with open(OUTPUT_CSV, "w", newline="") as f:
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
    metrics = parse_markdown_metrics()
    write_to_csv(metrics)
    print("Local non-cloud metrics successfully written to system_comparison_metrics.csv")
