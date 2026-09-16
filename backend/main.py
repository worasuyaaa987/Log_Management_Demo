import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Dict, Any
from datetime import timedelta, datetime, timezone
import json
import redis
import asyncio
from opensearchpy import helpers

from auth import (
    authenticate_user, create_access_token, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, Token, User
)
from models import LogEvent
from database import get_db

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Demo Log Management API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

geo_cache = {}

def get_geo_info(ip: str) -> str:
    if not ip: return "Unknown"
    if ip in geo_cache: return geo_cache[ip]
    if ip.startswith("192.168.") or ip.startswith("10.") or ip == "127.0.0.1":
        return "Internal"
    
    try:
        # Simple enrichment API (ip-api is free for 45 req/min)
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        if res.get("status") == "success":
            country = res.get("country", "Unknown")
            geo_cache[ip] = country
            return country
    except Exception:
        pass
    return "Unknown"

async def redis_worker():
    db = get_db()
    while True:
        try:
            pipe = redis_client.pipeline()
            pipe.lrange("logs_queue", 0, 499)
            pipe.ltrim("logs_queue", 500, -1)
            results = pipe.execute()
            
            logs = results[0]
            if logs:
                actions = []
                for log_json in logs:
                    log_data = json.loads(log_json)
                    index_name = log_data.pop("_index_name", "logs-all-default")
                    
                    # Enrichment step
                    src_ip = log_data.get("src_ip")
                    if src_ip:
                        log_data["country"] = get_geo_info(src_ip)
                        
                    action = {
                        "_index": index_name,
                        "_source": log_data
                    }
                    actions.append(action)
                
                if actions:
                    helpers.bulk(db, actions)
                    print(f"Bulk inserted {len(actions)} logs from Redis queue")
                    
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Redis worker error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_worker())

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
@limiter.limit("100/minute")
async def ingest_log(request: Request, log: LogEvent, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    # 1. Tenant Isolation Check (AuthZ)
    if current_user.tenant != "all" and current_user.tenant != log.tenant:
        raise HTTPException(status_code=403, detail="Not authorized to ingest for this tenant")
    
    # 2. Extract Data
    log_json_str = log.model_dump_json(by_alias=True, exclude_none=True)
    log_dict = json.loads(log_json_str)
    
    # 3. Time-based & Tenant-based Index Routing
    # Format: logs-{tenant}-{YYYY.MM.DD}
    date_str = log.timestamp.strftime("%Y.%m.%d")
    index_name = f"logs-{log.tenant.lower()}-{date_str}"
    log_dict["_index_name"] = index_name
    
    try:
        # Push to Redis Queue instead of direct OpenSearch indexing
        redis_client.lpush("logs_queue", json.dumps(log_dict))
        
        # 4. Trigger Alerting Check in background
        background_tasks.add_task(check_alert_condition, log, db, index_name)
        
        return {"status": "success", "message": "Log queued for ingestion"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue log: {str(e)}")

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
                    "min_doc_count": 0,
                    "time_zone": "+07:00"
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
                dt = datetime.fromtimestamp(bucket['key'] / 1000.0, tz=timezone.utc).astimezone(timezone(timedelta(hours=7)))
                time_str = dt.strftime("%H:00") if timeRange == "24h" else dt.strftime("%Y-%m-%d")
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
