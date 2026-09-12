import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from datetime import timedelta, datetime
import json

from auth import (
    authenticate_user, create_access_token, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, Token, User
)
from models import LogEvent
from database import get_db

app = FastAPI(title="Demo Log Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "tenant": user["tenant"]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def check_alert_condition(log: LogEvent, db, index_name: str):
    """Rule: 3 Failed logins from same IP in 5 minutes"""
    if log.event_type in ["LogonFailed", "app_login_failed"] and log.src_ip:
        five_mins_ago = (log.timestamp - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"src_ip.keyword": log.src_ip}},
                        {"terms": {"event_type.keyword": ["LogonFailed", "app_login_failed"]}},
                        {"range": {"@timestamp": {"gte": five_mins_ago}}}
                    ]
                }
            }
        }
        try:
            res = db.count(index=f"logs-{log.tenant.lower()}-*", body=query, ignore_unavailable=True)
            count = res.get('count', 0)
            if count >= 3:
                # Store alert in dedicated index
                alert_doc = {
                    "@timestamp": log.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "tenant": log.tenant,
                    "rule_name": "Multiple Failed Logins",
                    "severity": "High",
                    "description": f"IP {log.src_ip} failed to login {count} times within 5 minutes.",
                    "src_ip": log.src_ip
                }
                db.index(index="alerts", body=alert_doc, refresh=True)
                print(f"[ALERT] {alert_doc['description']}")
                
                # Send Webhook Notification (e.g. Discord, Slack)
                webhook_url = os.getenv("WEBHOOK_URL")
                if webhook_url:
                    try:
                        payload = {"content": f"\U0001f6a8 **ALERT [High]**: {alert_doc['description']}"}
                        requests.post(webhook_url, json=payload, timeout=5)
                    except Exception as we:
                        print(f"Webhook failed: {we}")
        except Exception as e:
            print(f"Alert check failed: {e}")

@app.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_log(log: LogEvent, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    # 1. Tenant Isolation Check (AuthZ)
    if current_user.tenant != "all" and current_user.tenant != log.tenant:
        raise HTTPException(status_code=403, detail="Not authorized to ingest for this tenant")
    
    # 2. Extract Data
    log_dict = log.model_dump(by_alias=True, exclude_none=True)
    
    # 3. Time-based & Tenant-based Index Routing
    # Format: logs-{tenant}-{YYYY.MM.DD}
    date_str = log.timestamp.strftime("%Y.%m.%d")
    index_name = f"logs-{log.tenant.lower()}-{date_str}"
    
    try:
        response = db.index(
            index=index_name,
            body=log_dict,
            refresh=True # Force refresh for immediate visibility in demo
        )
        
        # 4. Trigger Alerting Check in background
        background_tasks.add_task(check_alert_condition, log, db, index_name)
        
        return {"status": "success", "id": response["_id"], "index": index_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenSearch indexing failed: {str(e)}")

@app.get("/search")
async def search_logs(tenant: str = "all", timeRange: str = "24h", current_user: User = Depends(get_current_user), db=Depends(get_db)):
    # 1. Tenant Isolation Check (AuthZ)
    if current_user.tenant != "all":
        # Force tenant filter to current_user's tenant
        tenant = current_user.tenant
        
    # Construct index pattern
    index_pattern = f"logs-{tenant.lower()}-*" if tenant != "all" else "logs-*"
    
    # Query with aggregations for dashboard
    query = {
        "size": 100,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": []
            }
        },
        "aggs": {
            "top_ips": {
                "terms": { "field": "src_ip.keyword", "size": 5 }
            },
            "top_users": {
                "terms": { "field": "user.keyword", "size": 5 }
            },
            "top_events": {
                "terms": { "field": "event_type.keyword", "size": 5 }
            },
            "timeline": {
                "date_histogram": {
                    "field": "@timestamp",
                    "fixed_interval": "1h" if timeRange == "24h" else "1d",
                    "min_doc_count": 0
                }
            },
            "active_tenants": {
                "cardinality": {"field": "tenant.keyword"}
            }
        }
    }
    
    try:
        res = db.search(index=index_pattern, body=query, ignore_unavailable=True)
        
        # Get Alerts
        alerts = []
        alerts_count = 0
        try:
            alert_query = {
                "size": 10,
                "sort": [{"@timestamp": {"order": "desc"}}],
                "query": {"match_all": {}} if tenant == "all" else {"term": {"tenant.keyword": tenant}}
            }
            alert_res = db.search(index="alerts", body=alert_query, ignore_unavailable=True)
            alerts_count = alert_res['hits']['total']['value'] if isinstance(alert_res['hits']['total'], dict) else alert_res['hits']['total']
            for hit in alert_res['hits']['hits']:
                alerts.append(hit['_source'])
        except Exception:
            pass

        # Format response for the frontend
        total_logs = res['hits']['total']['value'] if isinstance(res['hits']['total'], dict) else res['hits']['total']
        
        # Parse timeline
        timeline = []
        if 'timeline' in res['aggregations']:
            for bucket in res['aggregations']['timeline']['buckets']:
                dt = datetime.fromtimestamp(bucket['key'] / 1000.0)
                time_str = dt.strftime("%H:%00") if timeRange == "24h" else dt.strftime("%Y-%m-%d")
                timeline.append({"time": time_str, "count": bucket['doc_count']})
                
        # Parse top terms
        def parse_top(agg_name):
            result = []
            if agg_name in res['aggregations']:
                for bucket in res['aggregations'][agg_name]['buckets']:
                    if bucket['key'] and bucket['key'] != "-":
                        result.append({"key": bucket['key'], "count": bucket['doc_count']})
            return result
            
        top_ips = parse_top('top_ips')
        top_users = parse_top('top_users')
        top_events = parse_top('top_events')
        
        # Parse recent logs
        logs = []
        for hit in res['hits']['hits']:
            src = hit['_source']
            logs.append({
                "id": hit['_id'],
                "timestamp": src.get('@timestamp'),
                "tenant": src.get('tenant'),
                "source": src.get('source'),
                "event_type": src.get('event_type'),
                "user": src.get('user', '-'),
                "src_ip": src.get('src_ip', '-'),
                "dst_ip": src.get('dst_ip', '-')
            })
            
        return {
            "total": total_logs,
            "active_tenants": res['aggregations'].get('active_tenants', {}).get('value', 0) if tenant == "all" else 1,
            "alerts_count": alerts_count,
            "alert_messages": alerts,
            "timeline": timeline,
            "top_ips": top_ips,
            "top_users": top_users,
            "top_events": top_events,
            "logs": logs
        }
    except Exception as e:
        print(f"Search error: {e}")
        # Return empty data if index doesn't exist yet
        return {
            "total": 0, "active_tenants": 0, "alerts_count": 0, "alert_messages": [],
            "timeline": [], "top_ips": [], "top_users": [], "top_events": [], "logs": []
        }
