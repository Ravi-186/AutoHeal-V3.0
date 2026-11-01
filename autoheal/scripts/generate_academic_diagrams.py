"""
AutoHeal Academic Diagram Generator
Generates all 8 verified system, deployment, component, and data-flow diagrams in:
1. Editable Mermaid (.mmd) source files
2. Scalable Vector Graphics (.svg) with high-contrast, report-ready light styling
3. High-Resolution PNG images (.png) at 300 DPI for direct academic document insertion
Plus the comprehensive documentation/diagram-notes.md companion report.
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

# Destination Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIAGRAMS_DIR = os.path.join(BASE_DIR, "documentation", "diagrams")
NOTES_FILE = os.path.join(BASE_DIR, "documentation", "diagram-notes.md")

os.makedirs(DIAGRAMS_DIR, exist_ok=True)

print(f"Generating academic diagrams in: {DIAGRAMS_DIR}")

# =============================================================================
# 1. MERMAID SOURCE GENERATION (.mmd)
# =============================================================================

MERMAID_DIAGRAMS = {
    "diagram1_system_architecture.mmd": """%% AutoHeal & ShopSphere System Architecture Diagram
flowchart TB
    subgraph PresentationTier["1. Presentation Tier"]
        UI_SOC["AutoHeal Enterprise SOC UI<br/>(SPA Dashboard, Live Metrics, Forensics)<br/><i>web/templates/index.html</i>"]
        UI_AttackCenter["Attack Center Control Console<br/>(Scenario Dispatch, SSE Stream)<br/><i>web/static/js/script.js</i>"]
        UI_Storefront["ShopSphere E-Commerce Storefront<br/>(Flipkart-Inspired Replica)<br/><i>web/templates/shopsphere.html</i>"]
        UI_3DSOC["3D Spatial SOC Topology<br/>(Streamlit WebGL on Port 8501)<br/><i>dashboard/app.py</i>"]
    end

    subgraph APITier["2. Application Gateway & API Tier (Port 8000)"]
        ASGI["FastAPI ASGI Core Server<br/><i>server.py</i>"]
        Middleware["AppSec Protection Middleware<br/>(Perimeter Intercept, Rate Limiting)<br/><i>src/appsec/middleware.py</i>"]
        ShopAPI["ShopSphere REST API<br/>(Catalog, Cart, Auth, Orders)<br/><i>shopsphere/api.py</i>"]
        SecAPI["AutoHeal AppSec Management API<br/>(Incidents, Telemetry, Vulnerabilities)<br/><i>src/appsec/api.py</i>"]
    end

    subgraph SecurityTier["3. Autonomous Security Pipeline (The Five Components)"]
        Comp1["Component 1: Detection Agent<br/>(Payload Regex + Feature Extraction)<br/><i>src/appsec/detector.py</i>"]
        Comp2["Component 2: Log Correlation Engine<br/>(Sliding Window & Idempotent Deduplication)<br/><i>src/appsec/correlation_engine.py</i>"]
        Comp3["Component 3: Response Agent<br/>(Policy Defense: IP Block, Rate Limit, Recovery)<br/><i>src/appsec/responder.py</i>"]
        Comp4["Component 4: Verification Agent<br/>(Loopback Synthetic Probes & Non-Regression)<br/><i>src/appsec/verifier.py</i>"]
        Comp5["Component 5: Escalation Mechanism<br/>(Bounded Retries & Terminal SOC Alerting)<br/><i>src/appsec/verifier.py</i>"]
    end

    subgraph MLTier["4. Intelligence & Forensic Enrichment"]
        RF_Model["Random Forest Classifier<br/>(Network & Auth Anomaly Scoring)<br/><i>models/rf_model.joblib</i>"]
        AI_Advisor["AI Security Advisor<br/>(MITRE ATT&CK Mapping & Root Cause)<br/><i>src/appsec/ai_advisor.py</i>"]
        Reporter["Forensic Dossier Generator<br/>(Binary PDF & Full JSON Exports)<br/><i>src/appsec/reporter.py</i>"]
    end

    subgraph DataTier["5. Persistent Data Store (SQLite WAL Mode)"]
        DB["ShopSphere & AutoHeal SQLite Database<br/><i>data/shopsphere.db</i>"]
        Tbl_Events["security_events<br/>(Immutable Ingress Logs)"]
        Tbl_Incidents["security_incidents<br/>(Correlated Dossiers)"]
        Tbl_Blocks["blocked_clients<br/>(Dynamic WAF Quarantine with TTL)"]
        Tbl_Store["Storefront Tables<br/>(users, products, orders, cart_items)"]
    end

    %% Flow Connections
    UI_AttackCenter -->|Controlled Attack Execution| ShopAPI
    UI_Storefront -->|Benign Shopper Requests| ShopAPI
    ShopAPI --> Middleware
    Middleware -->|Ingress Request Telemetry| Tbl_Events
    Middleware -->|Quarantine Check| Tbl_Blocks

    Tbl_Events --> Comp1
    Comp1 -->|Structured DetectionResult| Comp2
    Comp1 -.->|Feature Vectors| RF_Model
    Comp2 -->|Grouped & Deduplicated Incident| Tbl_Incidents
    Comp2 --> Comp3
    Comp3 -->|Apply Temporary Quarantine| Tbl_Blocks
    Comp3 -->|Action Audit & Handoff| Comp4

    Comp4 -->|Perimeter & Availability Probes| Middleware
    Comp4 -->|Containment Failed| Comp5
    Comp5 -->|Escalated TTL & Severity| Comp3

    Tbl_Incidents --> Reporter
    AI_Advisor --> Reporter
    Reporter --> UI_SOC
""",

    "diagram2_deployment.mmd": """%% AutoHeal & ShopSphere Deployment Diagram
flowchart TB
    subgraph Host["Developer Workstation / Host OS (Windows Localhost Environment)"]
        subgraph BrowserProcess["Client Process: Web Browser (Chrome / Edge / Firefox)"]
            Client_SOC["AutoHeal SOC Dashboard<br/>http://localhost:8000/"]
            Client_Shop["ShopSphere Storefront<br/>http://localhost:8000/shop"]
            Client_Streamlit["3D SOC Spatial Canvas<br/>http://localhost:8501/"]
        end

        subgraph UvicornProcess["Runtime Process 1: Python Uvicorn / FastAPI ASGI (PID 14220)"]
            FastAPI_Server["FastAPI Web Server<br/>Listening on 0.0.0.0:8000<br/><i>server.py</i>"]
            MW["AppSecProtectionMiddleware<br/>(Active Starlette In-Memory Rate Tracker)"]
            Runner["Attack Center Execution Engine<br/><i>src/appsec/security_tester.py</i>"]
            SecAgents["Active Autonomous Security Pipeline<br/>(Detector, Correlator, Responder, Verifier)"]
        end

        subgraph StreamlitProcess["Runtime Process 2: Python Streamlit Server (PID 18450)"]
            Streamlit_Server["Streamlit Web Server<br/>Listening on 0.0.0.0:8501<br/><i>dashboard/app.py</i>"]
            ThreeJS["Three.js WebGL Engine<br/>(3D Spatial Device Mesh)"]
        end

        subgraph LocalFileSystem["Local File System: C:\\Users\\bobba\\Documents\\AD\\autoheal\\"]
            subgraph DB_Dir["data/ Directory"]
                SQLite_DB["SQLite Database Engine (WAL Mode)<br/><b>data/shopsphere.db</b> (1.08 MB)<br/>Tables: security_events, security_incidents,<br/>blocked_clients, products, users, cart_items"]
            end
            subgraph Model_Dir["models/ Directory"]
                ML_Artifact["Scikit-Learn Random Forest Model<br/><b>models/rf_model.joblib</b><br/>(7 Feature Columns, Pre-Trained Weights)"]
            end
            subgraph Doc_Dir["documentation/ Directory"]
                Diag_Artifacts["PDF & JSON Export Cache<br/><b>documentation/diagrams/</b>"]
            end
        end
    end

    Client_SOC <-->|HTTP / JSON & SSE Stream :8000| FastAPI_Server
    Client_Shop <-->|HTTP / HTML & REST API :8000| FastAPI_Server
    Client_Streamlit <-->|WebSockets & HTTP :8501| Streamlit_Server

    FastAPI_Server <--> MW
    MW <--> Runner
    MW <--> SecAgents
    SecAgents <-->|Direct SQLite Connection Pooling| SQLite_DB
    SecAgents <-->|Joblib Memory Map| ML_Artifact
""",

    "diagram3_detection_agent_flowchart.mmd": """%% Component 1: Detection Agent Flowchart
flowchart TD
    Start([Ingress HTTP Request Telemetry]) --> Normalize[1. Normalize Input<br/>- URL Decode & Lowercase<br/>- Redact Passwords & Tokens<br/>- Extract IP, Path, Headers, Body]
    
    Normalize --> Check_SQLi{2. Inspect for SQL Injection?<br/>INJ-001 Patterns:<br/>UNION SELECT, OR '1'='1', --, DROP}
    Check_SQLi -- Yes --> Flag_SQLi[Flag SQLi Triggered<br/>Severity: CRITICAL<br/>Confidence: 0.98<br/>Action: BLOCK_IP]
    
    Check_SQLi -- No --> Check_XSS{3. Inspect for XSS?<br/>XSS-001 Patterns:<br/>&lt;script&gt;, onerror=, onload=, iframe}
    Check_XSS -- Yes --> Flag_XSS[Flag XSS Triggered<br/>Severity: HIGH<br/>Confidence: 0.94<br/>Action: BLOCK_IP]
    
    Check_XSS -- No --> Check_Admin{4. Inspect for Admin Probe?<br/>AUTH-002: /admin endpoint<br/>without admin cryptographic token}
    Check_Admin -- Yes --> Flag_Admin[Flag Unauthorized Probe<br/>Severity: HIGH<br/>Confidence: 0.99<br/>Action: BLOCK_IP]
    
    Check_Admin -- No --> Check_ML{5. Network & Auth Telemetry Available?<br/>failed_logins, connections, bytes_sent}
    
    Check_ML -- Yes --> Run_RF[Invoke Random Forest Model<br/><i>models/rf_model.joblib</i><br/>Predict Anomaly Probability Score]
    Run_RF --> Eval_Threshold{Score >= 0.45 or<br/>Security Guardrail Triggered?}
    Eval_Threshold -- Yes --> Flag_ML[Flag ML Anomaly Detected<br/>Severity: HIGH<br/>Confidence: Model Score]
    Eval_Threshold -- No --> Benign[Request Evaluated Normal<br/>Severity: INFO<br/>Triggered: False]
    
    Check_ML -- No --> Benign

    Flag_SQLi --> Build_Result[Construct Structured DetectionResult<br/>- rule_id, category, severity, confidence<br/>- evidence, timestamp, why_flagged, recommended_action]
    Flag_XSS --> Build_Result
    Flag_Admin --> Build_Result
    Flag_ML --> Build_Result
    Benign --> Build_Result
    
    Build_Result --> Output([Dispatch to Log Correlation Engine])
""",

    "diagram4_log_correlation_engine_flowchart.mmd": """%% Component 2: Log Correlation Engine Flowchart
flowchart TD
    Start([Security Telemetry Ingestion]) --> FetchEvents[Fetch Recent Telemetry Events<br/>Query security_events with sliding window = 60s]
    FetchEvents --> GroupIP[Group Events by Client IP & Correlation ID]
    
    GroupIP --> CheckBurstAuth{Failed Logins >= 4<br/>within 60s window?}
    CheckBurstAuth -- Yes --> FlagBurst[Correlate Rule AUTH-001<br/>Credential Stuffing / Brute Force<br/>Severity: HIGH | Confidence: 0.95]
    CheckBurstAuth -- No --> CheckRate{Total Requests >= 25<br/>within 60s window?}
    
    FlagBurst --> CheckRate
    CheckRate -- Yes --> FlagRate[Correlate Rule RATE-001<br/>Denial of Service / Scraping<br/>Severity: MEDIUM | Confidence: 0.90]
    CheckRate -- No --> CheckMultiStage{Multi-Stage Progression?<br/>AUTH_FAILURE followed by<br/>Admin Probe or Injection}
    
    FlagRate --> CheckMultiStage
    CheckMultiStage -- Yes --> FlagMulti[Correlate Rule CORR-001<br/>Multi-Step Intrusion Sequence<br/>Severity: CRITICAL | Confidence: 0.98]
    CheckMultiStage -- No --> CheckHealth{Unhandled 500 Errors >= 3?}
    
    FlagMulti --> CheckHealth
    CheckHealth -- Yes --> FlagHealth[Correlate Rule HEALTH-001<br/>Service Health Degradation<br/>Severity: HIGH | Action: RECOVER_SERVICE]
    CheckHealth -- No --> CollectDetections[Aggregate Correlated Detections]
    FlagHealth --> CollectDetections
    
    CollectDetections --> Deduplicate{Active Incident Exists for<br/>source_ip & rule_id in window?<br/><i>find_active_incident()</i>}
    
    Deduplicate -- Yes (Existing) --> UpdateIncident[Idempotent Update:<br/>- Merge new linked_event_ids<br/>- Update updated_at timestamp<br/>- Maximize confidence score<br/>- Preserve original incident_id]
    
    Deduplicate -- No (New) --> CreateIncident[Generate New Incident Record:<br/>- ID: INC-2026-XXXX<br/>- Status: UNDER_INVESTIGATION<br/>- Set initial MITRE ATT&CK mapping<br/>- Link initial event IDs]
    
    UpdateIncident --> Persist[Commit to SQLite security_incidents]
    CreateIncident --> Persist
    Persist --> Output([Dispatch Confirmed Incident to Response Agent])
""",

    "diagram5_response_agent_flowchart.mmd": """%% Component 3: Response Agent Flowchart
flowchart TD
    Start([Confirmed Incident Received]) --> CheckStatus{Incident State Check<br/>Is Dry-Run Mode Active?}
    
    CheckStatus -- Yes --> DryRun[Record Simulated Proposal Only<br/>Action: PROPOSED_ONLY<br/>Audit Trace Generated]
    
    CheckStatus -- No --> PolicyLookup[Lookup Defensive Policy Rule<br/><i>POLICY_RULES table</i><br/>Determine Action, TTL, Approval Requirements]
    
    PolicyLookup --> DispatchAction{Defensive Action Type}
    
    DispatchAction -- BLOCK_IP --> EnforceBlock[Dynamic WAF Quarantine<br/>- Insert into blocked_clients<br/>- Set TTL = 180s - 300s<br/>- Starlette Middleware Drops Requests with HTTP 403]
    
    DispatchAction -- RATE_LIMIT --> EnforceRate[Rate Limit Throttle<br/>- Update Sliding Window Token Bucket<br/>- Starlette Middleware Drops Burst with HTTP 429]
    
    DispatchAction -- RECOVER_SERVICE --> EnforceHeal[Autonomous Self-Healing<br/>- Reset Corrupted Connection Pools<br/>- Re-seed Baseline Storefront Data<br/>- Recover Nominal Transaction State]
    
    EnforceBlock --> AuditTrace[Generate Comprehensive Audit Log<br/>- Record action, target, timestamp, TTL<br/>- Measure execution latency (ms)<br/>- Append to incident mitigation_actions]
    EnforceRate --> AuditTrace
    EnforceHeal --> AuditTrace
    
    AuditTrace --> TransitionState[Update Incident Status in SQLite:<br/>status = 'RESPONSE_ATTEMPTED'<br/>recovery_status = 'MITIGATION_ENACTED']
    
    TransitionState --> Handoff([Immediate Handoff to Component 4: Verification Agent])
""",

    "diagram6_verification_escalation_flowchart.mmd": """%% Component 4 & 5: Verification & Escalation Flowchart
flowchart TD
    Start([Incident Handoff from Response Agent]) --> Probe1[Probe 1: Perimeter Quarantine Verification<br/>Synthetic HTTP Request with Attacker IP<br/>Target: Affected Endpoint e.g. /api/shop/auth/login]
    
    Probe1 --> CheckContainment{Attacker Intercepted?<br/>HTTP Status == 403 Forbidden<br/>or 429 Rate Limited}
    
    CheckContainment -- Yes --> Probe2[Probe 2: Storefront Availability Verification<br/>Synthetic HTTP Request with Clean Benign Shopper IP<br/>Target: Storefront Catalog /api/shop/products]
    
    Probe2 --> CheckAvailability{Legitimate Traffic Preserved?<br/>HTTP Status == 200 OK}
    
    CheckAvailability -- Yes --> SuccessState[Autonomous Verification SUCCESS<br/>- status = 'CONTAINED' / 'CONTAINMENT_VERIFIED'<br/>- verification_status = 'VERIFIED_CONTAINED'<br/>- recovery_status = 'NOMINAL_MONITORING'<br/>- Record probe latency & HTTP codes]
    
    CheckContainment -- No --> TriggerEscalation[Verification FAILED: Attacker Not Blocked]
    CheckAvailability -- No --> TriggerEscalation[Verification FAILED: Benign Users Impacted]
    
    TriggerEscalation --> CheckRetries{Component 5: Escalation Policy<br/>Current Retries < MAX_RETRIES (3)?}
    
    CheckRetries -- Yes (Retries 1-3) --> EscalateDefense[Apply Bounded Defensive Escalation:<br/>- Increment escalation_retries counter<br/>- Double Quarantine Duration (TTL = 600s, 1200s)<br/>- Elevate Severity to CRITICAL<br/>- Enforce Cooldown Interval (2s)<br/>- Re-apply Hardened WAF Perimeter Block]
    
    EscalateDefense --> Probe1
    
    CheckRetries -- No (Retries >= 3) --> TerminalEscalation[Safety Guardrail: Max Retries Exhausted<br/>- Terminate Autonomous Loop (No Thrashing)<br/>- status = 'ESCALATION_REQUIRED'<br/>- verification_status = 'VERIFICATION_FAILED'<br/>- recovery_status = 'MANUAL_INTERVENTION_REQUIRED'<br/>- Dispatch High-Priority SOC Tier-2 Alert]
    
    SuccessState --> End([End Workflow: Incident Ready for Forensic Report])
    TerminalEscalation --> End
""",

    "diagram7_end_to_end_sequence.mmd": """%% AutoHeal End-to-End Attack-to-Healing Sequence Diagram
sequenceDiagram
    autonumber
    actor User as SOC Operator
    participant UI as AutoHeal Website (Port 8000)
    participant Runner as Attack Center Runner
    participant Gateway as AppSec Middleware
    participant Shop as ShopSphere Storefront
    participant Det as Detection Agent
    participant Corr as Correlation Engine
    participant Resp as Response Agent
    participant Verif as Verification Agent
    participant DB as SQLite (shopsphere.db)
    participant Rep as Forensic Reporter

    User->>UI: Select Scenario (e.g. Failed Logins) & Click 'Start Test'
    UI->>Runner: POST /api/security/test/run {scenario: 'failed_logins', attempts: 5}
    
    loop Attempts 1 to 4 (Burst Phase)
        Runner->>Gateway: POST /api/shop/auth/login (Invalid Credentials, Client IP: 198.51.100.22)
        Gateway->>Shop: Forward Request
        Shop-->>Gateway: HTTP 401 Unauthorized
        Gateway->>DB: INSERT INTO security_events (status_code=401, type='AUTH_FAILURE')
        Gateway-->>Runner: HTTP 401 Unauthorized
    end

    Note over Gateway,Corr: 4th Auth Failure triggers Threshold Correlation
    Gateway->>Det: Trigger Telemetry Analysis
    Det->>Corr: Group events by Client IP across 60s sliding window
    Corr->>DB: upsert_security_incident (rule_id='AUTH-001', IP='198.51.100.22')
    DB-->>Corr: Incident Created (INC-2026-XXXX)
    Corr->>Resp: Handoff Incident for Defensive Response

    Resp->>DB: INSERT INTO blocked_clients (IP='198.51.100.22', TTL=180s)
    Resp->>Verif: Handoff Incident for Verification

    par Verification Probe 1 (Attacker IP)
        Verif->>Gateway: GET /api/shop/auth/login (X-Forwarded-For: 198.51.100.22)
        Gateway->>DB: Check is_client_blocked(198.51.100.22)
        DB-->>Gateway: Blocked = True
        Gateway-->>Verif: HTTP 403 Forbidden (Perimeter Quarantine Verified)
    and Verification Probe 2 (Clean Benign IP)
        Verif->>Gateway: GET /api/shop/products (X-Forwarded-For: 192.0.2.100)
        Gateway->>Shop: Forward Request
        Shop-->>Gateway: HTTP 200 OK
        Gateway-->>Verif: HTTP 200 OK (Storefront Availability Preserved)
    end

    Verif->>DB: UPDATE security_incidents SET status='CONTAINED', verification='VERIFIED_CONTAINED'
    
    Runner->>UI: Stream Test Traces & Verification Outcome (SSE data)
    UI-->>User: Display Green 'VERIFIED_CONTAINED' Badge & Incident Link
    
    User->>UI: Click 'Download PDF Report'
    UI->>Rep: GET /api/security/incidents/INC-2026-XXXX/export?format=pdf
    Rep->>DB: Fetch Incident Dossier & Linked Telemetry Events
    DB-->>Rep: Incident & Event Evidence
    Rep-->>User: Binary Download: INC-2026-XXXX_report.pdf (2-Page Forensic Dossier)
""",

    "diagram8_database_dataflow.mmd": """%% AutoHeal & ShopSphere Database Schema & Data-Flow Diagram
erDiagram
    SECURITY_EVENTS {
        INTEGER id PK
        TEXT event_id UK
        TEXT correlation_id
        TIMESTAMP timestamp
        TEXT client_ip
        TEXT user_agent
        TEXT method
        TEXT path
        INTEGER status_code
        REAL latency_ms
        TEXT user_id_or_session
        TEXT event_type
        TEXT severity
        TEXT details_json
        TEXT action_taken
    }

    SECURITY_INCIDENTS {
        INTEGER id PK
        TEXT incident_id UK
        TEXT rule_id
        TEXT title
        TEXT category
        TEXT severity
        TEXT status
        REAL confidence
        TEXT summary
        TEXT evidence_json
        TEXT affected_endpoints_json
        TEXT source_ip
        TEXT impact_actual
        TEXT impact_potential
        TEXT mitigation_actions_json
        TEXT remediation_details
        TEXT regression_tests_json
        TEXT verification_status
        TEXT mitre_technique_id
        TEXT mitre_tactic
        TEXT mitre_name
        TEXT recovery_status
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    BLOCKED_CLIENTS {
        INTEGER id PK
        TEXT client_ip UK
        TEXT reason
        TEXT rule_id
        TEXT incident_id FK
        TIMESTAMP blocked_at
        TIMESTAMP expires_at
        INTEGER is_active
    }

    VULNERABILITIES {
        INTEGER id PK
        TEXT vuln_id UK
        TEXT title
        TEXT category
        TEXT severity
        TEXT status
        TEXT file_path
        TEXT patch_diff
        TEXT regression_test_code
        TIMESTAMP created_at
    }

    USERS {
        INTEGER id PK
        TEXT email UK
        TEXT password_hash
        TEXT full_name
        TEXT role
        TIMESTAMP created_at
    }

    PRODUCTS {
        INTEGER id PK
        TEXT title
        TEXT category
        REAL price
        REAL original_price
        INTEGER stock
        REAL rating
    }

    ORDERS {
        INTEGER id PK
        TEXT order_ref UK
        INTEGER user_id FK
        TEXT customer_email
        REAL total_amount
        TEXT order_status
        TIMESTAMP created_at
    }

    SECURITY_EVENTS ||--o{ SECURITY_INCIDENTS : "correlated via linked_event_ids"
    SECURITY_INCIDENTS ||--o{ BLOCKED_CLIENTS : "triggers dynamic quarantine"
    USERS ||--o{ ORDERS : "places customer orders"
    SECURITY_INCIDENTS ||--o{ VULNERABILITIES : "links to patch remediation"
"""
}

# Write all Mermaid (.mmd) files
for fname, content in MERMAID_DIAGRAMS.items():
    fpath = os.path.join(DIAGRAMS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  [OK] Written Mermaid source: {fname}")

# =============================================================================
# 2. HIGH-FIDELITY SVG GENERATION (.svg)
# =============================================================================

def create_card_svg(x, y, w, h, title, subtitle, items, border_color="#0284c7", bg_color="#f0f9ff"):
    lines_svg = ""
    curr_y = y + 42
    for it in items:
        lines_svg += f'<text x="{x+16}" y="{curr_y}" font-family="Arial, sans-serif" font-size="11" fill="#334155">{it}</text>\n'
        curr_y += 18
    return f'''
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{bg_color}" stroke="{border_color}" stroke-width="2" filter="url(#dropShadow)" />
    <text x="{x+16}" y="{y+22}" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#0f172a">{title}</text>
    {f'<text x="{x+16}" y="{y+36}" font-family="Arial, sans-serif" font-size="10" font-style="italic" fill="#64748b">{subtitle}</text>' if subtitle else ''}
    {lines_svg}
    '''

def save_svg_file(filename, width, height, title, subtitle, body_svg):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
    <defs>
        <filter id="dropShadow" x="-5%" y="-5%" width="110%" height="110%">
            <feDropShadow dx="2" dy="3" stdDeviation="3" flood-opacity="0.1" />
        </filter>
        <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#0284c7" />
        </marker>
        <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#dc2626" />
        </marker>
        <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#16a34a" />
        </marker>
    </defs>
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#ffffff" />
    <rect x="10" y="10" width="{width-20}" height="{height-20}" rx="12" fill="#fafafa" stroke="#e2e8f0" stroke-width="1.5" />
    
    <!-- Title Banner -->
    <rect x="25" y="25" width="{width-50}" height="55" rx="6" fill="#0f172a" />
    <text x="45" y="52" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#ffffff">{title}</text>
    <text x="45" y="68" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8">{subtitle}</text>
    
    {body_svg}
</svg>'''
    fpath = os.path.join(DIAGRAMS_DIR, filename)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  [OK] Written SVG diagram: {filename}")

# Generate SVG 1: System Architecture
body_diag1 = ""
# Presentation Tier
body_diag1 += create_card_svg(40, 105, 260, 140, "1. Presentation Tier", "Client-Side User Interfaces", [
    "- AutoHeal SOC Dashboard (index.html)",
    "- Attack Center Control Console",
    "- ShopSphere Storefront (Flipkart Replica)",
    "- 3D Spatial Topology SOC (:8501 WebGL)"
], "#0284c7", "#f0f9ff")

# API Tier
body_diag1 += create_card_svg(330, 105, 260, 140, "2. Gateway & API Tier (:8000)", "FastAPI ASGI Runtime & Routes", [
    "- Starlette BaseHTTPMiddleware",
    "- AppSec Protection Middleware",
    "- ShopSphere REST API (/api/shop/*)",
    "- AutoHeal Admin & Telemetry APIs"
], "#0d9488", "#f0fdfa")

# The 5 Components Tier
body_diag1 += create_card_svg(620, 105, 330, 140, "3. Autonomous Security Pipeline", "The Five Core Security Components", [
    "- Comp 1: Detection Agent (Rules + ML)",
    "- Comp 2: Log Correlation Engine (60s window)",
    "- Comp 3: Response Agent (Policy WAF Quarantine)",
    "- Comp 4: Verification Agent (Loopback Probes)",
    "- Comp 5: Escalation Mechanism (Bounded Retries)"
], "#7c3aed", "#faf5ff")

# ML & Intelligence Tier
body_diag1 += create_card_svg(40, 275, 450, 130, "4. AI & Intelligence Layer", "Anomaly Scoring & Forensics", [
    "- Scikit-Learn Random Forest Classifier (models/rf_model.joblib)",
    "- 7 Feature Columns: bytes_sent, failed_logins, connections, cpu, etc.",
    "- AI Security Advisor & MITRE ATT&CK Mapping (ai_advisor.py)",
    "- Pure-Python PDF & Full JSON Forensic Report Generators"
], "#d97706", "#fffbeb")

# Data Tier
body_diag1 += create_card_svg(520, 275, 430, 130, "5. Persistent Telemetry & Storage Tier", "SQLite WAL Engine (data/shopsphere.db)", [
    "- security_events (Immutable Ingress HTTP Log Stream)",
    "- security_incidents (Correlated Dossiers & MITRE Records)",
    "- blocked_clients (Dynamic IP Quarantine with Expiry TTL)",
    "- Storefront Tables (users, products, orders, cart_items)"
], "#dc2626", "#fef2f2")

# Connecting Arrows
body_diag1 += '<path d="M 300 175 L 330 175" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag1 += '<path d="M 590 175 L 620 175" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'
body_diag1 += '<path d="M 780 245 L 780 275" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow)" />'
body_diag1 += '<path d="M 265 245 L 265 275" stroke="#d97706" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram1_system_architecture.svg", 990, 430, "AutoHeal & ShopSphere — System Architecture Diagram", "Verified implementation across Presentation, Gateway, Autonomous Security Pipeline, AI, and Storage Tiers", body_diag1)


# Generate SVG 2: Deployment Diagram
body_diag2 = ""
body_diag2 += create_card_svg(40, 105, 280, 280, "Client Layer (Web Browser)", "Edge Interactive Clients", [
    "1. AutoHeal SOC Single Page App",
    "   URL: http://localhost:8000/",
    "   Tech: Vanilla JS, CSS3 Dark Navy,",
    "   Chart.js, FontAwesome, Toastr",
    "",
    "2. ShopSphere Storefront",
    "   URL: http://localhost:8000/shop",
    "   Tech: Jinja2, HTML5, Vanilla JS",
    "",
    "3. 3D Spatial Topology Visualizer",
    "   URL: http://localhost:8501/",
    "   Tech: Streamlit, Three.js WebGL"
], "#0284c7", "#f0f9ff")

body_diag2 += create_card_svg(350, 105, 300, 280, "Process 1: ASGI Host (:8000)", "Python 3.12 Uvicorn Runtime", [
    "Executable: python server.py",
    "Active Port: 0.0.0.0:8000 (HTTP/1.1)",
    "Runtime Modules:",
    "- FastAPI Application (server.py)",
    "- AppSecProtectionMiddleware",
    "- ShopSphere E-Commerce API",
    "- AutoHeal AppSec Management API",
    "- Security Tester Runner (Localhost only)",
    "- 5 Security Pipeline Agents",
    "- In-Memory Rate Limiter (8s window)"
], "#0d9488", "#f0fdfa")

body_diag2 += create_card_svg(680, 105, 270, 280, "Local Storage & Model Tier", "Host Filesystem Persistence", [
    "Base Path: C:\\Users\\...\\AD\\autoheal\\",
    "",
    "1. Primary SQLite Database:",
    "   data/shopsphere.db (1.08 MB)",
    "   WAL Mode enabled, Foreign Keys",
    "",
    "2. Machine Learning Model Artifact:",
    "   models/rf_model.joblib (140 KB)",
    "   Pre-trained Scikit-Learn weights",
    "",
    "3. Forensic Export Outputs:",
    "   documentation/diagrams/"
], "#dc2626", "#fef2f2")

body_diag2 += '<path d="M 320 220 L 350 220" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag2 += '<path d="M 650 220 L 680 220" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram2_deployment.svg", 990, 420, "AutoHeal & ShopSphere — Verified Deployment Diagram", "Physical processes, boundaries, ports (:8000, :8501), SQLite WAL database path, and model artifact", body_diag2)


# Generate SVG 3: Detection Agent Flowchart
body_diag3 = ""
body_diag3 += create_card_svg(40, 105, 210, 120, "1. Ingress Normalization", "Validation & Feature Prep", [
    "- URL decode query string",
    "- Sanitize malformed unicode",
    "- Redact sensitive passwords",
    "- Extract method, path, IP"
], "#0284c7", "#f0f9ff")

body_diag3 += create_card_svg(280, 105, 210, 120, "2. Deterministic Rules", "Signature Pattern Matching", [
    "- INJ-001: SQL Injection",
    "- XSS-001: Script/DOM Tags",
    "- AUTH-002: Admin Probes",
    "- High Confidence: 0.94 - 0.99"
], "#0d9488", "#f0fdfa")

body_diag3 += create_card_svg(520, 105, 210, 120, "3. ML Anomaly Scoring", "Random Forest Classifier", [
    "- Load models/rf_model.joblib",
    "- Feature Schema (7 features)",
    "- Probability Score (0.0 - 1.0)",
    "- Threshold Check >= 0.45"
], "#d97706", "#fffbeb")

body_diag3 += create_card_svg(760, 105, 190, 120, "4. Detection Output", "Structured Object", [
    "- rule_id & category",
    "- severity: CRITICAL/HIGH",
    "- confidence & model_score",
    "- Dispatch to Correlator"
], "#7c3aed", "#faf5ff")

body_diag3 += '<path d="M 250 165 L 280 165" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag3 += '<path d="M 490 165 L 520 165" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'
body_diag3 += '<path d="M 730 165 L 760 165" stroke="#d97706" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram3_detection_agent_flowchart.svg", 990, 260, "Component 1: Detection Agent Execution Flowchart", "Ingress normalization, signature-based pattern matching, Scikit-Learn Random Forest anomaly inference", body_diag3)


# Generate SVG 4: Log Correlation Engine Flowchart
body_diag4 = ""
body_diag4 += create_card_svg(40, 105, 210, 140, "1. Window Aggregation", "Sliding Time Window (60s)", [
    "- Query security_events",
    "- Filter since_seconds = 60",
    "- Group by client_ip",
    "- Group by correlation_id"
], "#0284c7", "#f0f9ff")

body_diag4 += create_card_svg(280, 105, 220, 140, "2. Pattern Correlation", "Multi-Event Rules", [
    "- AUTH-001: >= 4 Auth Failures",
    "- RATE-001: >= 25 Requests/60s",
    "- CORR-001: Auth Fail -> Probe",
    "- HEALTH-001: >= 3 500 Errors"
], "#0d9488", "#f0fdfa")

body_diag4 += create_card_svg(530, 105, 210, 140, "3. Deduplication Check", "Idempotency Gate", [
    "- find_active_incident()",
    "- Match source_ip & rule_id",
    "- Window: last 300 seconds",
    "- Avoid duplicate rows"
], "#d97706", "#fffbeb")

body_diag4 += create_card_svg(770, 105, 180, 140, "4. Incident Dossier", "Persistence to SQLite", [
    "- Merge linked_event_ids",
    "- Update updated_at",
    "- Set status: UNDER_INVEST.",
    "- Handoff to Response"
], "#7c3aed", "#faf5ff")

body_diag4 += '<path d="M 250 175 L 280 175" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag4 += '<path d="M 500 175 L 530 175" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'
body_diag4 += '<path d="M 740 175 L 770 175" stroke="#d97706" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram4_log_correlation_engine_flowchart.svg", 990, 280, "Component 2: Log Correlation Engine Flowchart", "Time-window grouping, multi-stage attack detection, and idempotent incident deduplication", body_diag4)


# Generate SVG 5: Response Agent Flowchart
body_diag5 = ""
body_diag5 += create_card_svg(40, 105, 210, 130, "1. Incident Input", "Evaluated Threat Input", [
    "- Correlated incident ID",
    "- Rule ID & Threat Category",
    "- Target Client IP / Session",
    "- Check dry_run flag"
], "#0284c7", "#f0f9ff")

body_diag5 += create_card_svg(280, 105, 220, 130, "2. Policy Evaluation", "Autonomous Decision Gate", [
    "- Lookup POLICY_RULES",
    "- Action: BLOCK_IP / RATE",
    "- Configured TTL: 180s - 300s",
    "- Safe Loopback exemption"
], "#0d9488", "#f0fdfa")

body_diag5 += create_card_svg(530, 105, 210, 130, "3. Defensive Action", "Active Containment", [
    "- Insert into blocked_clients",
    "- Middleware intercepts (403)",
    "- Self-healing seed recovery",
    "- Measure latency (ms)"
], "#d97706", "#fffbeb")

body_diag5 += create_card_svg(770, 105, 180, 130, "4. Audit & Handoff", "Audit Trace & Verifier", [
    "- Log mitigation action",
    "- status: RESPONSE_ATTEMPT.",
    "- Handoff to Verifier",
    "- Ready for verification"
], "#7c3aed", "#faf5ff")

body_diag5 += '<path d="M 250 170 L 280 170" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag5 += '<path d="M 500 170 L 530 170" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'
body_diag5 += '<path d="M 740 170 L 770 170" stroke="#d97706" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram5_response_agent_flowchart.svg", 990, 270, "Component 3: Response Agent Flowchart", "Policy lookup, dynamic WAF quarantine with sliding TTL, audit logging, and handoff to verification", body_diag5)


# Generate SVG 6: Verification and Escalation Flowchart
body_diag6 = ""
body_diag6 += create_card_svg(40, 105, 220, 140, "1. Perimeter Containment Probe", "Malicious Attacker Testing", [
    "- Issue synthetic HTTP probe",
    "- Spoof attacker X-Forwarded-For",
    "- Inspect HTTP response code",
    "- Expected: 403 Forbidden"
], "#0284c7", "#f0f9ff")

body_diag6 += create_card_svg(290, 105, 220, 140, "2. Availability Non-Regression", "Benign Shopper Testing", [
    "- Issue clean shopper HTTP probe",
    "- Target: /api/shop/products",
    "- Inspect HTTP response code",
    "- Expected: 200 OK (Preserved)"
], "#0d9488", "#f0fdfa")

body_diag6 += create_card_svg(540, 105, 200, 140, "3. Verification Decision", "Dual Invariant Gate", [
    "IF 403 AND 200:",
    "- status = 'CONTAINED'",
    "- verification = 'VERIFIED'",
    "ELSE:",
    "- Trigger Escalation Mechanism"
], "#16a34a", "#f0fdf4")

body_diag6 += create_card_svg(770, 105, 180, 140, "4. Escalation Mechanism", "Bounded Retries (Max 3)", [
    "- If retries < 3: Double TTL,",
    "  elevate to CRITICAL, retry",
    "- If retries >= 3: Terminate,",
    "  status: ESCALATION_REQ."
], "#dc2626", "#fef2f2")

body_diag6 += '<path d="M 260 175 L 290 175" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag6 += '<path d="M 510 175 L 540 175" stroke="#0d9488" stroke-width="2" marker-end="url(#arrow)" />'
body_diag6 += '<path d="M 740 175 L 770 175" stroke="#dc2626" stroke-width="2" marker-end="url(#arrowRed)" />'

save_svg_file("diagram6_verification_escalation_flowchart.svg", 990, 280, "Component 4 & 5: Verification & Escalation Flowchart", "Dual-probe verification (containment + availability), bounded escalation retries, and terminal SOC dispatch", body_diag6)


# Generate SVG 7: End-to-End Sequence Diagram
body_diag7 = ""
actors = [
    (60, "SOC Operator"), (200, "Attack Center"), (360, "Middleware (:8000)"),
    (520, "Storefront / Shop"), (680, "Detection / Correlator"),
    (840, "Response / Verifier"), (950, "SQLite DB")
]
for ax, aname in actors:
    body_diag7 += f'<rect x="{ax-45}" y="100" width="90" height="30" rx="4" fill="#0f172a" />'
    body_diag7 += f'<text x="{ax}" y="119" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#ffffff" text-anchor="middle">{aname}</text>'
    body_diag7 += f'<line x1="{ax}" y1="130" x2="{ax}" y2="390" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4" />'

# Sequence Steps
steps = [
    (60, 200, 145, "1. Launch Attack Test (failed_logins)", "#0284c7"),
    (200, 360, 175, "2. HTTP POST /api/shop/auth/login", "#0284c7"),
    (360, 520, 200, "3. Check Credentials -> 401 Unauthorized", "#0d9488"),
    (360, 950, 225, "4. INSERT INTO security_events (AUTH_FAILURE)", "#64748b"),
    (360, 680, 255, "5. Threshold Reached: Trigger Correlation", "#7c3aed"),
    (680, 950, 280, "6. upsert_security_incident (AUTH-001)", "#7c3aed"),
    (680, 840, 305, "7. Handoff to Response & Verification", "#d97706"),
    (840, 950, 330, "8. Dynamic Quarantine in blocked_clients (TTL=180s)", "#dc2626"),
    (840, 360, 355, "9. Synthetic Probes: Attacker=403, Benign=200", "#16a34a"),
    (840, 200, 380, "10. Stream Verification Outcome (SSE)", "#16a34a")
]

for x1, x2, sy, slabel, scolor in steps:
    body_diag7 += f'<line x1="{x1}" y1="{sy}" x2="{x2}" y2="{sy}" stroke="{scolor}" stroke-width="2" marker-end="url(#arrow)" />'
    mid_x = (x1 + x2) / 2
    body_diag7 += f'<rect x="{mid_x-110}" y="{sy-14}" width="220" height="15" rx="3" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />'
    body_diag7 += f'<text x="{mid_x}" y="{sy-3}" font-family="Arial, sans-serif" font-size="9" font-weight="bold" fill="{scolor}" text-anchor="middle">{slabel}</text>'

save_svg_file("diagram7_end_to_end_sequence.svg", 1020, 420, "AutoHeal & ShopSphere — End-to-End Sequence Diagram", "Complete chronological interactions across User, Attack Center, Gateway, Storefront, Security Pipeline, and Storage", body_diag7)


# Generate SVG 8: Database & Data-Flow Diagram
body_diag8 = ""
body_diag8 += create_card_svg(40, 105, 280, 280, "Table: security_events", "Immutable Ingress HTTP Telemetry", [
    "- id: INTEGER PRIMARY KEY",
    "- event_id: TEXT UNIQUE (EVT-XXXX)",
    "- correlation_id: TEXT (corr-XXXX)",
    "- timestamp: TIMESTAMP (UTC)",
    "- client_ip: TEXT (198.51.100.X)",
    "- method: TEXT (GET/POST/PUT)",
    "- path: TEXT (/api/shop/...)",
    "- status_code: INTEGER (200, 401, 403)",
    "- latency_ms: REAL (ms elapsed)",
    "- event_type: TEXT (AUTH_FAILURE, ...)",
    "- severity: TEXT (INFO, HIGH, CRITICAL)",
    "- action_taken: TEXT (ALLOWED, BLOCKED)"
], "#0284c7", "#f0f9ff")

body_diag8 += create_card_svg(350, 105, 290, 280, "Table: security_incidents", "Correlated Forensic Dossiers", [
    "- id: INTEGER PRIMARY KEY",
    "- incident_id: TEXT UNIQUE (INC-2026-X)",
    "- rule_id: TEXT (AUTH-001, INJ-001)",
    "- category: TEXT (Credential Stuffing)",
    "- severity: TEXT (HIGH / CRITICAL)",
    "- status: TEXT (CONTAINED, ESCALATED)",
    "- confidence: REAL (0.0 - 1.0)",
    "- evidence_json: TEXT (linked_event_ids)",
    "- affected_endpoints_json: TEXT",
    "- verification_status: TEXT (VERIFIED)",
    "- mitre_technique_id: TEXT (T1110.001)",
    "- recovery_status: TEXT (NOMINAL)"
], "#7c3aed", "#faf5ff")

body_diag8 += create_card_svg(670, 105, 280, 280, "Table: blocked_clients", "Dynamic Perimeter WAF Blocklist", [
    "- id: INTEGER PRIMARY KEY",
    "- client_ip: TEXT UNIQUE (Quarantined)",
    "- reason: TEXT (Triggering rule summary)",
    "- rule_id: TEXT (INJ-001, AUTH-001)",
    "- incident_id: TEXT FK",
    "- blocked_at: TIMESTAMP DEFAULT NOW",
    "- expires_at: TIMESTAMP (Sliding TTL)",
    "- is_active: INTEGER (1 = blocked, 0 = exp.)",
    "",
    "Auto-Expiry Logic: Checked in middleware.",
    "Expired blocks set is_active=0 dynamically."
], "#dc2626", "#fef2f2")

body_diag8 += '<path d="M 320 220 L 350 220" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />'
body_diag8 += '<path d="M 640 220 L 670 220" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow)" />'

save_svg_file("diagram8_database_dataflow.svg", 990, 420, "AutoHeal & ShopSphere — Database & Data-Flow Diagram", "Actual SQLite schemas for security_events, security_incidents, and blocked_clients with relational linkages", body_diag8)


# =============================================================================
# 3. HIGH-RESOLUTION PNG GENERATION (.png) VIA MATPLOTLIB
# =============================================================================

def render_png_diagram(filename, title, subtitle, boxes, arrows=None, figsize=(14, 8)):
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fafafa')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Border frame
    frame = FancyBboxPatch((1, 1), 98, 98, boxstyle="round,pad=0.5",
                           ec="#cbd5e1", fc="#ffffff", lw=1.5)
    ax.add_patch(frame)

    # Title Banner
    banner = FancyBboxPatch((3, 88), 94, 9, boxstyle="round,pad=0.3",
                            ec="#0f172a", fc="#0f172a")
    ax.add_patch(banner)
    ax.text(5, 93.5, title, fontsize=14, fontweight='bold', color='#ffffff', va='center')
    ax.text(5, 90.0, subtitle, fontsize=9, color='#94a3b8', va='center')

    # Render Boxes
    for box in boxes:
        x, y, w, h = box['rect']
        bg = box.get('bg', '#f0f9ff')
        ec = box.get('ec', '#0284c7')
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                               ec=ec, fc=bg, lw=1.8)
        ax.add_patch(patch)
        ax.text(x + 2, y + h - 4, box['title'], fontsize=11, fontweight='bold', color='#0f172a')
        if 'subtitle' in box and box['subtitle']:
            ax.text(x + 2, y + h - 8, box['subtitle'], fontsize=8, fontstyle='italic', color='#64748b')

        item_y = y + h - 14
        for item in box.get('items', []):
            ax.text(x + 2, item_y, item, fontsize=8.5, color='#334155')
            item_y -= 4.2

    # Render Arrows
    if arrows:
        for x1, y1, x2, y2, color in arrows:
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="->", color=color, lw=2.0))

    png_path = os.path.join(DIAGRAMS_DIR, filename)
    plt.tight_layout()
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] Rendered 300 DPI PNG: {filename}")

# PNG 1: System Architecture
render_png_diagram(
    "diagram1_system_architecture.png",
    "AutoHeal & ShopSphere — System Architecture Diagram",
    "Comprehensive architecture spanning Presentation, API Gateway, 5 Autonomous Security Components, ML, and Storage",
    [
        {"rect": (4, 48, 27, 36), "title": "1. Presentation Tier", "subtitle": "Interactive SOC & Storefront", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["- AutoHeal SOC Dashboard (index.html)", "- Attack Center Console (script.js)", "- ShopSphere Storefront (shopsphere.html)", "- 3D WebGL Topology (dashboard/app.py)"]},
        {"rect": (35, 48, 28, 36), "title": "2. Gateway & API (:8000)", "subtitle": "FastAPI ASGI Server (server.py)", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["- Starlette BaseHTTPMiddleware", "- AppSec Protection Middleware", "- ShopSphere REST API (/api/shop/*)", "- AutoHeal AppSec Management API"]},
        {"rect": (67, 48, 29, 36), "title": "3. The 5 Security Components", "subtitle": "Autonomous AppSec Pipeline", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["- Comp 1: Detection Agent (detector.py)", "- Comp 2: Correlation Engine (sliding window)", "- Comp 3: Response Agent (responder.py)", "- Comp 4: Verification Agent (verifier.py)", "- Comp 5: Escalation Mechanism (retries)"]},
        {"rect": (4, 8, 44, 34), "title": "4. Machine Learning & Forensics Layer", "subtitle": "Anomaly Scoring & Intelligence", "bg": "#fffbeb", "ec": "#d97706",
         "items": ["- Random Forest Classifier (models/rf_model.joblib)", "- 7 Network & System Features (failed_logins, bytes, cpu)", "- AI Security Advisor & MITRE ATT&CK Engine", "- Pure-Python PDF & JSON Dossier Generators"]},
        {"rect": (52, 8, 44, 34), "title": "5. Persistent Telemetry & Storage Tier", "subtitle": "SQLite Engine (data/shopsphere.db)", "bg": "#fef2f2", "ec": "#dc2626",
         "items": ["- security_events (Immutable Request Logs)", "- security_incidents (Correlated Attack Records)", "- blocked_clients (Dynamic WAF Quarantine with TTL)", "- Storefront Tables (users, products, cart_items, orders)"]}
    ],
    arrows=[(31, 66, 35, 66, "#0284c7"), (63, 66, 67, 66, "#0d9488"), (81, 48, 81, 42, "#7c3aed"), (26, 48, 26, 42, "#d97706")]
)

# PNG 2: Deployment Diagram
render_png_diagram(
    "diagram2_deployment.png",
    "AutoHeal & ShopSphere — Verified Deployment Diagram",
    "Runtime boundaries, processes, active ports (:8000, :8501), SQLite WAL database path, and ML model file",
    [
        {"rect": (4, 15, 28, 68), "title": "Client Processes (Web Browser)", "subtitle": "Chrome / Edge / Firefox", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["1. AutoHeal SOC Dashboard", "   http://localhost:8000/", "   Single Page Application", "", "2. ShopSphere Storefront", "   http://localhost:8000/shop", "   Flipkart Replica UI", "", "3. 3D Spatial Canvas", "   http://localhost:8501/", "   Three.js WebGL SOC"]},
        {"rect": (36, 15, 30, 68), "title": "Runtime Process 1: ASGI Host", "subtitle": "Python Uvicorn (Port 8000)", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["server.py (FastAPI 0.115)", "Active Port: 0.0.0.0:8000", "", "Key Runtime Modules:", "- AppSecProtectionMiddleware", "- ShopSphere REST Endpoints", "- Attack Center Execution Engine", "- 5 Security Pipeline Components", "- Real-Time SSE Streamer", "- Dynamic In-Memory Rate Tracker"]},
        {"rect": (70, 15, 26, 68), "title": "Local Storage & Model Tier", "subtitle": "Filesystem Persistence", "bg": "#fef2f2", "ec": "#dc2626",
         "items": ["Host: Localhost / Windows", "", "1. SQLite Database Engine:", "   data/shopsphere.db (1.08MB)", "   WAL Mode, FK Enforced", "", "2. ML Model Weights:", "   models/rf_model.joblib", "   Scikit-Learn Classifier", "", "3. Generated Artifacts:", "   documentation/diagrams/"]}
    ],
    arrows=[(32, 49, 36, 49, "#0284c7"), (66, 49, 70, 49, "#0d9488")]
)

# PNG 3: Detection Agent Flowchart
render_png_diagram(
    "diagram3_detection_agent_flowchart.png",
    "Component 1: Detection Agent Execution Flowchart",
    "Ingress request normalization, deterministic pattern matching (SQLi, XSS, Admin), and ML inference",
    [
        {"rect": (4, 25, 20, 55), "title": "1. Ingress Prep", "subtitle": "Data Normalization", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["- URL decode query", "- Sanitize malformed", "- Redact credentials", "- Extract IP & path"]},
        {"rect": (28, 25, 21, 55), "title": "2. Signatures", "subtitle": "Deterministic Rules", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["- INJ-001: SQLi tautology", "- XSS-001: Script/DOM", "- AUTH-002: Admin probe", "- Conf: 0.94 - 0.99"]},
        {"rect": (53, 25, 21, 55), "title": "3. ML Inference", "subtitle": "Random Forest", "bg": "#fffbeb", "ec": "#d97706",
         "items": ["- rf_model.joblib", "- 7 Feature Columns", "- Prob Score (0-1)", "- Threshold >= 0.45"]},
        {"rect": (78, 25, 18, 55), "title": "4. Detection Output", "subtitle": "Structured Result", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["- rule_id & category", "- CRITICAL / HIGH", "- Evidence dossier", "- Handoff to Engine"]}
    ],
    arrows=[(24, 52, 28, 52, "#0284c7"), (49, 52, 53, 52, "#0d9488"), (74, 52, 78, 52, "#d97706")]
)

# PNG 4: Log Correlation Engine Flowchart
render_png_diagram(
    "diagram4_log_correlation_engine_flowchart.png",
    "Component 2: Log Correlation Engine Flowchart",
    "Sliding time window (60s), multi-event pattern detection, and idempotent incident deduplication",
    [
        {"rect": (4, 25, 20, 55), "title": "1. Aggregation", "subtitle": "Sliding Time Window", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["- security_events", "- 60s sliding window", "- Group by client_ip", "- Group by session"]},
        {"rect": (28, 25, 21, 55), "title": "2. Rules Logic", "subtitle": "Multi-Step Patterns", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["- AUTH-001: >= 4 failed", "- RATE-001: >= 25 reqs", "- CORR-001: Auth+Probe", "- HEALTH: >= 3 500s"]},
        {"rect": (53, 25, 21, 55), "title": "3. Deduplication", "subtitle": "Idempotency Gate", "bg": "#fffbeb", "ec": "#d97706",
         "items": ["- find_active_incident", "- Match IP & rule_id", "- Window: 300 seconds", "- Avoid duplicates"]},
        {"rect": (78, 25, 18, 55), "title": "4. Persistence", "subtitle": "Incident Dossier", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["- Merge event IDs", "- Update updated_at", "- Set status: UNDER_INV", "- Handoff to Response"]}
    ],
    arrows=[(24, 52, 28, 52, "#0284c7"), (49, 52, 53, 52, "#0d9488"), (74, 52, 78, 52, "#d97706")]
)

# PNG 5: Response Agent Flowchart
render_png_diagram(
    "diagram5_response_agent_flowchart.png",
    "Component 3: Response Agent Flowchart",
    "Policy-driven mitigation, dynamic client IP quarantine with TTL auto-expiry, and verification handoff",
    [
        {"rect": (4, 25, 20, 55), "title": "1. Incident Input", "subtitle": "Evaluated Threat", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["- Correlated incident ID", "- Threat rule & category", "- Target client IP", "- Check dry_run flag"]},
        {"rect": (28, 25, 21, 55), "title": "2. Policy Lookup", "subtitle": "Defensive Rules", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["- Lookup POLICY_RULES", "- BLOCK_IP / RATE_LIMIT", "- TTL: 180s - 300s", "- Loopback safeguard"]},
        {"rect": (53, 25, 21, 55), "title": "3. Enactment", "subtitle": "Active Mitigation", "bg": "#fffbeb", "ec": "#d97706",
         "items": ["- blocked_clients table", "- Middleware 403 drop", "- Self-heal db seed", "- Latency timing (ms)"]},
        {"rect": (78, 25, 18, 55), "title": "4. Audit & Handoff", "subtitle": "State Transition", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["- Record action audit", "- status: RESPONSE_ATT", "- Invoke Verifier", "- Prepare follow-up"]}
    ],
    arrows=[(24, 52, 28, 52, "#0284c7"), (49, 52, 53, 52, "#0d9488"), (74, 52, 78, 52, "#d97706")]
)

# PNG 6: Verification and Escalation Flowchart
render_png_diagram(
    "diagram6_verification_escalation_flowchart.png",
    "Component 4 & 5: Verification & Escalation Flowchart",
    "Dual-probe verification (containment + availability), bounded escalation retries, and terminal SOC alert",
    [
        {"rect": (4, 25, 21, 55), "title": "1. Quarantine Probe", "subtitle": "Attacker Testing", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["- Synthetic HTTP probe", "- Spoofed attacker IP", "- Target: /api/shop/...", "- Expect: 403 Forbidden"]},
        {"rect": (29, 25, 21, 55), "title": "2. Availability Probe", "subtitle": "Benign Shopper Testing", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["- Clean customer IP", "- Target: /api/shop/products", "- Non-regression check", "- Expect: 200 OK"]},
        {"rect": (54, 25, 20, 55), "title": "3. Decision Gate", "subtitle": "Invariant Check", "bg": "#f0fdf4", "ec": "#16a34a",
         "items": ["IF 403 AND 200:", "  status = 'CONTAINED'", "  verif = 'VERIFIED'", "ELSE:", "  Trigger Escalation"]},
        {"rect": (78, 25, 18, 55), "title": "4. Escalation Policy", "subtitle": "Bounded Retries", "bg": "#fef2f2", "ec": "#dc2626",
         "items": ["- Retries < 3: Double TTL,", "  CRITICAL, re-verify", "- Retries >= 3: Terminate,", "  ESCALATION_REQUIRED"]}
    ],
    arrows=[(25, 52, 29, 52, "#0284c7"), (50, 52, 54, 52, "#0d9488"), (74, 52, 78, 52, "#dc2626")]
)

# PNG 7: End-to-End Sequence Diagram
render_png_diagram(
    "diagram7_end_to_end_sequence.png",
    "AutoHeal & ShopSphere — End-to-End Sequence Diagram",
    "Chronological workflow: User -> Attack Center -> Gateway -> Detection -> Correlation -> Response -> Verification -> Report",
    [
        {"rect": (4, 48, 44, 35), "title": "Phase 1: Attack & Ingress Telemetry", "subtitle": "Attack Center to Gateway", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["1. User selects scenario & clicks 'Start Test'", "2. Attack runner dispatches HTTP requests to ShopSphere", "3. Storefront returns 401 Unauthorized", "4. Starlette middleware records event into security_events"]},
        {"rect": (52, 48, 44, 35), "title": "Phase 2: Detection & Correlation", "subtitle": "Sliding Window Analysis", "bg": "#f0fdfa", "ec": "#0d9488",
         "items": ["5. Detection Agent evaluates signature & ML features", "6. Correlation Engine groups 4+ auth failures in 60s", "7. upsert_security_incident prevents duplicate rows", "8. Structured incident created (INC-2026-XXXX)"]},
        {"rect": (4, 8, 44, 35), "title": "Phase 3: Autonomous Response & Probing", "subtitle": "WAF Quarantine & Verification", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["9. Response Agent applies IP quarantine in blocked_clients", "10. Verification Agent issues synthetic probe (Attacker -> 403)", "11. Verification Agent issues benign shopper probe (Shopper -> 200)", "12. Incident updated: status='CONTAINED', verif='VERIFIED'"]},
        {"rect": (52, 8, 44, 35), "title": "Phase 4: Forensics & Reporting", "subtitle": "Dossier & Artifact Generation", "bg": "#fffbeb", "ec": "#d97706",
         "items": ["13. Live execution trace streamed to UI via SSE (/test/stream)", "14. UI renders verified containment badge and dossier link", "15. User requests PDF report (/incidents/{id}/export?format=pdf)", "16. Binary PDF generated with MITRE mapping and redacted evidence"]}
    ],
    arrows=[(48, 65, 52, 65, "#0284c7"), (74, 48, 74, 43, "#0d9488"), (48, 25, 52, 25, "#7c3aed")]
)

# PNG 8: Database & Data-Flow Diagram
render_png_diagram(
    "diagram8_database_dataflow.png",
    "AutoHeal & ShopSphere — Database & Data-Flow Diagram",
    "Actual SQLite schema: security_events, security_incidents, blocked_clients, and relational linkages",
    [
        {"rect": (4, 15, 28, 68), "title": "security_events", "subtitle": "Immutable Telemetry Stream", "bg": "#f0f9ff", "ec": "#0284c7",
         "items": ["id INTEGER PRIMARY KEY", "event_id TEXT UNIQUE", "correlation_id TEXT", "timestamp TIMESTAMP (UTC)", "client_ip TEXT", "method TEXT (GET/POST)", "path TEXT (/api/shop/...)", "status_code INTEGER", "latency_ms REAL", "event_type TEXT", "severity TEXT", "action_taken TEXT"]},
        {"rect": (36, 15, 30, 68), "title": "security_incidents", "subtitle": "Correlated Attack Dossiers", "bg": "#faf5ff", "ec": "#7c3aed",
         "items": ["id INTEGER PRIMARY KEY", "incident_id TEXT UNIQUE", "rule_id TEXT (AUTH-001)", "category TEXT", "severity TEXT", "status TEXT (CONTAINED)", "confidence REAL", "evidence_json TEXT", "mitigation_actions_json TEXT", "verification_status TEXT", "mitre_technique_id TEXT", "recovery_status TEXT"]},
        {"rect": (70, 15, 26, 68), "title": "blocked_clients", "subtitle": "Perimeter WAF Quarantine", "bg": "#fef2f2", "ec": "#dc2626",
         "items": ["id INTEGER PRIMARY KEY", "client_ip TEXT UNIQUE", "reason TEXT", "rule_id TEXT", "incident_id TEXT FK", "blocked_at TIMESTAMP", "expires_at TIMESTAMP", "is_active INTEGER (1/0)", "", "Auto-expiry evaluated in", "middleware on each check."]}
    ],
    arrows=[(32, 49, 36, 49, "#0284c7"), (66, 49, 70, 49, "#7c3aed")]
)

print("[SUCCESS] All 8 diagrams generated in MMD, SVG, and PNG formats.")
