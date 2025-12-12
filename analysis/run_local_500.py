import requests
import time

URL = "http://127.0.0.1:8001/recommend/1"  

for i in range(500):
    try:
        r = requests.get(URL, timeout=2)
        print(f"{i+1}: {r.status_code}")
    except Exception as e:
        print(f"{i+1}: ERROR {e}")

time.sleep(1)
print("\nDONE — 500 requests sent.")
