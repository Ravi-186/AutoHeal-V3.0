# AutoHeal v3.0 — Phase 5: Incident Command Center Architecture

## 1. Executive Overview

The **Enterprise Incident Command Center** represents the central operational nervous system of the AutoHeal v3.0 AppSec platform. Designed under the **Obsidian Sentinel** visual and architectural standard, it delivers real-time situational awareness, rapid forensic triage, attack-chain timeline reconstruction, evidence integrity assurance, and closed-loop self-healing verification.

This document articulates the end-to-end architecture unifying ingress middleware telemetry, detection correlation engines, attack simulation center outputs, digital evidence stores, SOAR containment automations, and analyst collaboration workflows.

---

## 2. Architectural Topology

```mermaid
graph TD
    subgraph Data Sources & Ingress
        ShopSphere[ShopSphere Ingress Middleware] -->|HTTP Telemetry| SecEvents[security_events SQLite]
        AttackSim[Attack Simulation Center] -->|Execution Telemetry| SimExec[simulation_executions]
    end

    subgraph Detection & Correlation
        SecEvents --> DetEngine[Sliding-Window Correlation Engine]
        DetEngine -->|Incident Escalation| IncidentsDB[(security_incidents)]
    end

    subgraph Command Center Services
        IncidentsDB --> StatsService[KPI Aggregation Service]
        IncidentsDB --> QueryService[Paginated Query & Filter Engine]
        IncidentsDB --> TimelineService[Timeline Reconstruction Engine]
        IncidentsDB --> EvidenceService[Forensic Evidence Explorer]
        IncidentsDB --> AttackSeqService[Attack Sequence Synthesizer]
        IncidentsDB --> LifecycleService[State Machine & Verification Gate]
        IncidentsDB --> ConcurrencyService[Optimistic Concurrency Manager]
    end

    subgraph Immutable Audit & Collaboration
        LifecycleService --> ActivityLog[(incident_activity_logs)]
        ConcurrencyService --> ActivityLog
    end

    subgraph Presentation Tier (Obsidian Sentinel)
        StatsService --> RibbonKPI[8 KPI Metric Cards]
        QueryService --> TableView[Interactive Incidents Table]
        TimelineService --> DetailWS[Incident Detail Workspace]
        EvidenceService --> DetailWS
        AttackSeqService --> DetailWS
        LifecycleService --> ModalControls[Status / Assign / Priority Modals]
    end
```

---

## 3. Core Architectural Subsystems

### 3.1 Real-Time KPI Aggregation Subsystem
All operational statistics presented in the Command Center are computed from actual persisted SQLite records in `security_incidents`:
- **Total Incidents:** Cumulative count of all recorded security incidents.
- **Active Incidents:** Non-resolved, non-closed incidents currently requiring operational attention.
- **Critical Incidents:** Incidents with `severity = 'CRITICAL'`.
- **High-Severity Incidents:** Incidents with `severity = 'HIGH'`.
- **Investigating Incidents:** Incidents actively under investigation (`status = 'INVESTIGATING'`).
- **Pending Remediation:** Incidents with uncompleted remediation actions (`status IN ('NEW', 'TRIAGED', 'INVESTIGATING', 'CONTAINMENT')`).
- **Verification Failures:** Incidents where autonomous dual-probe verification failed (`verification_status LIKE '%FAIL%'`).
- **Resolved Incidents:** Formally validated incidents that passed resolution verification gates (`status IN ('RESOLVED', 'CLOSED')`).

### 3.2 High-Throughput Paginated Query Engine
To accommodate large production databases, the incident list endpoint (`/api/security/incidents`) supports server-side compound filtering, full-text searching, multi-column sorting, and pagination:
- **Filtering Dimensions:** Time Range (`1h`, `24h`, `7d`, `30d`, `all`), Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), Status (`NEW`, `TRIAGED`, `INVESTIGATING`, `CONTAINMENT`, `REMEDIATION`, `VERIFICATION`, `RESOLVED`, `CLOSED`), Priority (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and Assigned Analyst.
- **Multi-Field Search:** Real-time LIKE matching across `incident_id`, `title`, `rule_id`, `target_endpoint`, `summary`, and `source_ip`.
- **Formula-Safe CSV Streaming:** Direct CSV generation with RFC-4180 escaping and formula injection immunization (`'`, `=`, `+`, `-`, `@`).

### 3.3 Investigation Workspace Subsystem
A dedicated, full-width workspace (`#incidentDetailWorkspace`) renders deep-dive telemetry for selected incidents across 8 specialized investigation tabs:
1. **Overview:** Executive summary, detection rationale, actual vs. potential impact, affected micro-endpoints, and recommended investigation roadmap.
2. **Event Timeline:** Unified chronological stepper reconciling ingress requests, detection triggers, SOAR policy deployments, synthetic probes, and analyst notes.
3. **Digital Evidence Explorer:** Structured evidence inspector featuring cryptographic SHA-256 integrity hashing and secret redaction.
4. **Attack Sequence Analysis:** 5-stage attack chain flowchart clearly demarcating observed facts from analytical hypotheses and mapping to MITRE ATT&CK.
5. **Root-Cause Analysis:** Multi-field root-cause workspace persisting suspected entry points, contributing conditions, and confirmed conclusions.
6. **Response Actions:** SOAR response console providing dynamic IP quarantine, token revocation, and AST virtual patching options.
7. **Verification:** Autonomous dual-probe validation console confirming attacker 403 Forbidden vs benign shopper 200 OK loopback telemetry.
8. **Audit History & Notes:** Immutable cryptographically attributable audit trail coupled with internal analyst collaboration thread.

---

## 4. Integration Matrix

| Subsystem | Integration Point | Data Exchanged | Protocol |
| :--- | :--- | :--- | :--- |
| **Security Event Explorer** | `security_events` table | Ingress telemetry, client IP, path, method, status code | SQLite Foreign Key / Query |
| **Detection Engine** | `src.appsec.models.create_security_incident` | Rule ID, confidence score, evidence dictionary, severity | Internal Python API |
| **Attack Simulation Center** | `simulation_executions` table | `related_simulation_id`, scenario ID, execution ID | Foreign Reference / Metadata |
| **SOAR Response Engine** | `blocked_clients`, WAF middleware | IP quarantine status, token blacklist, virtual patch | REST / Internal Dispatcher |
| **Verification Agent** | Loopback probe client | Attacker status (403), shopper status (200) | Synthetic HTTP Probing |
| **Audit Logging** | `incident_activity_logs` table | Action type, author, version, content, details | SQLite Append-Only Journal |
| **Reporting Engine** | `src.appsec.reporter` | Formatted Markdown, JSON dossier, PDF report | REST Streaming / File Export |

---

## 5. Architectural Non-Negotiables

1. **Persisted Ground Truth:** No statistics, metrics, timeline entries, or evidence records may be hardcoded or fabricated on the client.
2. **Immutable Forensic Auditing:** Every lifecycle status transition, priority change, analyst assignment, root-cause update, and note addition generates an immutable record in `incident_activity_logs`.
3. **Optimistic Concurrency:** All mutating operations require `current_version` checking against the persisted record version to prevent silent concurrent overwrites.
4. **Defensive Verification Gate:** Incidents cannot be marked `RESOLVED` unless independent synthetic verification confirms containment (`VERIFIED_CONTAINED` or `VERIFIED_RECOVERED`) and non-empty resolution notes are supplied.
