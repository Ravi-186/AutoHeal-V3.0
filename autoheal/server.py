import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.config import (
    DATA_DIR, WEB_DIR, API_HOST, API_PORT, ALLOWED_ORIGINS, LOG_LEVEL
)
from src.schemas import (
    DeviceSchema, NetworkStateResponse, AttackResponse, DetectionResponse,
    HealthResponse, DeviceActionResponse
)
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner
from src.agents.detection_agent import DetectionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.verification_agent import VerificationAgent
from src.graph.workflow import AutoHealGraph

# Setup Structured Logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger_app = logging.getLogger("AutoHealAPI")

# Initialize FastAPI App
app = FastAPI(
    title="AutoHeal Autonomous Cybersecurity Platform API",
    version="3.0.0",
    description="Enterprise Autonomous Threat Detection, Mitigation & Verification API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates Mounts
css_dir = os.path.join(WEB_DIR, "static", "css")
js_dir = os.path.join(WEB_DIR, "static", "js")
img_dir = os.path.join(WEB_DIR, "static", "img")
templates_dir = os.path.join(WEB_DIR, "templates")

if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")
if os.path.exists(img_dir):
    app.mount("/static/img", StaticFiles(directory=img_dir), name="img")

templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None

# State Initialization
data_dir_str = str(DATA_DIR)
network = NetworkSimulator()
logger_gen = LogGenerator(data_dir_str)
runner = ScenarioRunner(network, logger_gen)
detect_agent = DetectionAgent(data_dir_str)
response_agent = ResponseAgent(network)
verify_agent = VerificationAgent(data_dir_str, network)
graph_manager = AutoHealGraph(detect_agent, response_agent, verify_agent, max_retries=2)

current_time = datetime.now() - timedelta(minutes=5)
workflow_history: List[Dict[str, Any]] = []

# Seed initial nominal traffic baseline
current_time = runner.generate_normal_traffic(current_time, duration_minutes=5)
logger_app.info("AutoHeal Enterprise Sentinel Initialized. Nominal baseline established.")

from shopsphere.api import router as shopsphere_router
app.include_router(shopsphere_router)

from src.appsec.middleware import AppSecProtectionMiddleware
from src.appsec.api import router as appsec_router
from src.appsec.soar_api import router as soar_router
app.add_middleware(AppSecProtectionMiddleware)
app.include_router(appsec_router)
app.include_router(soar_router)

# --- Web & Health Endpoints ---
@app.get("/shop", summary="ShopSphere E-Commerce Live Application")
async def serve_shopsphere(request: Request):
    """Serves the full-stack Flipkart-style ShopSphere e-commerce application."""
    if not templates:
        return JSONResponse({"status": "error", "message": "Templates directory not found"})
    return templates.TemplateResponse(request=request, name="shopsphere.html")

@app.get("/", summary="Serve Primary AutoHeal SOC Dashboard")
async def serve_dashboard(request: Request):
    if not templates:
        return JSONResponse({"status": "healthy", "service": "AutoHeal API", "docs": "/api/docs"})
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/health", response_model=HealthResponse, summary="Production Service Health Check")
def health_check():
    """Returns real-time service health, model availability, and monitored endpoint count."""
    active_threats = sum(1 for d in network.devices.values() if d.state != "Normal")
    return HealthResponse(
        status="HEALTHY",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="3.0.0-enterprise",
        model_loaded=detect_agent.engine.model is not None,
        devices_monitored=len(network.devices),
        active_threats=active_threats,
        environment=os.getenv("ENVIRONMENT", "production")
    )

@app.get("/api/state", response_model=NetworkStateResponse, summary="Retrieve Live Network State & Logs")
def get_state():
    """Returns all monitored enterprise assets, active threat status, and recent correlated incident logs."""
    devices = [{
        "id": d_id,
        "role": d.role,
        "ip": d.ip,
        "state": d.state,
        "zone": getattr(d, 'zone', 'Corporate LAN'),
        "risk_score": getattr(d, 'risk_score', 0)
    } for d_id, d in network.devices.items() if not (d_id.startswith("DEV00") and d_id not in ["DEV001", "DEV002"])]
    
    active_threats = sum(1 for d in network.devices.values() if d.state != "Normal")
    
    logs = []
    for h in reversed(workflow_history):
        dev = network.devices.get(h['device_id'])
        logs.append({
            "time": h['time'].strftime('%H:%M:%S'),
            "ip": dev.ip if dev else "10.0.0.0",
            "device": h['device_id'],
            "type": "AI Threat",
            "status": "BLOCKED" if h['action'] in ['BLOCK', 'ISOLATE'] else "WARNING",
            "action": h['action'],
            "verified": h['verified'],
            "mitre": h.get('mitre_tactic', 'T1078 - Valid Accounts')
        })
        
    return NetworkStateResponse(
        devices=devices,
        active_threats=active_threats,
        total_devices=str(len(devices)),
        total_incidents=len(workflow_history),
        logs=logs
    )

# --- Attack Simulation Endpoints ---
@app.post("/api/attack/{attack_type}", response_model=AttackResponse, summary="Inject Multi-Vector Adversary Simulation")
def trigger_attack(attack_type: str):
    """Simulates an adversary technique (A: Brute Force, B: Lateral Recon, C: Ransomware, D: C2 Tunnel)."""
    global current_time
    atk = attack_type.upper()
    
    if atk == "A":
        target = "CORP-LAPTOP-142"
        current_time = runner.run_attack_a(current_time, target)
        logger_app.warning(f"Adversary Attack A injected on {target}")
        return AttackResponse(status="success", message=f"Attack A launched on {target}", target_device=target, mitre_tactic="T1110 - Brute Force")
    elif atk == "B":
        target = "ENT-APP-SRV-01"
        current_time = runner.run_attack_b(current_time, target)
        logger_app.warning(f"Adversary Attack B injected on {target}")
        return AttackResponse(status="success", message=f"Attack B launched on {target}", target_device=target, mitre_tactic="T1046 - Network Discovery")
    elif atk == "C":
        target = "ENT-HR-DB-01"
        current_time = runner.run_attack_c(current_time, target)
        logger_app.warning(f"Adversary Ransomware Attack C injected on {target}")
        return AttackResponse(status="success", message=f"Ransomware Attack C launched on {target}", target_device=target, mitre_tactic="T1486 - Data Encrypted")
    elif atk == "D":
        target = "ENT-PAYMENT-DB"
        current_time = runner.run_attack_d(current_time, target)
        logger_app.warning(f"Adversary C2 Beaconing Attack D injected on {target}")
        return AttackResponse(status="success", message=f"C2 Beaconing Attack D launched on {target}", target_device=target, mitre_tactic="T1568 - Dynamic Resolution")
        
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown attack type '{attack_type}'. Supported: A, B, C, D")

# --- Autonomous Detection & Remediation ---
@app.post("/api/detect", response_model=DetectionResponse, summary="Trigger LangGraph AI Autonomous Scan")
def run_detection():
    """Executes the Detect -> Respond -> Verify loop across all monitored enterprise endpoints."""
    global current_time
    threat_found = False
    new_incidents = []
    
    for dev_id in list(network.devices.keys()):
        initial_state = {
            "device_id": dev_id,
            "current_time": current_time,
            "incident": None,
            "action_taken": None,
            "is_verified": False,
            "retry_count": 0,
            "audit_trail": []
        }
        
        running_state = dict(initial_state)
        for output in graph_manager.graph.stream(initial_state):
            for node_name, state_update in output.items():
                if isinstance(state_update, dict):
                    running_state.update(state_update)
        
        if running_state.get('incident'):
            threat_found = True
            inc = running_state['incident']
            incident_data = {
                'incident_id': getattr(inc, 'incident_id', 'INC-AUTO'),
                'device_id': dev_id,
                'time': running_state['current_time'].strftime('%H:%M:%S'),
                'action': running_state.get('action_taken', 'ISOLATE'),
                'verified': running_state.get('is_verified', False),
                'mitre_tactic': getattr(inc, 'mitre_tactic', 'T1078 - Valid Accounts'),
                'reason': getattr(inc, 'reason', 'Anomalous activity detected'),
                'audit_trail': running_state.get('audit_trail', [])
            }
            workflow_history.append({
                'device_id': dev_id,
                'time': running_state['current_time'],
                'action': running_state.get('action_taken', 'ISOLATE'),
                'verified': running_state.get('is_verified', False),
                'mitre_tactic': incident_data['mitre_tactic'],
                'incident': inc
            })
            new_incidents.append(incident_data)
            logger_app.info(f"LangGraph Agent neutralized incident on {dev_id} with action {running_state.get('action_taken')}")
            
    return DetectionResponse(threat_found=threat_found, incidents=new_incidents)

# --- Endpoint Management & Overrides ---
@app.post("/api/device/{device_id}/restore", response_model=DeviceActionResponse, summary="Restore Quarantined Endpoint")
def restore_device_endpoint(device_id: str):
    """Restores an isolated or blocked device back to Normal operating status."""
    if device_id not in network.devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    prev = network.devices[device_id].state
    network.restore_device(device_id)
    return DeviceActionResponse(
        status="success",
        device_id=device_id,
        previous_state=prev,
        current_state="Normal",
        message=f"Device {device_id} restored to nominal operating baseline."
    )

@app.post("/api/device/{device_id}/isolate", response_model=DeviceActionResponse, summary="Force Microsegmentation Isolation")
def isolate_device_endpoint(device_id: str):
    """Manually isolates an endpoint onto a quarantine VLAN."""
    if device_id not in network.devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    prev = network.devices[device_id].state
    network.isolate_device(device_id)
    return DeviceActionResponse(
        status="success",
        device_id=device_id,
        previous_state=prev,
        current_state="Isolated",
        message=f"Device {device_id} quarantined onto isolation VLAN."
    )

@app.post("/api/device/{device_id}/block", response_model=DeviceActionResponse, summary="Force 802.1X Perimeter Block")
def block_device_endpoint(device_id: str):
    """Manually shuts down switch port and blocks device at firewall perimeter."""
    if device_id not in network.devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    prev = network.devices[device_id].state
    network.block_device(device_id)
    return DeviceActionResponse(
        status="success",
        device_id=device_id,
        previous_state=prev,
        current_state="Blocked",
        message=f"Device {device_id} completely blocked at 802.1X and perimeter firewalls."
    )

@app.post("/api/reset", summary="Reset Sandbox State")
def reset_sandbox():
    """Resets all device states, clear active alerts, and re-establishes nominal baseline."""
    global current_time, workflow_history
    for d in network.devices.values():
        d.state = "Normal"
        d.risk_score = 0
    workflow_history.clear()
    current_time = runner.generate_normal_traffic(datetime.now(), duration_minutes=5)
    logger_app.info("Sandbox reset to initial nominal baseline.")
    return {"status": "success", "message": "Simulation sandbox successfully reset."}

@app.get("/api/incidents", summary="Get Full Forensic Incidents Dossier")
def get_incidents():
    """Returns complete list of incidents with extracted IoCs and forensic event logs."""
    return [
        h['incident'].to_dict() if hasattr(h.get('incident'), 'to_dict') else {
            'device_id': h['device_id'],
            'time': str(h['time']),
            'action': h['action']
        }
        for h in workflow_history
    ]

# --- Flipkart Live Demo Endpoints ---
@app.get("/flipkart", summary="Flipkart Live E-Commerce Storefront Replica")
async def serve_flipkart(request: Request):
    """Serves the interactive Flipkart Big Billion Days storefront with live AutoHeal attack simulation."""
    if not templates:
        return JSONResponse({"status": "error", "message": "Templates directory not found"})
    return templates.TemplateResponse("flipkart.html", {"request": request})

@app.get("/api/flipkart/status", summary="Get Flipkart Microservices Security Status")
def get_flipkart_status():
    """Returns security status of Flipkart microservices and real-time defense health."""
    fk_keys = ['FK-FRONTEND-GATEWAY', 'FK-STORE-APP', 'FK-AUTH-SERVICE', 'FK-CHECKOUT-PAYMENT', 'FK-INVENTORY-DB']
    services = []
    for k in fk_keys:
        d = network.devices[k]
        services.append({
            "id": k,
            "name": k.replace("FK-", "").replace("-", " ").title(),
            "ip": d.ip,
            "role": d.role,
            "zone": d.zone,
            "state": d.state,
            "risk_score": d.risk_score
        })
    compromised = [s for s in services if s['state'] != 'Normal']
    shield_status = "OPTIMAL - ZERO THREAT" if not compromised else f"ACTIVE DEFENSE - {len(compromised)} QUARANTINED"
    return {
        "services": services,
        "shield_status": shield_status,
        "active_breaches": len(compromised),
        "recent_mitigations": [
            {
                "device": h['device_id'],
                "action": h['action'],
                "mitre": h.get('mitre_tactic', 'T1078'),
                "time": h['time'].strftime('%H:%M:%S') if hasattr(h['time'], 'strftime') else str(h['time']),
                "verified": h.get('verified', True)
            }
            for h in reversed(workflow_history) if h['device_id'].startswith("FK-")
        ][:5]
    }

@app.post("/api/flipkart/attack/{scenario}", summary="Trigger Adversary Attack Against Flipkart Microservices")
def trigger_flipkart_attack(scenario: str):
    """Simulates realistic e-commerce cyber attack and triggers autonomous LangGraph self-healing."""
    global current_time
    scenario_clean = scenario.lower().strip()
    target = ""
    mitre = ""
    description = ""

    if scenario_clean in ["credential_stuffing", "auth"]:
        target = "FK-AUTH-SERVICE"
        mitre = "T1110 - Brute Force / Credential Stuffing"
        description = "Flash sale botnet attacking customer login accounts with 25+ rapid failed attempts."
        current_time = runner.run_flipkart_credential_stuffing(current_time, target)
    elif scenario_clean in ["payment_exfiltration", "card_skimming", "pci"]:
        target = "FK-CHECKOUT-PAYMENT"
        mitre = "T1048 - Exfiltration Over Alternative Protocol"
        description = "Magecart / card-skimming script attempting to siphon customer CVV and payment tokens."
        current_time = runner.run_flipkart_payment_exfiltration(current_time, target)
    elif scenario_clean in ["inventory_ransomware", "database"]:
        target = "FK-INVENTORY-DB"
        mitre = "T1486 - Data Encrypted for Impact"
        description = "Ransomware encryption spike locking warehouse inventory tables during peak flash sale."
        current_time = runner.run_flipkart_inventory_ransomware(current_time, target)
    elif scenario_clean in ["catalog_ddos", "scraper", "gateway"]:
        target = "FK-FRONTEND-GATEWAY"
        mitre = "T1046 - Network Service Discovery"
        description = "Competitor scraping botnet flooding frontend gateway and probing internal APIs."
        current_time = runner.run_flipkart_catalog_ddos(current_time, target)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario}'. Supported: credential_stuffing, payment_exfiltration, inventory_ransomware, catalog_ddos"
        )

    # Immediately execute autonomous LangGraph Detect -> Respond -> Verify loop
    initial_state = {
        "device_id": target,
        "current_time": current_time,
        "incident": None,
        "action_taken": None,
        "is_verified": False,
        "retry_count": 0,
        "audit_trail": []
    }
    running_state = dict(initial_state)
    t_heal_start = time.perf_counter()
    for output in graph_manager.graph.stream(initial_state):
        for node_name, state_update in output.items():
            if isinstance(state_update, dict):
                running_state.update(state_update)
    remediation_time_ms = round((time.perf_counter() - t_heal_start) * 1000, 2)

    action_taken = running_state.get('action_taken', 'ISOLATE')
    is_verified = running_state.get('is_verified', False)
    inc = running_state.get('incident')

    if inc:
        workflow_history.append({
            'device_id': target,
            'time': current_time,
            'action': action_taken,
            'verified': is_verified,
            'mitre_tactic': mitre,
            'incident': inc
        })

    return {
        "status": "success",
        "scenario": scenario_clean,
        "target_service": target,
        "mitre_tactic": mitre,
        "threat_description": description,
        "autonomous_action": action_taken,
        "healed_and_verified": is_verified,
        "remediation_time_ms": remediation_time_ms,
        "service_state": network.devices[target].state,
        "audit_trail": running_state.get('audit_trail', [
            f"[Detection] Anomaly detected on {target} (Confidence: 0.95)",
            f"[Correlation] Root-cause confirmed. Blast radius bounded to {target}",
            f"[Response] Autonomous Zero-Trust isolation applied. Traffic diverted to standby replica.",
            f"[Verification] Telemetry normalized. Storefront availability preserved."
        ]),
        "message": f"AutoHeal autonomous agent swarm neutralized {mitre} on {target} in {remediation_time_ms}ms!"
    }

@app.post("/api/flipkart/restore", summary="Restore All Flipkart Microservices")
def restore_flipkart():
    """Restores all Flipkart microservices back to normal operating health."""
    fk_keys = ['FK-FRONTEND-GATEWAY', 'FK-STORE-APP', 'FK-AUTH-SERVICE', 'FK-CHECKOUT-PAYMENT', 'FK-INVENTORY-DB']
    for k in fk_keys:
        network.restore_device(k)
    return {"status": "success", "message": "All Flipkart microservices restored to nominal state."}


if __name__ == "__main__":
    uvicorn.run("server:app", host=API_HOST, port=API_PORT, reload=False)
