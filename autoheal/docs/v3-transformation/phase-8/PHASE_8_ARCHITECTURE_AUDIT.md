# AutoHeal Phase 8: Architecture & Data Model Audit
## 3D Threat Topology & AI SOC Copilot

**Audited Component:** AutoHeal v3.0 Enterprise SOC Platform  
**Target Application:** ShopSphere E-Commerce Application (`http://localhost:8000`)  
**Design Identity:** Obsidian Sentinel (`#090D14`, `#101722`, `#151F2C`, `#253344`, `#F1F5F9`, `#94A3B8`, `#22C55E`, `#38BDF8`, `#F59E0B`, `#EF4444`, `#A78BFA`)  
**Date:** 2026-11-01  
**Status:** Certified Architecture Audit  

---

## 1. Executive Summary
Phase 8 introduces two core enterprise capabilities to AutoHeal v3.0:
1. **Module A — 3D Threat Topology (`/threat-topology`)**: A real-time, interactive 3D spatial security environment that maps confirmed and inferred graph relationships between source IPs, target endpoints, affected assets, detection rules, security events, incidents, remediation operations, and verification probes.
2. **Module B — AI SOC Copilot (`/soc-copilot`)**: A grounded, hallucination-resistant security analyst assistant capable of investigating incidents, synthesizing evidence dossiers, explaining attack vectors, correlating anomalies, recommending playbooks, and drafting audit-ready incident reports.

This audit evaluates the existing frontend and backend foundations, verifies all underlying database schemas, establishes graph relationship models, reviews AI provider capabilities, and defines the technical roadmap.

---

## 2. Existing Data Sources Audit

AutoHeal maintains a unified SQLite database (`autoheal/data/shopsphere.db`) alongside in-memory state engines. Every entity visualized in the 3D topology and cited by the AI Copilot maps directly to these verified data sources:

| Data Source | Storage Location | Schema / Object Model | Key Records Available |
| :--- | :--- | :--- | :--- |
| **Security Telemetry Events** | SQLite: `security_events` | Table 9 (`event_id`, `correlation_id`, `client_ip`, `path`, `method`, `status_code`, `event_type`, `severity`, `details_json`, `action_taken`) | > 1,500 real events recorded across live test runs. |
| **Security Incidents** | SQLite: `security_incidents` | Table 10 (`incident_id`, `rule_id`, `title`, `category`, `severity`, `status`, `summary`, `evidence_json`, `affected_endpoints_json`, `source_ip`, `mitigation_actions_json`, `verification_status`) | Correlated incidents across injection, auth, XSS, DoS. |
| **Monitored Assets & Devices** | `NetworkSimulator` & `devices` | In-memory + SQLite (`id`, `role`, `ip`, `state`, `zone`, `risk_score`) | Edge Gateway, App Server, DB Server, Corporate Laptops. |
| **Application Services & Endpoints**| `ShopSphere` Architecture | FastAPI service routes (`UserService`, `ProductService`, `CartService`, `/api/shop/auth/*`, `/api/shop/products/*`) | Real endpoints exposed by ShopSphere. |
| **Detection Rule Catalog** | `src/appsec/models.py` | `RULE_METADATA` (7 rules: `AUTH-001`, `AUTH-002`, `INJ-001`, `XSS-001`, `RATE-001`, `HEALTH-001`, `RECON-001`) | Detection criteria, MITRE tactics, CWE mappings. |
| **Dynamic Quarantine Blocklist**| SQLite: `blocked_clients` | Table 11 (`client_ip`, `reason`, `rule_id`, `incident_id`, `blocked_at`, `expires_at`, `is_active`) | Actively quarantined attacker IPs. |
| **Known Vulnerabilities** | SQLite: `vulnerabilities` | Table 12 (`vuln_id`, `component_path`, `cwe_id`, `patch_diff`, `regression_test_status`, `status`) | Tracked application code defects and AST patches. |
| **SOAR Playbooks & Executions**| SQLite: `soar_playbooks`, `soar_executions` | Tables 16-20 (`execution_id`, `playbook_name`, `status`, `verification_status`, `context_json`) | Orchestrated workflow history and node telemetry. |
| **Self-Healing Executions** | SQLite: `self_healing_executions`| Table 22 (`execution_id`, `incident_id`, `lifecycle_stage`, `root_cause_analysis_json`, `selected_plan_json`, `pre_change_state_json`, `verification_state`) | 14-stage remediation records & pre-change snapshots. |
| **Autonomy Policies & Audit Logs**| SQLite: `self_healing_policies`, `self_healing_audit_logs` | Tables 23 & 24 (`autonomy_level`, `emergency_stop`, `allowlists`, audit entries) | Governance records and emergency stop ledger. |

---

## 3. Graph Entity Taxonomy for 3D Topology

The 3D topology does not fabricate fictitious devices or imaginary cloud clusters. Entities are strictly partitioned into three verifiable tiers:

```
                                  TOPOLOGY ENTITY TAXONOMY
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      ▼                                      ▼                                      ▼
[ SOURCE ENTITIES ]                  [ SECURITY ENTITIES ]                  [ TARGET ENTITIES ]
• Source IP Addresses                • Security Events                      • ShopSphere Edge Gateway
• Authenticated Users                • Detection Rules (7)                  • Target Endpoints (/api/...)
• Quarantined Attackers              • Correlated Incidents                 • Service Components
• Test Runners (Simulation)          • Remediation Operations               • Database Catalog Store
                                     • Verification Probes
```

### 1. Source Entities
- **Source IP**: `198.51.100.99`, `203.0.113.42`, `127.0.0.1` (labeled as internal sandbox).
- **User Identity**: `admin@shopsphere.local`, `customer@shopsphere.local` (from `users`).
- **Client Session**: Active tokens and session IDs.

### 2. Target Entities
- **Edge Gateway**: `DEV001: Edge Security Gateway` (central ingress hub).
- **Service Components**: `CartService`, `ProductService`, `UserService`, `AdminService`.
- **API Endpoints**: `/api/shop/auth/login`, `/api/shop/products`, `/api/shop/cart/items`, `/api/shop/admin/summary`.
- **Database Components**: `ShopSphere:SQLiteCatalog`, `ShopSphere:AuthStore`.

### 3. Security Entities
- **Detection Rules**: `INJ-001`, `AUTH-001`, `AUTH-002`, `XSS-001`, `RATE-001`, `HEALTH-001`, `RECON-001`.
- **Security Events**: Individual telemetry entries with severity indicators (Info, Medium, High, Critical).
- **Security Incidents**: Escalated incidents (`INC-...`).
- **Remediation Actions**: `BLOCK_IP`, `APPLY_RATE_LIMIT`, `CODE_REPAIR_PATCH`, `REVOKE_SESSION`.
- **Verification Probes**: Functional probe (HTTP 200) vs Exploit probe (HTTP 403/429).

---

## 4. Relationship & Correlation Audit

To prevent false visual proximity leading to erroneous analytical conclusions, edges are strictly typed and verifiable:

| Edge Type | Source Entity | Target Entity | Underlying Record / Rule | Classification |
| :--- | :--- | :--- | :--- | :---: |
| `DISPATCHED_REQUEST` | Source IP | Security Event | `security_events.client_ip` | **CONFIRMED** |
| `TARGETED_ENDPOINT` | Security Event | API Endpoint | `security_events.path` | **CONFIRMED** |
| `TRIGGERED_RULE` | Security Event | Detection Rule | `security_events.event_type = rule_id` | **CONFIRMED** |
| `CORRELATED_INTO` | Security Event | Incident | Shared `correlation_id` or `evidence_json` | **CONFIRMED** |
| `IMPACTS_SERVICE` | Incident | Service / Asset | `security_incidents.affected_endpoints_json` | **CONFIRMED** |
| `INITIATED_REMEDIATION`| Incident | Remediation Exec | `self_healing_executions.incident_id` | **CONFIRMED** |
| `TRIGGERED_PLAYBOOK` | Incident | SOAR Execution | `soar_executions.incident_id` | **CONFIRMED** |
| `PRODUCED_VERIFICATION`| Remediation Exec | Verification Probe | `self_healing_executions.verification_state` | **CONFIRMED** |
| `ENFORCED_QUARANTINE` | Source IP | Blocked Client | `blocked_clients.client_ip` | **CONFIRMED** |
| `SUSPECTED_SAME_CAMPAIGN`| Source IP A | Source IP B | Temporal proximity (<60s) targeting same rule | **INFERRED** |
| `HEURISTIC_LATERAL_LINK` | Endpoint A | Endpoint B | Sequential error cascade without explicit token | **INFERRED** |

Edges rendered with solid lines represent **CONFIRMED** database relationships. Dotted lines represent **INFERRED** heuristic correlations. Unknown or speculative relationships are omitted.

---

## 5. Real-Time Telemetry & SSE Capabilities

AutoHeal has an established Server-Sent Events (SSE) infrastructure:
- **Executive SSE Stream**: `/api/security/stream` (emits live threat events, block notifications, posture shifts).
- **Attack Center SSE Stream**: `/api/security/attack-center/stream` (emits step-by-step synthetic simulation execution progress).
- **Threat Center SSE Stream**: Native browser `EventSource` connection in `script.js`.

**Phase 8 Real-Time Design:**
- The 3D Threat Topology connects to `/api/threat-topology/stream` (or `/api/security/stream`) to update node threat pulsing and spawn newly detected edges dynamically without rebuilding the WebGL scene.
- Polling fallback (10s interval) guarantees operation if SSE is severed.

---

## 6. AI Provider Integration & Capabilities Audit

### Current State
1. **Installed Dependencies**: `fastapi`, `pydantic`, `httpx`, `langgraph`, `scikit-learn`.
2. **Proprietary SDKs**: No proprietary packages (`google-generativeai`, `openai`, `anthropic`) are baked into `requirements.txt`.
3. **Existing AI Model Assets**:
   - `models/autoheal_detector.joblib` (Isolation Forest / Random Forest classifier for anomaly detection).
   - `src/appsec/ai_advisor.py` (`AISecurityAdvisor`: maps MITRE ATT&CK techniques and generates grounded forensic summaries).

### AI Provider Architecture for Phase 8
In strict compliance with prompt constraints (*"Do not pretend an LLM is connected. Do not hardcode API keys."*), the **AI SOC Copilot** implements a dual-mode provider architecture:

```
                           AI COPILOT PROVIDER GATEWAY
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
[ CONFIGURED PROVIDER MODE ]                              [ DETERMINISTIC GROUNDED MODE ]
Triggered when:                                          Triggered when:
• `GEMINI_API_KEY` is present, OR                        • No external API key is set in env
• `OPENAI_API_KEY` is present, OR                        • Offline / air-gapped deployment
• `OLLAMA_HOST` is accessible                            • Local testing environment

Behavior:                                                Behavior:
• Calls real external/local LLM via httpx                • Uses AISecurityAdvisor & graph analytics
• Passes sanitized, evidence-grounded prompt             • Generates 100% deterministic, grounded
• Streams real responses                                   investigation dossiers & report narratives
• Explicitly attributes provider name                    • Explicitly discloses: "Deterministic Mode
                                                           (Local Rule-Based / Offline)"
```

This guarantees that:
- If a user configures `GEMINI_API_KEY=...` or `OPENAI_API_KEY=...`, AutoHeal engages the real LLM for conversational exploration.
- If no key is set, the platform remains 100% functional, delivering deterministic, evidence-based investigation without ever pretending an LLM is active.

---

## 7. Security, Privacy & Guardrail Constraints

1. **Prompt Injection Defense**: Raw query strings, user agents, and HTTP body samples from `security_events` are scrubbed before inclusion in LLM context. Markdown escape characters and delimiter injection tags are neutralized.
2. **Secret Redaction**: Passwords, API tokens, JWT secrets, PBKDF2 salts, and private keys are redacted using regex filters before being passed to either the Copilot or the frontend.
3. **Zero Autonomous Tool Abuse**: The Copilot provides *read-only* diagnostic tools (retrieving incidents, searching events, fetching playbooks). It cannot directly execute mutating operations (`BLOCK_IP`, code patches). Any state modification must be presented as an analyst proposal requiring explicit operator action.
4. **Target Allowlisting**: All investigative tools are strictly scoped to `localhost`, `127.0.0.1`, `ShopSphere`, and internal monitored assets.

---

## 8. Technical Implementation Plan

1. **Backend Graph & Copilot Engine**:
   - `autoheal/src/appsec/threat_topology_models.py`: Graph snapshot generator, entity node builders, relationship edge builders, temporal filters, attack sequence extractor.
   - `autoheal/src/appsec/threat_topology_api.py`: Endpoints at `/api/threat-topology/graph`, `/api/threat-topology/entities/{type}/{id}`, `/api/threat-topology/attack-sequence`, `/api/threat-topology/stream`.
   - `autoheal/src/appsec/copilot_engine.py`: Grounded investigation pipeline, evidence retriever, prompt builder, secret sanitizer, dual-mode provider handler, report generator.
   - `autoheal/src/appsec/copilot_api.py`: Endpoints at `/api/copilot/chat`, `/api/copilot/investigate/{incident_id}`, `/api/copilot/evidence`, `/api/copilot/reports/generate`, `/api/copilot/status`.
2. **Frontend 3D Threat Topology (`/threat-topology`)**:
   - Obsidian Sentinel canvas inside `#pageThreatTopology`.
   - Three.js WebGL graph renderer with force-directed spatial layout, node colors by entity type and severity, edge styles by confirmation status.
   - Interactive orbit controls (rotate, pan, zoom, select, focus, reset camera).
   - Filter toolbar (entity types, severity, time window, incident filter).
   - Entity Detail Inspector Drawer.
   - Chronological Attack Sequence Timeline view.
   - Accessible 2D table fallback.
3. **Frontend AI SOC Copilot (`/soc-copilot`)**:
   - Analyst workspace inside `#pageSocCopilot`.
   - Investigation context selector (incident, IP, asset, test run).
   - Conversational chat feed with streaming indicator and suggested investigation prompts.
   - Structured investigation dossier (Executive Summary, Confirmed Facts, Probable Causes, Hypotheses, Playbook Recommendations).
   - Incident Report Generator with live preview and export.
4. **Testing & Documentation**:
   - Comprehensive test suite `tests/test_threat_topology_and_copilot.py` covering graph construction, confirmed vs inferred edges, copilot grounding, prompt injection defenses, provider offline fallback, and report generation.
   - Full platform regression validation (173+ tests).
   - 16 detailed Phase 8 documentation files.
