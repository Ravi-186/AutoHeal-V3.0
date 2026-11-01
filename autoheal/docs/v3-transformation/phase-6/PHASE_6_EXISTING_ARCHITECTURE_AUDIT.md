# AutoHeal v3.0 — Phase 6: Architecture Audit & SOAR Foundation Inspection
## Enterprise Security Orchestration, Automation and Response (SOAR)

---

## 1. Executive Summary

This document establishes the architectural baseline for **Phase 6: Visual SOAR Automation Builder** in the AutoHeal platform. In accordance with the Phase 6 mandate, a deep audit of the existing backend modules, database schemas, frontend controllers, incident response mechanisms, and test suites was conducted prior to any implementation.

This audit maps existing capabilities, catalogs reusable components, identifies technical gaps, defines security constraints, and outlines the integration architecture necessary to build an enterprise-grade visual SOAR workflow engine without reinventing working modules or fabricating capabilities.

---

## 2. Existing Automation Architecture

The current AutoHeal system possesses foundational automation concepts scattered across three layers:

```
+----------------------------------------------------------------------------------------------------+
|  CURRENT LAYER 1: Device-Level Simulated StateGraph (src/graph/workflow.py)                        |
|  - Powered by LangGraph StateGraph (detect -> respond -> verify loop)                              |
|  - Targets synthetic simulated network devices (DEV001, CORP-LAPTOP-142)                           |
|  - Fixed hardcoded topology: unconditional or single binary conditional edges                      |
+----------------------------------------------------------------------------------------------------+
                                                  |
+----------------------------------------------------------------------------------------------------+
|  CURRENT LAYER 2: Application Security Response Engine (src/appsec/responder.py)                   |
|  - AppSecResponder executes static POLICY_RULES (INJ-001, XSS-001, AUTH-001, RATE-001)           |
|  - Performs dynamic IP quarantine via block_client_ip() in SQLite blocked_clients                  |
|  - Dispatches dry-run simulation or live mitigation with execution duration timing                 |
|  - Hands off directly to AppSecVerifier for dual-probe containment verification                   |
+----------------------------------------------------------------------------------------------------+
                                                  |
+----------------------------------------------------------------------------------------------------+
|  CURRENT LAYER 3: Closed-Loop Dual-Probe Verification (src/appsec/verifier.py)                     |
|  - AppSecVerifier conducts Perimeter Probes (attacker 403 Forbidden) and Availability Probes       |
|    (benign shopper 200 OK)                                                                         |
|  - Bounded escalation policy (max 3 retries with 2-second cooldown)                                |
|  - Immutable logging to incident records and activity trail                                        |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 Reusable Components Identified

| Existing Component | Source File | Reusability in Phase 6 Visual SOAR |
| :--- | :--- | :--- |
| **`AppSecResponder`** | `src/appsec/responder.py` | Provides proven implementations for `BLOCK_IP`, `RATE_LIMIT`, `RECOVER_SERVICE`, and rollback capabilities. Reused as the core action dispatch engine. |
| **`AppSecVerifier`** | `src/appsec/verifier.py` | Implements true dual-probe verification (Perimeter 403 vs Benign 200). Reused for Verification nodes in SOAR playbooks. |
| **`UserService`** | `shopsphere/services.py` | Server-side session management (`logout(token)`), credential verification, and user lookup. Reused for session revocation and account disable action nodes. |
| **`VulnerabilityManager`** | `src/appsec/vulnerability_manager.py` | AST virtual patch deployment, rollback, and syntax diff verification. Reused for AST surgical virtual patching actions. |
| **`AppSecReporter`** | `src/appsec/reporter.py` | Structured JSON and executive PDF report compilation. Reused for automated reporting nodes. |
| **`Database Connection Manager`** | `shopsphere/database.py` | Context-managed SQLite connection pool (`get_db_connection()`) with WAL mode and foreign key enforcement. |
| **`Incident Management & Concurrency`** | `src/appsec/models.py` | Complete incident creation, update, note appending, analyst assignment, activity logging, and versioning implemented in Phase 5. |

---

## 3. Available Response Actions Catalog

The platform currently supports the following real, backend-verified response actions that will be exposed in the Visual SOAR Builder:

1. **Dynamic IP Quarantine (`BLOCK_IP`):**
   - *Backend Implementation:* `models.block_client_ip()`, `blocked_clients` table, enforced at runtime by `AppSecProtectionMiddleware`.
   - *Parameters:* `client_ip`, `reason`, `rule_id`, `duration_seconds`.
2. **Dynamic IP Release (`UNBLOCK_IP`):**
   - *Backend Implementation:* `models.unblock_client_ip()`.
   - *Parameters:* `client_ip`.
3. **Session Revocation (`REVOKE_SESSION`):**
   - *Backend Implementation:* `UserService.logout(token)` / database update invalidating `token` and `token_expires_at` in `users`.
   - *Parameters:* `user_token` or `user_email`.
4. **Account Quarantine / Disable (`DISABLE_ACCOUNT`):**
   - *Backend Implementation:* Database update expiring session tokens and flagging user status.
   - *Parameters:* `user_email` or `user_id`.
5. **Rate-Limit Tightening (`APPLY_RATE_LIMIT`):**
   - *Backend Implementation:* Dynamic IP quarantine with `RATE_LIMIT` tag and custom duration window.
   - *Parameters:* `client_ip`, `duration_seconds`, `threshold`.
6. **Create Incident (`CREATE_INCIDENT`):**
   - *Backend Implementation:* `models.create_security_incident()`.
   - *Parameters:* `title`, `category`, `severity`, `summary`, `source_ip`, `evidence`.
7. **Append Incident Note (`ADD_INCIDENT_NOTE`):**
   - *Backend Implementation:* `models.add_incident_note()`.
   - *Parameters:* `incident_id`, `content`, `author`.
8. **Assign Analyst (`ASSIGN_ANALYST`):**
   - *Backend Implementation:* `models.assign_incident_analyst()`.
   - *Parameters:* `incident_id`, `analyst`, `reason`.
9. **Update Incident Priority (`UPDATE_PRIORITY`):**
   - *Backend Implementation:* `models.update_incident_priority()`.
   - *Parameters:* `incident_id`, `priority`, `reason`.
10. **Run Verification Probe (`RUN_VERIFICATION_PROBE`):**
    - *Backend Implementation:* `AppSecVerifier.verify_incident_containment()`.
    - *Parameters:* `incident_id`, `target_url`, `source_ip`.
11. **Generate Forensic Report (`GENERATE_REPORT`):**
    - *Backend Implementation:* `AppSecReporter.generate_incident_report()`.
    - *Parameters:* `incident_id`, `format` (`json` / `pdf`).

---

## 4. Gaps & Missing Capabilities

While individual action primitives exist, the system lacks the workflow orchestration infrastructure required for an enterprise SOAR builder:

1. **No Workflow Definition Persistence:**
   There are no database tables to store user-defined playbooks, nodes, edges, parameters, versions, draft/published states, and metadata.
2. **No Visual Workflow Canvas:**
   The current `#pageSoar` view contains only a static 5-node HTML flowchart (`.soar-flowchart`) and an active blocklist table. There is no interactive canvas allowing drag-and-drop, node creation, connection dragging, panning, zooming, or visual configuration.
3. **No Dynamic Workflow Validation Engine:**
   No server-side DAG validator exists to check graph connectivity, trigger presence, unreachable nodes, invalid branch mappings, unsupported node configurations, or cycle detection.
4. **No Dynamic Execution Engine:**
   Existing execution relies on hardcoded loops (`AutoHealGraph` in `src/graph/workflow.py` or static rules in `responder.py`). There is no engine capable of executing arbitrary graph topologies, evaluating dynamic condition expressions, handling branch routing, pausing at approval checkpoints, and resuming execution.
5. **No Approval Center:**
   High-impact actions cannot be intercepted for analyst approval; the system lacks approval queues, decision recording, and replay protection.
6. **No Execution History & Node-by-Node Telemetry:**
   No schema or engine exists to log individual execution runs, per-node outputs, latency, retry counts, or verification outcomes.

---

## 5. Required Backend Changes & Architecture

### 5.1 Database Schema Extensions (SQLite)
To support Phase 6, five new database tables and associated indexes must be added to `shopsphere/database.py`:
- `soar_playbooks`: Primary registry of workflows (name, category, description, status, current_version, trigger_type, owner).
- `soar_playbook_versions`: Immutable version snapshots (version number, nodes_json, edges_json, config_json, validation_hash, created_at).
- `soar_executions`: Execution instances (execution_id, playbook_id, version, trigger_source, incident_id, status, execution_mode, started_at, completed_at, duration_ms, error).
- `soar_node_executions`: Per-node telemetry records (node_id, node_type, node_name, status, input_json, output_json, start_time, end_time, duration_ms, retry_count, error).
- `soar_approvals`: Pending and resolved approval gates (approval_id, execution_id, node_id, action_description, status, requested_by, approved_by, reason, decided_at).
- `soar_audit_logs`: Immutable security audit log for all SOAR modifications and privileged actions.

### 5.2 Server-Side Execution & Validation Engine
A dedicated module `src/appsec/soar_engine.py` will implement:
- `SOARValidator`: Validates schemas, DAG acyclicity, connectivity, and configuration constraints.
- `SOARExecutionEngine`: Coordinates step-by-step traversal, condition evaluation, branch resolution, approval pauses, action execution, and error handling.
- `SOARApprovalManager`: Manages approval creation, notification, single-use resolution, and workflow continuation.

### 5.3 REST API Endpoints
A dedicated FastAPI router mounted at `/api/soar` will expose:
- Playbook CRUD: `GET /playbooks`, `POST /playbooks`, `GET /playbooks/{id}`, `PUT /playbooks/{id}`, `DELETE /playbooks/{id}`.
- Versions & Publishing: `GET /playbooks/{id}/versions`, `POST /playbooks/{id}/publish`.
- Validation: `POST /playbooks/validate`.
- Execution & Dry-Run: `POST /playbooks/{id}/execute`, `POST /playbooks/{id}/dry-run`.
- Execution Monitoring: `GET /executions`, `GET /executions/{id}`, `POST /executions/{id}/cancel`.
- Approvals: `GET /approvals`, `POST /approvals/{id}/decide`.
- Audit History: `GET /audit-logs`.

---

## 6. Security Constraints & Guardrails

1. **Strict Target Allowlisting:**
   Workflows must only execute actions against the isolated ShopSphere environment (`http://localhost:8000`, `127.0.0.1`, in-process test client). External network connections or arbitrary URLs are strictly forbidden.
2. **Zero Code Injection Surface:**
   Workflow definitions must never accept raw Python expressions, JavaScript `eval`, shell commands, or unparameterized SQL queries. All conditions must be evaluated using safe, structured comparison operators (`EQUALS`, `NOT_EQUALS`, `CONTAINS`, `GREATER_THAN`, `IN_LIST`).
3. **Approval Gates for High-Impact Actions:**
   Actions that disconnect clients, ban IP addresses, disable accounts, or apply code patches must support an enforced `requires_approval` flag that pauses execution until an authorized analyst (`role = 'admin'` or authorized SOC analyst) submits a signed approval.
4. **Idempotency & Replay Protection:**
   Approval tokens must be strictly single-use. Executions must enforce unique execution IDs and prevent duplicate simultaneous runs for the same incident/target.
5. **Sensitive Telemetry Redaction:**
   All execution logs, node input/output records, and audit events must sanitize credentials, passwords, and tokens before persistence or presentation.

---

## 7. Frontend Architecture Plan

The current `#pageSoar` section in `web/templates/index.html` will be expanded into a unified, high-density SOAR Automation Center matching the **Obsidian Sentinel** standard:
- **Playbook Library View:** Grid and table view of all playbooks with status pills, execution counts, success/failure metrics, and filter toolbar.
- **Visual Playbook Builder (Canvas):** High-performance SVG-based interactive canvas supporting node dragging, connecting bezier/orthogonal curves, multi-selection, pan/zoom, minimap, undo/redo, and keyboard accessibility fallback.
- **Node Configuration Slide-Over Panel:** Dynamic contextual form with schema validation, input mapping, error tooltips, and real-time guidance.
- **Execution Monitor & Timeline:** Live execution tracker displaying node progression, status badges, execution timings, and drill-down drawers.
- **Approval Center:** Dedicated queue for pending human-in-the-loop decisions with contextual incident evidence.
- **Integration with Incident Command Center:** Direct "Launch Playbook" modal embedded in Phase 5's `#incidentDetailWorkspace`.

---

## 8. Conclusion

The existing AutoHeal codebase provides solid, verified primitives for IP blocking, session management, incident lifecycle management, and dual-probe verification. Phase 6 will synthesize these disparate capabilities into a unified, enterprise-grade Visual SOAR platform with full backend authoritativeness, robust validation, and uncompromised security.
