# AutoHeal & ShopSphere Architecture, Deployment, and Security Diagrams
## Supporting Notes and Academic Documentation Reference

This document provides academic captions, architectural explanations, source code cross-references, and verified runtime details for the 8 system and component diagrams generated for the **AutoHeal Autonomous Application Security, Self-Healing & Forensics Platform** and the **ShopSphere E-Commerce Application**.

All diagrams have been generated directly from the verified codebase in three formats:
- **High-Resolution PNG (300 DPI)**: Tailored with a clean white/light background and high contrast for direct insertion into academic reports and IEEE/ACM style publications.
- **Scalable Vector Graphics (SVG)**: Lossless vector representation for web dashboards, scalable posters, or vector typesetting.
- **Editable Mermaid Source (`.mmd`)**: Standard Mermaid DSL files for ongoing maintenance, interactive rendering, and text-based version control.

Directory location: `documentation/diagrams/`

---

## Diagram 1: System Architecture Diagram

- **PNG File**: `documentation/diagrams/diagram1_system_architecture.png`
- **SVG File**: `documentation/diagrams/diagram1_system_architecture.svg`
- **Mermaid Source**: `documentation/diagrams/diagram1_system_architecture.mmd`

### Academic Caption
> **Figure 1**: *High-Level System Architecture of AutoHeal Integrated with the ShopSphere E-Commerce Platform, depicting Client Interface Layers, ASGI Application Core, Telemetry Pipeline, Autonomous Defense Agents, and Persistent SQLite Storage.*

### Architectural Explanation & Component Boundaries
The system implements a defense-in-depth architecture partitioned into four distinct functional tiers:
1. **Client / Presentation Layer**:
   - **AutoHeal SOC Web Console** (`web/index.html`, `web/static/js/script.js`): Single Page Application (SPA) providing real-time telemetry streaming, incident management, attack campaign triggering, forensic report generation, and defense posture metrics.
   - **ShopSphere Storefront** (`web/templates/shop.html`, `web/static/js/shop.js`): A modern Flipkart-inspired consumer e-commerce storefront supporting product search, catalog browsing, cart operations, user authentication, and multi-step simulated checkout.
   - **Streamlit 3D SOC Dashboard** (`dashboard/app.py`): WebGL/Three.js spatial network visualization displaying active threat nodes and telemetry metrics on port 8501.
2. **ShopSphere Core Application Layer (FastAPI on Port 8000)**:
   - Built on FastAPI (`src/api/app.py`), routing traffic to Storefront endpoints (`/shop`), Shop REST APIs (`/api/shop/*`), and Security Monitoring APIs (`/api/security/*`).
   - Protected by the non-blocking `AppSecProtectionMiddleware` (`src/appsec/middleware.py`) which inspects HTTP requests, queries the active blacklist, logs raw telemetry events, and coordinates with the detector.
3. **AutoHeal Autonomous Defense Agents**:
   - **Attack Center** (`src/appsec/live_testing.py`): Controlled security testing runner enforcing bounded payloads, local target restrictions, and real HTTP execution against ShopSphere.
   - **Detection Agent** (`src/appsec/detector.py`): Real-time analysis combining deterministic regex rules (`INJ-001`, `XSS-001`, `AUTH-002`) and pre-trained Random Forest ML inference (`models/rf_model.joblib`).
   - **Log Correlation Engine** (`src/appsec/correlation_engine.py`): Sliding-window (60s) temporal and IP/session correlation, identifying brute force attacks (`AUTH-001`), traffic anomalies (`RATE-001`), multi-stage reconnaissance (`CORR-001`), and server errors (`HEALTH-001`).
   - **Response Agent** (`src/appsec/responder.py`): Autonomous mitigation subsystem implementing policy-driven IP bans, rate limits, and service remediation with dual-tier verifier handoff.
   - **Verification Agent & Escalator** (`src/appsec/verifier.py`): Closed-loop verification executing synthetic loopback probes (attacker verification + clean shopper sanity check) and bounded retry escalation (max 3 retries with cooldown and exponential TTL backoff).
   - **Forensics & Reporting Engine** (`src/reporting/report_generator.py`): Evidence aggregation pipeline generating tamper-evident JSON and publication-ready PDF forensic incident dossiers.
4. **Data Persistence Tier (SQLite in WAL Mode)**:
   - Primary database located at `data/shopsphere.db`. Contains relational schemas for e-commerce entities (`users`, `products`, `orders`, `cart_items`) alongside cybersecurity telemetry (`security_events`, `security_incidents`, `blocked_clients`, `vulnerabilities`).

### Source Code References
- Storefront & REST API: `src/api/app.py`, `src/api/routes.py`
- AppSec API Endpoints: `src/appsec/api.py`
- Protection Middleware: `src/appsec/middleware.py`
- Security Agents: `src/appsec/detector.py`, `src/appsec/correlation_engine.py`, `src/appsec/responder.py`, `src/appsec/verifier.py`
- Attack Runner: `src/appsec/live_testing.py`
- Database Models & DAO: `src/appsec/models.py`, `src/database/models.py`

---

## Diagram 2: Deployment Diagram

- **PNG File**: `documentation/diagrams/diagram2_deployment.png`
- **SVG File**: `documentation/diagrams/diagram2_deployment.svg`
- **Mermaid Source**: `documentation/diagrams/diagram2_deployment.mmd`

### Academic Caption
> **Figure 2**: *Physical Process and Local Deployment Topology of AutoHeal and ShopSphere, illustrating runtime process boundaries, network port allocations, inter-process communication, and filesystem assets.*

### Architectural Explanation & Verified Runtime Specifications
All system components execute deterministically on the local host environment without external cloud dependencies:
1. **ShopSphere & AutoHeal Primary ASGI Node (`Uvicorn / FastAPI`)**:
   - **Port**: `8000` (`http://localhost:8000`)
   - **Process**: Python 3.12 executing `uvicorn src.api.app:app --host 0.0.0.0 --port 8000`
   - **Static & Template Delivery**: Serves AutoHeal SOC UI from `web/` and `web/static/`, and ShopSphere storefront from `web/templates/shop.html`.
   - **API Boundaries**: Hosts both e-commerce endpoints (`/api/shop/*`) and cybersecurity orchestration endpoints (`/api/security/*`).
   - **Middleware Injection**: Hosts `AppSecProtectionMiddleware` executing on every request to block blacklisted IPs and log telemetry.
2. **AutoHeal 3D SOC Center Node (`Streamlit`)**:
   - **Port**: `8501` (`http://localhost:8501`)
   - **Process**: Python 3.12 executing `streamlit run dashboard/app.py --server.port 8501`
   - **Features**: Real-time 3D Three.js canvas visualizing spatial threat topology, incident counts, and live system metrics.
3. **Database & Storage Boundary**:
   - **File**: `data/shopsphere.db` (SQLite 3 with `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL`).
   - Accessible concurrently by both ASGI worker threads and background analyzer processes.
4. **Machine Learning Model Artifact**:
   - **File**: `models/rf_model.joblib`
   - **Architecture**: Scikit-Learn `RandomForestClassifier` trained on 7 network telemetry features (`bytes_sent`, `bytes_received`, `connections`, `failed_logins`, `dns_requests`, `cpu_usage`, `mem_usage`).
   - Loaded into memory by `src/detection/model.py` and evaluated via `src/appsec/detector.py`.

### Source Code References
- Application Entry Point: `src/api/app.py:L1-L120`
- Streamlit SOC Entry Point: `dashboard/app.py:L1-L80`
- Database Engine: `src/database/session.py:L1-L40`, `src/appsec/models.py:L1-L60`
- Model Loader: `src/detection/model.py:L1-L90`

---

## Diagram 3: Detection Agent Flowchart

- **PNG File**: `documentation/diagrams/diagram3_detection_agent_flowchart.png`
- **SVG File**: `documentation/diagrams/diagram3_detection_agent_flowchart.svg`
- **Mermaid Source**: `documentation/diagrams/diagram3_detection_agent_flowchart.mmd`

### Academic Caption
> **Figure 3**: *Detection Agent Execution Pipeline, showing raw event normalization, deterministic signature evaluation, Random Forest ML inference, risk score calculation, and structured detection output generation.*

### Architectural Explanation & Detection Logic
The Detection Agent (`src/appsec/detector.py`) implements a hybrid signature-and-anomaly detection algorithm:
1. **Ingestion & Normalization**:
   - Ingests raw HTTP telemetry records from the `security_events` table or live middleware stream.
   - Cleans and normalizes URL paths, request headers, query strings, and payloads (URL decoding, whitespace normalization, case-insensitive mapping).
2. **Deterministic Rule Engine (Layer 1)**:
   - **SQL Injection (`INJ-001`)**: Evaluates payload against high-precision SQLi token sequences (e.g., `' OR '1'='1`, `UNION SELECT`, `--`, `SLEEP()`).
   - **Cross-Site Scripting (`XSS-001`)**: Evaluates payload against `<script>`, `onerror=`, `javascript:`, and HTML injection vectors.
   - **Administrative Path Traversal / Probe (`AUTH-002`)**: Detects unauthorized access attempts targeting restricted endpoints (`/admin`, `/api/admin/*`, `/actuator`).
3. **Machine Learning Anomaly Engine (Layer 2)**:
   - Ingests quantitative telemetry metrics (`bytes_sent`, `bytes_received`, `failed_logins`, `connections`, `cpu_usage`, `mem_usage`).
   - Evaluates features against `models/rf_model.joblib`.
   - Produces an anomaly probability classification (`model_score`).
4. **Composite Scoring & Structured Output**:
   - Computes overall severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and numeric risk score ($0.0 - 1.0$).
   - Returns a structured `DetectionResult` object containing rule identifier, human-readable rationale, risk score, model confidence, and linked source event IDs.

### Source Code References
- Detection Agent: `src/appsec/detector.py:AppSecDetector`
- Detection Rules & Signatures: `src/appsec/detector.py:L28-L95`
- ML Integration: `src/detection/model.py:DetectionModel`, `src/appsec/detector.py:L115-L148`

---

## Diagram 4: Log Correlation Engine Flowchart

- **PNG File**: `documentation/diagrams/diagram4_log_correlation_engine_flowchart.png`
- **SVG File**: `documentation/diagrams/diagram4_log_correlation_engine_flowchart.svg`
- **Mermaid Source**: `documentation/diagrams/diagram4_log_correlation_engine_flowchart.mmd`

### Academic Caption
> **Figure 4**: *Log Correlation Engine Multi-Event Aggregation Flowchart, demonstrating 60-second sliding-window grouping, temporal correlation, multi-stage attack detection, and idempotent incident deduplication.*

### Architectural Explanation & Correlation Logic
The Log Correlation Engine (`src/appsec/correlation_engine.py`) transforms isolated security events into contextualized, actionable incidents:
1. **Sliding Time-Window Extraction**:
   - Queries unanalyzed security events from `data/shopsphere.db` within a configurable sliding temporal window (default $\Delta t = 60\text{ seconds}$).
2. **Grouping by Correlation Keys**:
   - Groups incoming events by IP address (`source_ip`), authenticated user/session (`user_id`), and targeted resource (`endpoint_path`).
3. **Correlation Rule Evaluation**:
   - **Brute Force Authentication (`AUTH-001`)**: Aggregates failed login attempts (`POST /api/shop/auth/login` with HTTP 401). Triggers when $\ge 4$ failures occur within the 60-second window.
   - **Rate Anomaly / Volumetric Flood (`RATE-001`)**: Aggregates total request velocity across endpoints. Triggers when $\ge 25$ requests occur from a single source within 60 seconds.
   - **Multi-Stage Kill Chain Attack (`CORR-001`)**: Correlates authentication failures immediately followed by administrative endpoint probes (`/admin`, `/api/admin/*`) from the same source IP.
   - **Application Error Burst (`HEALTH-001`)**: Identifies $\ge 3$ consecutive HTTP 500 internal server errors, signaling potential exploit-induced backend instability.
4. **Idempotent Persistence & Deduplication**:
   - Before inserting a new incident, executes `find_active_incident(source_ip, rule_id, window_seconds=300)`.
   - If an active incident exists for the source IP and rule within 5 minutes, updates the existing record with linked event IDs, refreshed timestamps, and merged evidence.
   - If no active incident exists, inserts a new record with status `UNDER_INVESTIGATION` and dispatches it to the Response Agent.

### Source Code References
- Correlation Engine: `src/appsec/correlation_engine.py:AppSecCorrelationEngine`
- Correlation Rules: `src/appsec/correlation_engine.py:L35-L165`
- Idempotent DAO: `src/appsec/models.py:find_active_incident`, `src/appsec/models.py:upsert_security_incident`

---

## Diagram 5: Response Agent Flowchart

- **PNG File**: `documentation/diagrams/diagram5_response_agent_flowchart.png`
- **SVG File**: `documentation/diagrams/diagram5_response_agent_flowchart.svg`
- **Mermaid Source**: `documentation/diagrams/diagram5_response_agent_flowchart.mmd`

### Academic Caption
> **Figure 5**: *Response Agent Autonomous Mitigation Workflow, detailing policy qualification, defensive action execution, rate-limiting, temporary IP blocking, audit trail logging, and verifier dispatch.*

### Architectural Explanation & Defense Policies
The Response Agent (`src/appsec/responder.py`) executes automated defensive countermeasures against verified incidents:
1. **Policy Qualification**:
   - Analyzes incident classification, severity, and confidence.
   - Ensures benign traffic or low-confidence anomalies are not subjected to destructive mitigation.
2. **Defensive Action Selection**:
   - **Temporary IP Block (`BLOCK_IP`)**:
     - Applied to `CRITICAL` and `HIGH` severity incidents (e.g., Brute Force `AUTH-001`, SQL Injection `INJ-001`, Multi-Stage Attack `CORR-001`).
     - Inserts a record into `blocked_clients` in `data/shopsphere.db` with client IP, reason, incident ID reference, and temporary TTL (default 120 seconds).
     - Instantly enforced on subsequent requests by `AppSecProtectionMiddleware`, returning HTTP 403 Forbidden with `{"error": "Access denied by AutoHeal Security Engine"}`.
   - **Rate Limiting (`RATE_LIMIT`)**:
     - Applied to `MEDIUM` severity or volumetric anomalies (`RATE-001`).
     - Enforces throttling on the affected client IP.
   - **Service Recovery (`RECOVER_SERVICE`)**:
     - Applied to server instability incidents (`HEALTH-001`).
     - Triggers automated cache flushes and connection pool resets.
3. **Audit Logging & Incident State Transition**:
   - Updates `security_incidents` status to `RESPONSE_ATTEMPTED`.
   - Appends detailed mitigation metadata (action type, parameters, execution timestamp, operator) to incident audit log.
4. **Handoff to Verification**:
   - Dispatches incident directly to the Verification Agent (`src/appsec/verifier.py`) for closed-loop containment testing.

### Source Code References
- Response Agent: `src/appsec/responder.py:AppSecResponder`
- Response Policies: `src/appsec/responder.py:L32-L115`
- Middleware Enforcement: `src/appsec/middleware.py:L40-L75`
- Blocklist Storage: `src/appsec/models.py:record_blocked_client`, `src/appsec/models.py:is_ip_blocked`

---

## Diagram 6: Verification and Escalation Flowchart

- **PNG File**: `documentation/diagrams/diagram6_verification_escalation_flowchart.png`
- **SVG File**: `documentation/diagrams/diagram6_verification_escalation_flowchart.svg`
- **Mermaid Source**: `documentation/diagrams/diagram6_verification_escalation_flowchart.mmd`

### Academic Caption
> **Figure 6**: *Verification Agent and Escalation Subsystem Flowchart, illustrating dual synthetic loopback probes, containment validation, bounded retry escalation, and definitive resolution states.*

### Architectural Explanation & Bounded Loopback Assurance
The Verification Agent and Escalation Subsystem (`src/appsec/verifier.py`) prevents false-positive resolutions and runaway mitigation loops:
1. **Dual Synthetic Loopback Probes**:
   - **Probe 1 (Attacker Verification)**: Sends a synthetic loopback HTTP request using the attacker's client IP. Verifies that the endpoint actively rejects the request with HTTP 403 Forbidden and the AutoHeal block header.
   - **Probe 2 (Sanity Check - Legitimate Shopper)**: Sends a concurrent synthetic request to the same endpoint from a known benign IP (`127.0.0.99`). Confirms the endpoint returns HTTP 200 OK, verifying legitimate e-commerce users are not locked out.
2. **Containment Evaluation**:
   - **Case A: Both Probes Satisfied (Success)**:
     - The threat is strictly contained without collateral disruption.
     - Incident status transitions to `CONTAINMENT_VERIFIED` (or `CONTAINED`).
     - Verification status marked as `VERIFIED_CONTAINED`.
     - Evidence and verification timestamp recorded in SQLite.
   - **Case B: Attacker Still Permitted or Legitimate Users Blocked (Failure)**:
     - Mitigation failed to contain threat or caused collateral damage.
     - Verification status marked as `VERIFICATION_FAILED`.
3. **Bounded Escalation Mechanism**:
   - Reads current retry count $R$ from incident metadata.
   - **If $R < 3$ (Retry Allowed)**:
     - Increments retry count ($R \leftarrow R + 1$).
     - Imposes a mandatory 2.0-second cooldown period.
     - Doubles block TTL (exponential backoff: $120\text{s} \times 2^R$).
     - Re-executes `ResponseAgent.apply_response()`.
     - Incident status reverts to `RESPONSE_ATTEMPTED` for another verification cycle.
   - **If $R \ge 3$ (Escalation Ceiling Reached)**:
     - Breaks loop to prevent infinite execution.
     - Flags incident with status `ESCALATION_REQUIRED`.
     - Marks verification status as `ESCALATED_UNRESOLVED`.
     - Notifies SOC operators and preserves incident open for manual forensic intervention.

### Source Code References
- Verification Agent: `src/appsec/verifier.py:AppSecVerifier`
- Dual Probe Logic: `src/appsec/verifier.py:L35-L120`
- Escalation Policy: `src/appsec/verifier.py:L125-L178`
- Verification API Endpoint: `src/appsec/api.py:verify_incident_endpoint`

---

## Diagram 7: End-to-End Sequence Diagram

- **PNG File**: `documentation/diagrams/diagram7_end_to_end_sequence.png`
- **SVG File**: `documentation/diagrams/diagram7_end_to_end_sequence.svg`
- **Mermaid Source**: `documentation/diagrams/diagram7_end_to_end_sequence.mmd`

### Academic Caption
> **Figure 7**: *Chronological Sequence Diagram of the Complete Autonomous Security Lifecycle, tracing an Attack Launch, HTTP Ingestion, Telemetry Logging, Detection, Correlation, Mitigation, Dual Verification, and Forensic Report Generation.*

### Architectural Explanation & Chronological Interaction Sequence
This sequence diagram depicts the end-to-end execution flow of a live attack demonstration:
1. **Attack Triggering**:
   - SOC Analyst opens Attack Center (`web/index.html`) and selects a scenario (e.g., Brute Force Login, 6 bounded attempts against `http://localhost:8000/api/shop/auth/login`).
   - Analyst clicks **Launch Attack**.
   - Front-end invokes `POST /api/security/test/run` on the Attack Runner (`src/appsec/live_testing.py`).
2. **HTTP Request Execution**:
   - Attack Runner transmits bounded HTTP requests with custom headers (`X-Test-Client-IP: 198.51.100.55`) to ShopSphere REST API (`src/api/app.py`).
3. **Telemetry Ingestion & Storage**:
   - `AppSecProtectionMiddleware` intercepts each request, logs raw telemetry (timestamp, method, URI, status, client IP, user agent) to the `security_events` table in `data/shopsphere.db`.
   - Returns actual HTTP response (e.g., 401 Unauthorized) to the Attack Runner.
4. **Detection & Correlation**:
   - Detection Agent analyzes events, flagging signature violations and ML anomalies.
   - Log Correlation Engine aggregates events within the 60-second sliding window, detecting rule `AUTH-001` ($\ge 4$ failures).
   - Idempotent upsert creates or updates Incident `INC-xxxx` with status `UNDER_INVESTIGATION`.
5. **Autonomous Response**:
   - Response Agent executes `BLOCK_IP` policy, inserting IP `198.51.100.55` into `blocked_clients` with a 120-second TTL.
   - Status transitions to `RESPONSE_ATTEMPTED`.
6. **Closed-Loop Verification**:
   - Verification Agent executes synthetic probe 1 from `198.51.100.55`: Middleware rejects with HTTP 403 Forbidden.
   - Verification Agent executes synthetic probe 2 from `127.0.0.99`: Middleware permits with HTTP 200 OK.
   - Status transitions to `CONTAINMENT_VERIFIED` with `verification_status="VERIFIED_CONTAINED"`.
7. **Forensics & Reporting**:
   - Analyst clicks **Generate Report** in AutoHeal SOC UI (`POST /api/security/reports/generate/{incident_id}`).
   - Reporting Engine compiles full event timeline, detection rule, response log, and verification proof into JSON and PDF forensic dossiers.

### Source Code References
- Attack Runner: `src/appsec/live_testing.py`
- Protection Middleware: `src/appsec/middleware.py`
- Correlation & Upsert: `src/appsec/correlation_engine.py`, `src/appsec/models.py`
- Verification & API: `src/appsec/verifier.py`, `src/appsec/api.py`
- Reporting: `src/reporting/report_generator.py`

---

## Diagram 8: Database and Data-Flow Diagram

- **PNG File**: `documentation/diagrams/diagram8_database_dataflow.png`
- **SVG File**: `documentation/diagrams/diagram8_database_dataflow.svg`
- **Mermaid Source**: `documentation/diagrams/diagram8_database_dataflow.mmd`

### Academic Caption
> **Figure 8**: *Entity Relationship and Data-Flow Architecture of `data/shopsphere.db`, illustrating the dual-domain schema connecting E-Commerce Business Entities with Autonomous Cyber Defense Telemetry.*

### Architectural Explanation & Verified Schema Architecture
The database layer (`data/shopsphere.db`) manages two interconnected domains in a unified SQLite repository configured with Write-Ahead Logging (WAL):

#### 1. E-Commerce Domain Tables
- **`users`**:
  - `id` (INTEGER, PK), `username` (VARCHAR), `email` (VARCHAR, UNIQUE), `password_hash` (VARCHAR), `role` (VARCHAR: `admin` | `customer`), `created_at` (DATETIME).
- **`products`**:
  - `id` (INTEGER, PK), `name` (VARCHAR), `description` (TEXT), `price` (FLOAT), `category` (VARCHAR), `stock` (INTEGER), `image_url` (VARCHAR), `rating` (FLOAT).
- **`cart_items`**:
  - `id` (INTEGER, PK), `user_id` (INTEGER, FK $\to$ `users.id`), `product_id` (INTEGER, FK $\to$ `products.id`), `quantity` (INTEGER), `created_at` (DATETIME).
- **`orders` & `order_items`**:
  - `orders`: `id` (INTEGER, PK), `user_id` (INTEGER, FK $\to$ `users.id`), `total_amount` (FLOAT), `status` (VARCHAR), `created_at` (DATETIME).
  - `order_items`: `id` (INTEGER, PK), `order_id` (INTEGER, FK $\to$ `orders.id`), `product_id` (INTEGER, FK $\to$ `products.id`), `quantity` (INTEGER), `price_at_order` (FLOAT).

#### 2. AutoHeal Cyber Defense Telemetry Tables
- **`security_events`**:
  - `id` (INTEGER, PK), `timestamp` (DATETIME), `method` (VARCHAR), `path` (VARCHAR), `status_code` (INTEGER), `source_ip` (VARCHAR), `user_agent` (VARCHAR), `request_body` (TEXT), `response_body` (TEXT), `duration_ms` (FLOAT).
- **`security_incidents`**:
  - `id` (INTEGER, PK), `incident_id` (VARCHAR, UNIQUE, e.g. `INC-20261019-XXXX`), `rule_id` (VARCHAR), `classification` (VARCHAR), `severity` (VARCHAR: `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`), `status` (VARCHAR: `UNDER_INVESTIGATION` | `RESPONSE_ATTEMPTED` | `CONTAINMENT_VERIFIED` | `ESCALATION_REQUIRED`), `source_ip` (VARCHAR), `affected_endpoint` (VARCHAR), `first_seen` (DATETIME), `last_seen` (DATETIME), `linked_event_ids` (TEXT/JSON), `evidence` (TEXT/JSON), `verification_status` (VARCHAR), `retry_count` (INTEGER), `created_at` (DATETIME), `updated_at` (DATETIME).
- **`blocked_clients`**:
  - `id` (INTEGER, PK), `client_ip` (VARCHAR, INDEXED), `reason` (VARCHAR), `incident_id` (VARCHAR, FK $\to$ `security_incidents.incident_id`), `expires_at` (DATETIME), `created_at` (DATETIME).
- **`vulnerabilities`**:
  - `id` (INTEGER, PK), `cve_id` (VARCHAR), `component` (VARCHAR), `severity` (VARCHAR), `description` (TEXT), `remediation` (TEXT), `status` (VARCHAR).

### Source Code References
- AppSec Database Engine & Schemas: `src/appsec/models.py:init_appsec_db`
- E-Commerce Models & Schemas: `src/database/models.py`
- Database Session Factory: `src/database/session.py`

---

## Summary of Diagram Deliverables

| Diagram # | Title | Formats Available | Primary Source Code Reference |
|---|---|---|---|
| **1** | System Architecture Diagram | PNG, SVG, MMD | `src/api/app.py`, `src/appsec/` |
| **2** | Deployment Diagram | PNG, SVG, MMD | `src/api/app.py`, `dashboard/app.py`, `models/rf_model.joblib` |
| **3** | Detection Agent Flowchart | PNG, SVG, MMD | `src/appsec/detector.py`, `src/detection/model.py` |
| **4** | Log Correlation Engine Flowchart | PNG, SVG, MMD | `src/appsec/correlation_engine.py`, `src/appsec/models.py` |
| **5** | Response Agent Flowchart | PNG, SVG, MMD | `src/appsec/responder.py`, `src/appsec/middleware.py` |
| **6** | Verification and Escalation Flowchart | PNG, SVG, MMD | `src/appsec/verifier.py` |
| **7** | End-to-End Sequence Diagram | PNG, SVG, MMD | `src/appsec/live_testing.py`, `src/appsec/` |
| **8** | Database and Data-Flow Diagram | PNG, SVG, MMD | `src/appsec/models.py`, `src/database/models.py` |

All files in `documentation/diagrams/` are directly compatible with PDF authoring tools, LaTeX, Google Docs, Microsoft Word, and Markdown previewers.
