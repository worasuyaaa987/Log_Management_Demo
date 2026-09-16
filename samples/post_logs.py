#!/usr/bin/env python3
import time
import json
import requests
import random
from datetime import datetime, timezone

# Configuration
API_URL = "http://localhost:8000/ingest"

# In a real scenario, this would be a valid JWT or API key for the tenant.
# This matches the INGEST_TOKEN default we set in docker-compose.yml
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer demo_secret_token"
}

def generate_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_sample_logs():
    """Generates a batch of mixed log types mimicking different sources"""
    now = generate_timestamp()
    
    logs = [
        # 1. API Login Failed (from original requirements)
        {
            "tenant": "demoA",
            "source": "api",
            "event_type": "app_login_failed",
            "user": "alice",
            "src_ip": f"203.0.113.{random.randint(1, 254)}",
            "reason": "wrong_password",
            "@timestamp": now
        },
        # 2. CrowdStrike Malware Detected
        {
            "tenant": "demoA",
            "source": "crowdstrike",
            "event_type": "malware_detected",
            "host": f"WIN10-0{random.randint(1, 9)}",
            "process": "powershell.exe",
            "severity": 8,
            "sha256": "abcdef1234567890abcdef1234567890",
            "action": "quarantine",
            "@timestamp": now
        },
        # 3. AWS CloudTrail
        {
            "tenant": "demoB",
            "source": "aws",
            "cloud": {
                "service": "iam",
                "account_id": "123456789012",
                "region": "ap-southeast-1"
            },
            "event_type": "CreateUser",
            "user": "admin",
            "src_ip": f"54.169.2.{random.randint(1, 254)}",
            "@timestamp": now,
            "raw": {"eventName": "CreateUser", "requestParameters": {"userName": "temp-user"}}
        },
        # 4. Microsoft 365 Audit
        {
            "tenant": "demoB",
            "source": "m365",
            "event_type": "UserLoggedIn",
            "user": "bob@demo.local",
            "src_ip": f"198.51.100.{random.randint(1, 254)}",
            "status": "Success",
            "workload": "Exchange",
            "@timestamp": now
        },
        # 5. Microsoft AD / Windows Security (Event ID 4625)
        {
            "tenant": "demoA",
            "source": "ad",
            "event_id": 4625,
            "event_type": "LogonFailed",
            "user": "demo\\eve",
            "host": "DC01",
            "src_ip": f"203.0.113.{random.randint(1, 254)}",
            "logon_type": 3,
            "@timestamp": now
        }
    ]
    return logs

def send_logs(logs):
    """Sends the logs to the ingest endpoint"""
    success_count = 0
    for log in logs:
        try:
            # We use HTTP POST directly to the FastAPI /ingest endpoint
            response = requests.post(API_URL, headers=HEADERS, json=log)
            if response.status_code in [200, 201, 202]:
                success_count += 1
            else:
                print(f"[ERROR] Failed to send log. Status code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Connection failed. Is the FastAPI backend running at {API_URL}?")
            return False
        
        # Small delay between events for realism
        time.sleep(0.05)
    
    return success_count > 0

if __name__ == "__main__":
    print("Starting Demo Log Management Ingestion Simulator...")
    print(f"Targeting API: {API_URL}")
    print("-" * 50)
    
    total_sent = 0
    # Loop 10 times to send 50 logs total
    for i in range(10):
        logs_to_send = generate_sample_logs()
        random.shuffle(logs_to_send)
        if send_logs(logs_to_send):
            total_sent += len(logs_to_send)
            print(f"Batch {i+1}/10 sent successfully.")
            
    print("-" * 50)
    print(f"Simulation complete. {total_sent} logs sent. Check your frontend dashboard!")
