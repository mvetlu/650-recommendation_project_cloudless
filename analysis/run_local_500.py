import requests
import time

URL = "http://localhost:8000/recommend/1"

for i in range(500):
    try:
        r = requests.get(URL, timeout=2)
        print(f"{i+1}: {r.status_code}")
    except Exception as e:
        print(f"{i+1}: ERROR {e}")

time.sleep(1)
print("\nDONE — 500 requests sent.")
