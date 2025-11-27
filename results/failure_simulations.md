# Failure Simulations

## 1. Test Setup

* **Tool:** Locust (Headless Mode)
* **Load:** 5 Concurrent Users (`--users 5`), spawning 1 user/second (`--spawn-rate 1`).
* **Duration:** 10 minutes (`--run-time 10m`), allowing ample time for stabilization, failure, and recovery.
* **Metrics Output:** Results saved to CSV files (requires `--csv` flag, not shown in commands below).

---

## 2. Simulation 1: Database Outage (PostgreSQL Kill)

This simulation tests the application's behavior when its primary data source (PostgreSQL) is lost, and its ability to automatically reconnect upon database service restoration.

### Procedure

| Terminal | Command | Purpose |
| :--- | :--- | :--- |
| **Terminal 1** | `cd api; python app.py` | Start the FastAPI service (foreground). |
| **Terminal 2** | `locust -f locustfile.py --host=http://localhost:8000 --users 5 --spawn-rate 1 --run-time 10m --headless &` | Start the load test in the background. |
| **Wait 30s** | *(Optional: Run `bg` to ensure the job runs fully).* | Allow load to ramp up and stabilize at 0% errors. |
| **Terminal 3** | `brew services stop postgresql` | **FAILURE INDUCTION:** Simulates a database server crash/outage. |
| **Wait 30-60s** | *(Observe errors in Terminal 1 & 2).* | Measure failure and downtime. |
| **Terminal 3** | `brew services start postgresql` | **RECOVERY:** Restart the database service. |
| **Wait 1m** | *(Observe recovery in Terminal 1 & 2).* | Capture time to re-establish connection and return to 0% errors. |

### Metrics to Capture

| Metric | How to Measure | Source |
| :--- | :--- | :--- |
| **Time to Detect Failure** | Timestamp of the first `5xx` error in the API log OR the first $100\%$ failure report in Locust. | API Log / Locust Console |
| **Downtime Duration** | (Time of First successful `200` after DB restart) - (Time of `brew services stop`) | API Log / Locust CSV |
| **Recovery Time** | Time from `brew services start` until Locust reports $0\%$ failures. | Locust Console / CSV |
| **API Response Code (Failure)** | Typically $\mathbf{503}$ (Service Unavailable) or $\mathbf{500}$ (Internal Server Error). | API Log |

---

## 3. Simulation 2: API Process Crash (Hard Kill)

This simulation tests the resilience of the system when the main application process fails abruptly (e.g., due to memory corruption, unhandled exception, or manual intervention).

### Procedure

| Terminal | Command | Purpose |
| :--- | :--- | :--- |
| **Terminal 1** | `cd api; python app.py` | Start the FastAPI service (foreground). |
| **Terminal 2** | `locust -f locustfile.py --host=http://localhost:8000 --users 5 --spawn-rate 1 --run-time 10m --headless &` | Start the load test in the background. |
| **Wait 30s** | *(Optional: Run `bg` to ensure the job runs fully).* | Allow load to stabilize. |
| **Terminal 3** | `lsof -i :8000` | Find the Process ID (PID) of the FastAPI application. |
| **Terminal 3** | `kill -9 <pid>` | **FAILURE INDUCTION:** Simulate a hard process crash. |
| **Wait 30-60s** | *(Observe errors in Locust: Connection Refused).* | Measure failure and downtime. |
| **Terminal 3** | `cd api; python app.py` | **RECOVERY:** Manually restart the application process. |
| **Wait 1m** | *(Observe recovery in Locust).* | Capture time to re-establish connection and return to 0% errors. |

### Metrics to Capture

| Metric | How to Measure | Source |
| :--- | :--- | :--- |
| **Time to Detect Failure** | Time from `kill -9 <pid>` until the first "Connection Refused" error appears in Locust. | Locust Console / CSV |
| **Downtime Duration** | (Time of Process Restart) - (Time of `kill -9 <pid>`) | Terminal History |
| **Recovery Time** | Time from when the new API instance starts until Locust reports $0\%$ failures. | Locust Console / CSV |
| **API Response Code (Failure)** | Request will fail at the TCP/OS level, resulting in a **Connection Refused** error, not an HTTP status code. | Locust Error Log |