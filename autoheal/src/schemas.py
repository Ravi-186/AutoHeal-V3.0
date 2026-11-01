from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DeviceSchema(BaseModel):
    id: str
    role: str
    ip: str
    state: str = Field(..., description="Normal, Isolated, Blocked, or Quarantined")
    zone: str = "Corporate LAN"
    risk_score: int = 0

class IncidentLogSchema(BaseModel):
    time: str
    ip: str
    device: str
    type: str = "AI Threat"
    status: str
    action: str
    verified: bool
    mitre: str

class NetworkStateResponse(BaseModel):
    devices: List[DeviceSchema]
    active_threats: int
    total_devices: str
    total_incidents: int
    logs: List[IncidentLogSchema]

class AttackResponse(BaseModel):
    status: str
    message: str
    target_device: Optional[str] = None
    mitre_tactic: Optional[str] = None

class DetectionResponse(BaseModel):
    threat_found: bool
    incidents: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str = "HEALTHY"
    timestamp: str
    version: str = "2.4.0-enterprise"
    model_loaded: bool
    devices_monitored: int
    active_threats: int
    environment: str = "production"

class DeviceActionResponse(BaseModel):
    status: str
    device_id: str
    previous_state: str
    current_state: str
    message: str
