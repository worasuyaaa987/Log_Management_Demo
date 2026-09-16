import time
import requests
from datetime import datetime, timezone

API_URL = "http://localhost:8000/ingest"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer demo_secret_token"
}

def send_alert_logs():
    print("🚨 Triggering Brute Force Alert (3 Failed Logins)...")
    
    # We use a static IP to ensure the rule triggers!
    attacker_ip = "192.168.99.99"
    
    for i in range(3):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log = {
            "tenant": "demoA",
            "source": "api",
            "event_type": "app_login_failed",
            "user": "admin",
            "src_ip": attacker_ip,
            "reason": "wrong_password",
            "@timestamp": now
        }
        
        print(f"Sending failed login {i+1}/3 from {attacker_ip}...")
        response = requests.post(API_URL, headers=HEADERS, json=log)
        
        if response.status_code == 201:
            print(f"✅ Success")
        else:
            print(f"❌ Failed: {response.text}")
            
        time.sleep(0.5)

    print("\n✅ Done! Check your Dashboard under 'Recent Alerts' (Refresh the page)")

if __name__ == "__main__":
    send_alert_logs()
