import psutil
import time
import csv
import os
import signal
import sys
from datetime import datetime

# Configuration
SAMPLE_INTERVAL = 5  # seconds between samples
LOG_FILE = "../logs/system_metrics.csv"
POSTGRES_PROCESS_NAME = "postgres"
PYTHON_PROCESS_NAME = "python"

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    global running
    print("\n\nStopping monitoring gracefully...")
    running = False


def find_process_by_name(name):
    pids = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check process name
            if name.lower() in proc.info['name'].lower():
                pids.append(proc.info['pid'])
            # Check command line for Python scripts
            elif proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline']).lower()
                if name.lower() in cmdline:
                    pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return pids


def get_process_stats(pid):
    try:
        proc = psutil.Process(pid)
        return {
            'cpu_percent': proc.cpu_percent(interval=0.1),
            'memory_percent': proc.memory_percent(),
            'memory_mb': proc.memory_info().rss / (1024 * 1024)  # Convert to MB
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def collect_metrics():
    timestamp = datetime.now().isoformat()

    # System-wide metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()

    metrics = {
        'timestamp': timestamp,
        'system_cpu_percent': cpu_percent,
        'system_memory_percent': memory.percent,
        'system_memory_used_gb': memory.used / (1024 ** 3),
        'system_memory_available_gb': memory.available / (1024 ** 3),
        'disk_percent': disk.percent,
        'network_bytes_sent': net_io.bytes_sent,
        'network_bytes_recv': net_io.bytes_recv
    }

    # PostgreSQL process metrics
    postgres_pids = find_process_by_name(POSTGRES_PROCESS_NAME)
    if postgres_pids:
        # Sum metrics across all postgres processes
        total_pg_cpu = 0
        total_pg_mem = 0
        total_pg_mem_mb = 0
        for pid in postgres_pids:
            stats = get_process_stats(pid)
            if stats:
                total_pg_cpu += stats['cpu_percent']
                total_pg_mem += stats['memory_percent']
                total_pg_mem_mb += stats['memory_mb']

        metrics['postgres_cpu_percent'] = round(total_pg_cpu, 2)
        metrics['postgres_memory_percent'] = round(total_pg_mem, 2)
        metrics['postgres_memory_mb'] = round(total_pg_mem_mb, 2)
        metrics['postgres_process_count'] = len(postgres_pids)
    else:
        metrics['postgres_cpu_percent'] = 0
        metrics['postgres_memory_percent'] = 0
        metrics['postgres_memory_mb'] = 0
        metrics['postgres_process_count'] = 0

    # Python API process metrics (look for app.py)
    python_pids = [pid for pid in find_process_by_name("app.py")]
    if python_pids:
        total_py_cpu = 0
        total_py_mem = 0
        total_py_mem_mb = 0
        for pid in python_pids:
            stats = get_process_stats(pid)
            if stats:
                total_py_cpu += stats['cpu_percent']
                total_py_mem += stats['memory_percent']
                total_py_mem_mb += stats['memory_mb']

        metrics['api_cpu_percent'] = round(total_py_cpu, 2)
        metrics['api_memory_percent'] = round(total_py_mem, 2)
        metrics['api_memory_mb'] = round(total_py_mem_mb, 2)
        metrics['api_process_count'] = len(python_pids)
    else:
        metrics['api_cpu_percent'] = 0
        metrics['api_memory_percent'] = 0
        metrics['api_memory_mb'] = 0
        metrics['api_process_count'] = 0

    return metrics


def write_metrics_to_csv(metrics, is_first_write=False):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    mode = 'w' if is_first_write else 'a'
    with open(LOG_FILE, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=metrics.keys())
        if is_first_write:
            writer.writeheader()
        writer.writerow(metrics)


def print_metrics(metrics):
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"SYSTEM RESOURCES:")
    print(f"  CPU Usage:        {metrics['system_cpu_percent']:.1f}%")
    print(
        f"  Memory Usage:     {metrics['system_memory_percent']:.1f}% ({metrics['system_memory_used_gb']:.2f} GB used)")
    print(f"  Disk Usage:       {metrics['disk_percent']:.1f}%")
    print(f"\nPOSTGRESQL:")
    print(f"  Processes:        {metrics['postgres_process_count']}")
    print(f"  CPU Usage:        {metrics['postgres_cpu_percent']:.1f}%")
    print(f"  Memory Usage:     {metrics['postgres_memory_percent']:.1f}% ({metrics['postgres_memory_mb']:.1f} MB)")
    print(f"\nAPI SERVER (app.py):")
    print(f"  Processes:        {metrics['api_process_count']}")
    print(f"  CPU Usage:        {metrics['api_cpu_percent']:.1f}%")
    print(f"  Memory Usage:     {metrics['api_memory_percent']:.1f}% ({metrics['api_memory_mb']:.1f} MB)")


def main():
    global running

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 70)
    print("SYSTEM RESOURCE MONITOR")
    print("=" * 70)
    print(f"Sampling interval: {SAMPLE_INTERVAL} seconds")
    print(f"Log file: {LOG_FILE}")
    print(f"Monitoring: System, PostgreSQL, API (app.py)")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 70)

    # Check if processes are running
    postgres_pids = find_process_by_name(POSTGRES_PROCESS_NAME)
    python_pids = find_process_by_name("app.py")

    print(f"\nInitial process detection:")
    print(f"  PostgreSQL processes found: {len(postgres_pids)}")
    print(f"  API processes found: {len(python_pids)}")

    if not postgres_pids:
        print("\n⚠️  WARNING: No PostgreSQL processes detected!")
    if not python_pids:
        print("\n⚠️  WARNING: No API (app.py) processes detected!")

    print("\nStarting monitoring...\n")

    is_first_write = True
    sample_count = 0

    while running:
        try:
            # Collect metrics
            metrics = collect_metrics()

            # Write to CSV
            write_metrics_to_csv(metrics, is_first_write)
            is_first_write = False

            # Print to console
            print_metrics(metrics)

            sample_count += 1
            print(f"\nSamples collected: {sample_count} | Next sample in {SAMPLE_INTERVAL}s...")

            # Wait for next sample
            time.sleep(SAMPLE_INTERVAL)

        except Exception as e:
            print(f"\n❌ Error collecting metrics: {e}")
            time.sleep(SAMPLE_INTERVAL)

    # Graceful shutdown
    print("\n" + "=" * 70)
    print(f"Monitoring stopped. Collected {sample_count} samples.")
    print(f"Results saved to: {LOG_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()