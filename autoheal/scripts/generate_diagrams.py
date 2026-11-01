import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAGRAMS_DIR = os.path.join(BASE_DIR, "AutoHeal_Documentation", "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

DIAGRAMS = {
    "diagram_01_architecture.png": """
graph TB
    subgraph ClientTier ["Client Presentation Tier"]
        Browser["Modern Web Browser (Chrome / Edge / Firefox)"]
        UI_Store["ShopSphere E-Commerce Storefront (/shop)"]
        UI_SOC["AutoHeal CyberShield SOC Dashboard (/)"]
        UI_3D["Streamlit 3D Autonomous Threat Center (:8501)"]
        Browser --> UI_Store
        Browser --> UI_SOC
        Browser --> UI_3D
    end

    subgraph SecurityTier ["Ingress & AppSec Middleware Tier"]
        Middleware["Starlette AppSec Protection Middleware"]
        PerimeterFilter["Perimeter Request Filter & Sanitizer"]
        IPQuarantine["Dynamic IP Quarantine Gatekeeper (HTTP 403)"]
        RateLimiter["Sliding-Window Rate Limiter (HTTP 429)"]
        Middleware --> PerimeterFilter
        PerimeterFilter --> IPQuarantine
        PerimeterFilter --> RateLimiter
    end

    subgraph AppTier ["ShopSphere Core Application Services"]
        Router["FastAPI Application Router (:8000)"]
        CatalogSvc["Catalog & Product Service"]
        CartSvc["Cart & Inventory Management"]
        AuthSvc["Authentication & Session Manager"]
        OrderSvc["Order Processing & Checkout Engine"]
        Router --> CatalogSvc
        Router --> CartSvc
        Router --> AuthSvc
        Router --> OrderSvc
    end

    subgraph DefenseTier ["AutoHeal Autonomous Defense & Healing Engine"]
        DetectionEngine["Sliding-Window Threat Detector (AUTH, RATE, SQLI, XSS, ADMIN)"]
        IncidentManager["Incident Management & MITRE ATT&CK Correlation"]
        ResponseEngine["Autonomous Response Agent (Quarantine, TTL Banning)"]
        VerificationAgent["Synthetic Verification Agent (Probing & Confirmation)"]
        RemediationHub["Vulnerability Remediation Engine (Diagnosis, Patching, Rollback)"]
        Reporter["Forensic Dossier & PDF Export Service"]
        
        DetectionEngine --> IncidentManager
        IncidentManager --> ResponseEngine
        ResponseEngine --> VerificationAgent
        IncidentManager --> RemediationHub
        IncidentManager --> Reporter
    end

    subgraph StorageTier ["Persistence & Telemetry Tier"]
        DB_Telemetry[("SQLite: appsec_telemetry.db (Immutable Logs & Dossiers)")]
        DB_Shop[("SQLite: shopsphere.db (Products, Users, Orders)")]
        Cache_Quarantine[("In-Memory Active Quarantine Registry")]
    end

    UI_Store --> Middleware
    UI_SOC --> Router
    UI_3D --> DefenseTier
    IPQuarantine --> Router
    Middleware --> DB_Telemetry
    IPQuarantine -.-> Cache_Quarantine
    AppTier --> DB_Shop
    Middleware --> DetectionEngine
    ResponseEngine --> Cache_Quarantine
    IncidentManager --> DB_Telemetry
    RemediationHub --> DB_Shop
""",

    "diagram_02_dfd.png": """
graph LR
    subgraph ExternalEntities ["External Entities"]
        Shopper["Legitimate Shopper"]
        Attacker["Adversary / Threat Simulator"]
        Analyst["SOC Security Analyst"]
    end

    subgraph Processes ["AutoHeal Processing Pipeline"]
        P1["1.0 Request Ingestion & Header Fingerprinting"]
        P2["2.0 Persistent Telemetry Logging"]
        P3["3.0 Sliding-Window Threat Correlation"]
        P4["4.0 Autonomous Mitigation & IP Quarantine"]
        P5["5.0 Synthetic Containment Verification"]
        P6["6.0 Forensic Reporting & Code Healing"]
    end

    subgraph DataStores ["Data Stores"]
        D1[("D1: Telemetry Event Log")]
        D2[("D2: Incident Dossier Store")]
        D3[("D3: Active Quarantine Cache")]
        D4[("D4: ShopSphere Database")]
    end

    Shopper -->|HTTP Orders/Browse| P1
    Attacker -->|Brute-Force / Injections| P1
    P1 -->|Ingress Streams| P2
    P2 -->|Append Events| D1
    D1 -->|Event Batch Window| P3
    P3 -->|Trigger Rule Alert| D2
    P3 -->|Enact Containment| P4
    P4 -->|Write Active Ban| D3
    D3 -->|Block Filter| P1
    P4 -->|Trigger Probe| P5
    P5 -->|Probe Result: 403 Pass| D2
    D2 -->|Generate Dossier| P6
    P6 -->|Surgical Patch| D4
    Analyst -->|Review Metrics & PDF| P6
    Analyst -->|Manual Unblock / Rollback| P4
""",

    "diagram_03_class_diagram.png": """
classDiagram
    class AppSecProtectionMiddleware {
        +list blocked_ips
        +dispatch(request, call_next) Response
        +is_ip_blocked(client_ip) bool
        +record_telemetry(event_dict) void
    }

    class AppSecDetector {
        +dict detection_rules
        +evaluate_telemetry(window_seconds) list
        +detect_brute_force(client_ip) Incident
        +detect_rate_anomaly(client_ip) Incident
        +detect_injection_attack(payload) Incident
    }

    class AppSecResponder {
        +dict active_quarantines
        +quarantine_client(client_ip, ttl_seconds, reason) bool
        +release_client(client_ip) bool
        +enforce_rate_limit(client_ip) void
    }

    class VerificationAgent {
        +str target_base_url
        +probe_endpoint(endpoint, client_ip) ProbeResult
        +confirm_containment(incident_id) bool
    }

    class ShopSphereAutoHealEngine {
        +str component_path
        +diagnose_bug(error_trace) Diagnosis
        +run_regression_tests() TestReport
        +apply_surgical_patch(patch_id) bool
        +rollback_patch(patch_id) bool
    }

    class SecurityIncident {
        +str incident_id
        +str rule_id
        +str severity
        +str status
        +float confidence
        +str source_ip
        +dict evidence
        +str verification_status
    }

    class AppSecReporter {
        +generate_pdf_report(incident_id) bytes
        +generate_json_dossier(incident_id) dict
        +generate_markdown_report(incident_id) str
    }

    AppSecProtectionMiddleware --> AppSecDetector : feeds telemetry
    AppSecDetector --> SecurityIncident : instantiates
    AppSecDetector --> AppSecResponder : triggers containment
    AppSecResponder --> VerificationAgent : requests verification
    SecurityIncident --> AppSecReporter : rendered by
    SecurityIncident --> ShopSphereAutoHealEngine : initiates code healing
""",

    "diagram_04_use_case.png": """
graph TB
    subgraph Actors ["System Actors"]
        Shopper((Legitimate Shopper))
        Attacker((Threat Actor / Simulator))
        Analyst((SOC Security Analyst))
        Sentinel((AutoHeal Sentinel Agent))
    end

    subgraph ShopSphereCases ["ShopSphere E-Commerce Use Cases"]
        UC1["Browse Product Catalog"]
        UC2["Add Item to Cart"]
        UC3["User Login & Authentication"]
        UC4["Checkout & Order Placement"]
    end

    subgraph AutoHealCases ["AutoHeal Defense & Incident Use Cases"]
        UC5["Simulate Bounded Attack Scenario"]
        UC6["Stream Real-Time Telemetry"]
        UC7["Detect Cyber Threat & Correlate"]
        UC8["Enforce Dynamic IP Quarantine"]
        UC9["Execute Synthetic Verification Probe"]
        UC10["Investigate Incident Dossier"]
        UC11["Export Audit-Ready PDF Report"]
        UC12["Trigger Code Healing & Rollback"]
    end

    Shopper --> UC1
    Shopper --> UC2
    Shopper --> UC3
    Shopper --> UC4

    Attacker --> UC5
    Attacker -.->|Targets| UC3

    Sentinel --> UC6
    Sentinel --> UC7
    Sentinel --> UC8
    Sentinel --> UC9

    Analyst --> UC10
    Analyst --> UC11
    Analyst --> UC12
    Analyst --> UC5
""",

    "diagram_05_sequence.png": """
sequenceDiagram
    autonumber
    actor Attacker as Threat Simulator
    participant Middleware as AppSec Middleware
    participant Detector as Sliding-Window Detector
    participant Store as Telemetry DB (SQLite)
    participant Responder as Quarantine Sentinel
    participant Verifier as Verification Engine
    participant SOC as AutoHeal SOC Dashboard

    Attacker->>Middleware: POST /api/auth/login (Invalid Credential #1..#4)
    Middleware->>Store: Persist SecurityEvent(AUTH_FAILURE, 401)
    Middleware-->>Attacker: 401 Unauthorized

    Detector->>Store: Query sliding window (60s aggregate)
    Store-->>Detector: 4 failed attempts from IP 198.51.100.99
    Detector->>Detector: Correlate Rule AUTH-001 (Confidence 96%)
    Detector->>Store: Insert Incident INC-2026-329E3D6E (HIGH, MITIGATING)
    
    Detector->>Responder: Trigger Containment(IP=198.51.100.99, TTL=300s)
    Responder->>Middleware: Register Quarantine Rule (HTTP 403 Forbidden)
    
    Responder->>Verifier: Dispatch Synthetic Verification Probe
    Verifier->>Middleware: GET /api/shop (Header: X-Forwarded-For: 198.51.100.99)
    Middleware-->>Verifier: HTTP 403 Forbidden (Blocked by Quarantine)
    Verifier->>Store: Update Incident(Status=VERIFIED_CONTAINED)
    
    Store->>SOC: Push SSE Telemetry & Update Posture Score (65/100)
    
    Attacker->>Middleware: POST /api/auth/login (Subsequent attempt)
    Middleware-->>Attacker: HTTP 403 Forbidden (Perimeter Terminated)
""",

    "diagram_06_activity.png": """
graph TD
    Start([HTTP Request Arrives at Port 8000]) --> CheckQuarantine{Is Client IP in Active Quarantine?}
    
    CheckQuarantine -- Yes --> Return403[Return HTTP 403 Forbidden]
    Return403 --> LogBlockEvent[Record Telemetry: QUARANTINE_BLOCKED]
    LogBlockEvent --> TerminateRequest([Connection Terminated])
    
    CheckQuarantine -- No --> RouteToHandler[Route to Target API / Frontend Handler]
    RouteToHandler --> ExecuteEndpoint[Process Business Logic e.g., Shop / Auth]
    ExecuteEndpoint --> CaptureResponse[Capture Response Status & Latency]
    CaptureResponse --> LogEvent[Record Telemetry in appsec_telemetry.db]
    
    LogEvent --> EvaluateWindow{Sliding Window Pattern Exceeds Threshold?}
    EvaluateWindow -- No --> PassThrough([Response Dispatched to Client])
    
    EvaluateWindow -- Yes --> GenerateIncident[Create Security Incident Dossier]
    GenerateIncident --> EnactMitigation[Enact Policy Containment: Block IP / Rate-Limit]
    EnactMitigation --> UpdateQuarantineCache[Register IP in Sentinel Active Cache with TTL]
    
    UpdateQuarantineCache --> LaunchProbe[Launch Synthetic Verification Probe]
    LaunchProbe --> CheckProbe{Did Probe Receive 403 Forbidden?}
    
    CheckProbe -- Yes --> MarkContained[Set Verification State: VERIFIED_CONTAINED]
    CheckProbe -- No --> EscalateAlert[Set Verification State: ESCALATED_HITL]
    
    MarkContained --> PushSSE[Push Live SSE Update to SOC Dashboard]
    EscalateAlert --> PushSSE
    PushSSE --> End([Monitoring Active])
""",

    "diagram_07_deployment.png": """
graph TB
    subgraph ClientHost ["Client Tier (Analyst / Shopper Workstation)"]
        BrowserApp["Web Browser Client (Google Chrome / Microsoft Edge)"]
    end

    subgraph ServerNode ["Host Node Runtime (Local Host Machine)"]
        FastAPIServer["FastAPI / Uvicorn ASGI Server (Port 8000)"]
        ShopSphereApp["ShopSphere E-Commerce Application (/shop)"]
        AutoHealSOCApp["AutoHeal CyberShield SOC Console (/)"]
        AppSecMW["Starlette AppSec Security Middleware"]
        StreamlitServer["Streamlit 3D Autonomous Threat Hub (Port 8501)"]
        LangGraphEngine["LangGraph Multi-Agent Orchestrator"]
    end

    subgraph StorageNode ["Persistent Storage Layer (Local SQLite Engines)"]
        DB_AppSec[("appsec_telemetry.db (Security Events & Incidents)")]
        DB_ShopCore[("shopsphere.db (Products, Users, Orders)")]
        DB_AuditLogs[("data/appsec_audit.log (JSON Lines Stream)")]
    end

    BrowserApp -->|HTTP/REST & SSE| FastAPIServer
    BrowserApp -->|HTTP & WebSockets| StreamlitServer

    FastAPIServer --> ShopSphereApp
    FastAPIServer --> AutoHealSOCApp
    FastAPIServer --> AppSecMW

    StreamlitServer --> LangGraphEngine

    FastAPIServer --> DB_AppSec
    FastAPIServer --> DB_ShopCore
    FastAPIServer --> DB_AuditLogs
    StreamlitServer --> DB_AppSec
"""
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            background: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 40px;
        }}
        #diagram-wrapper {{
            display: inline-block;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div id="diagram-wrapper">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'neutral',
            flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis' }},
            sequence: {{ useMaxWidth: false, showSequenceNumbers: true }}
        }});
    </script>
</body>
</html>
"""

def generate_all_diagrams():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=2600,2000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    temp_html_path = os.path.join(DIAGRAMS_DIR, "temp_diagram.html")

    try:
        for filename, code in DIAGRAMS.items():
            print(f"Rendering {filename}...")
            html_content = HTML_TEMPLATE.format(mermaid_code=code.strip())
            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            driver.get(f"file:///{temp_html_path.replace(os.sep, '/')}")
            time.sleep(3)

            wrapper = driver.find_element(By.ID, "diagram-wrapper")
            out_path = os.path.join(DIAGRAMS_DIR, filename)
            wrapper.screenshot(out_path)
            print(f"Saved: {filename} ({os.path.getsize(out_path)} bytes)")

        print("All 7 architectural diagrams rendered successfully with perfect wrapping!")
    finally:
        driver.quit()
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)

if __name__ == "__main__":
    generate_all_diagrams()
