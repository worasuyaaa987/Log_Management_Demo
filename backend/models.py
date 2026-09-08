from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class LogEvent(BaseModel):
    model_config = ConfigDict(extra='allow') # Allow dynamic fields
    
    timestamp: datetime = Field(alias="@timestamp")
    tenant: str
    source: str
    event_type: str
    vendor: Optional[str] = None
    product: Optional[str] = None
    event_subtype: Optional[str] = None
    severity: Optional[int] = None
    action: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    user: Optional[str] = None
    host: Optional[str] = None
    process: Optional[str] = None
    url: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    rule_name: Optional[str] = None
    rule_id: Optional[str] = None
    raw: Optional[Any] = None
    tags: Optional[List[str]] = Field(default=None, alias="_tags")
