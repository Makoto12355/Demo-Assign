import requests
import random
import time
from datetime import datetime

URL = "http://localhost:8083/log"

def generate_firewall_log():
    actions = ["ACCEPT", "DROP", "REJECT"]
    protocols = ["TCP", "UDP", "ICMP"]
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "device_id": "FW-CORE-01",
        "facility": "authpriv",
        "level": random.choice(["info", "warning", "critical"]),
        "src_addr": f"172.16.0.{random.randint(1, 254)}",
        "dst_addr": f"8.8.8.{random.randint(1, 8)}",
        "proto": random.choice(protocols),
        "action": random.choice(actions),
        "bytes_sent": random.randint(100, 5000),
        "msg": "Inbound connection attempt"
    }

if __name__ == "__main__":
    print("Starting Firewall Syslog Generator...")
    try:
        while True:
            log_data = generate_firewall_log()
            res = requests.post(URL, json=log_data)
            print(f"[{res.status_code}] Sent log: {log_data['src_addr']} -> {log_data['action']}")
            
            # ปรับความเร็วตรงนี้ (เช่น 0.5 คือส่งทุกครึ่งวินาที)
            time.sleep(0.5) 
    except KeyboardInterrupt:
        print("\nStopped by user.")