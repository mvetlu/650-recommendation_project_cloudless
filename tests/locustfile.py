from locust import HttpUser, task, between, events
import random
import csv
import os
import time

# Load valid user IDs from CSV
USER_IDS = []
# CSV_PATH = "../data/processed/users_top10k.csv"
CSV_PATH = "../data/processed/users_sample10.csv"


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global USER_IDS

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: User CSV not found at {CSV_PATH}")
        print(f"Current directory: {os.getcwd()}")
        return

    with open(CSV_PATH, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        USER_IDS = [row[0] for row in reader]

    print(f"Loaded {len(USER_IDS)} user IDs for testing")


class RecommendationUser(HttpUser):
    # Wait 1-3 seconds between requests (simulates real user behavior)
    wait_time = between(1, 3)

    @task(10)  # Weight: 10 (most common operation)
    def get_recommendations(self):
        if not USER_IDS:
            return

        user_id = random.choice(USER_IDS)

        with self.client.get(
                f"/recommend/{user_id}",
                catch_response=True,
                name="/recommend/[user_id]"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "recommendations" in data and data["count"] > 0:
                        response.success()
                    else:
                        response.failure("Empty recommendations")
                except Exception as e:
                    response.failure(f"Invalid JSON: {e}")
            elif response.status_code == 404:
                response.failure("User not found")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)  # Weight: 1 (less common)
    def health_check(self):
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("Service unhealthy")
                except:
                    response.failure("Invalid health check response")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)  # Weight: 1 (less common)
    def get_stats(self):
        """Get system statistics"""
        self.client.get("/stats", name="/stats")

    def on_start(self):
        # Optional: Could simulate login or session initialization here
        pass


class BurstTrafficUser(HttpUser):
    wait_time = between(0, 0.1)  # Minimal wait (aggressive)

    @task
    def rapid_fire_recommendations(self):
        if not USER_IDS:
            return

        user_id = random.choice(USER_IDS)
        self.client.get(
            f"/recommend/{user_id}",
            name="/recommend/[user_id]"
        )


request_times = []
error_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    global request_times, error_count

    if exception:
        error_count += 1
    else:
        request_times.append(response_time)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    if not request_times:
        print("\nNo successful requests recorded")
        return

    request_times.sort()
    total_requests = len(request_times)

    p50_index = int(total_requests * 0.50)
    p95_index = int(total_requests * 0.95)
    p99_index = int(total_requests * 0.99)

    print("LOAD TEST SUMMARY")
    print(f"Total successful requests: {total_requests}")
    print(f"Total errors: {error_count}")
    print(f"Error rate: {(error_count / (total_requests + error_count) * 100):.2f}%")
    print(f"\nLatency Percentiles:")
    print(f"  P50 (median): {request_times[p50_index]:.2f} ms")
    print(f"  P95:          {request_times[p95_index]:.2f} ms")
    print(f"  P99:          {request_times[p99_index]:.2f} ms")
    print(f"  Min:          {min(request_times):.2f} ms")
    print(f"  Max:          {max(request_times):.2f} ms")
    print(f"  Average:      {sum(request_times) / len(request_times):.2f} ms")