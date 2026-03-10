import requests
import datetime
import json
import time

# --- Configuration ---
ENDPOINT = "http://localhost:8083/log"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_secret_token"
}

def send_test_log(level="INFO", message="Test log message"):
    payload = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": message,
        "metadata": {
            "source": "python-tester",
            "type": "api_test"
        }
    }

    try:
        response = requests.post(ENDPOINT, headers=HEADERS, json=payload)
        response.raise_for_status() # เช็คว่า Error 4xx/5xx หรือไม่
        print(f"[{response.status_code}] Sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # ทดสอบยิง 5 ครั้ง ทุกๆ 1 วินาที
    levels = ["INFO", "WARNING", "ERROR"]
    for i in range(5):
        msg = f"Automatic test log sequence #{i+1}"
        send_test_log(level=levels[i % 3], message=msg)
        time.sleep(1)