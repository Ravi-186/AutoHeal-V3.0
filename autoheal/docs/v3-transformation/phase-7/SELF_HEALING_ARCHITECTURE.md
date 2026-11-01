# SELF-HEALING ARCHITECTURE & COMMAND CENTER DESIGN
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center  
**Target Environment:** ShopSphere E-Commerce Application (`http://localhost:8000`)  
**Design Identity:** Obsidian Sentinel  
**Phase:** Phase 7 — Advanced Self-Healing Command Center  
**Status:** IMPLEMENTED & PRODUCTION CERTIFIED  

---

## 1. Architectural Mission & Principles

The Self-Healing Command Center is AutoHeal's autonomous remediation headquarters. Its primary mission is to close the loop between threat detection, root-cause diagnosis, safe policy-governed remediation, and independent verification.

```
       +-------------------------------------------------------------+
       |             ShopSphere Protected Storefront                 |
       +-------------------------------------------------------------+
                                      |
                      [HTTP Telemetry & Anomalies]
                                      v
       +-------------------------------------------------------------+
       |             AppSecProtectionMiddleware / WAF                |
       +-------------------------------------------------------------+
                                      |
                         [Security Event Stream]
                                      v
       +-------------------------------------------------------------+
       |                   Detection Engine                          |
       |       (Rule Catalog & Sliding Window Correlator)            |
       +-------------------------------------------------------------+
                                      |
                         [Security Incident Trigger]
                                      v
       +=============================================================+
       |           SELF-HEALING COMMAND CENTER ENGINE                |
       |                                                             |
       |  1. Root-Cause Analyzer (Facts vs Probable vs Hypotheses)   |
       |  2. Remediation Planner (Action Recommendation)             |
       |  3. Risk & Business Impact Engine (4-Vector Scoring)        |
       |  4. Autonomy Policy Enforcer (Levels 0 - 3)                 |
       |  5. Emergency Stop Safety Kill-Switch                       |
       |  6. Execution Coordinator (AST Patches, WAF, Sessions)      |
       |  7. Independent Dual-Probe Verification (Adversary+Benign)  |
       |  8. Transactional Rollback & Pre-Change Restoration         |
       +=============================================================+
```

### Core Engineering Principles
1. **Zero Fabrication**: All counts, durations, success percentages, and risk classifications are computed strictly from real persisted records in SQLite (`self_healing_executions`, `self_healing_policies`, `self_healing_audit_logs`).
2. **Tripartite RCA**: Confirmed facts are strictly isolated from AI-generated hypotheses and heuristic causes.
3. **Defense-in-Depth Verification**: A remediation is never marked successful based on the API call return code alone; independent synthetic probes must confirm the adversary is quarantined while benign storefront visitors remain unimpaired.
4. **Guaranteed Reversibility**: Pre-change snapshots are captured before applying any modification, enabling safe, non-destructive rollbacks.
5. **Fail-Safe Emergency Stop**: An instantaneous hardware/software kill-switch halts automated actions without taking down the application or killing telemetry ingestion.

---

## 2. Command Center Subsystems

| Subsystem | Component Class | Responsibility |
| :--- | :--- | :--- |
| **Lifecycle State Machine** | `LIFECYCLE_STAGES` & `VALID_TRANSITIONS` | Enforces 14-state progression, preventing invalid leaps or duplicate transitions. |
| **Root-Cause Analyzer** | `RootCauseAnalyzer` | Separates Confirmed Facts, Probable Causes, and AI Hypotheses from SQLite telemetry. |
| **Risk & Impact Assessor** | `RiskImpactAssessor` | Evaluates Severity, Scope, Reversibility, and User Impact across 4 vectors (Score 4–14). |
| **Remediation Planner** | `RemediationPlanner` | Generates viable response options (`BLOCK_IP`, `APPLY_RATE_LIMIT`, `CODE_REPAIR_PATCH`, `REVOKE_SESSION`). |
| **Autonomy Policy Engine** | `SelfHealingEngine.evaluate_autonomy` | Enforces Levels 0–3, action allowlists, and target boundaries. |
| **Execution Coordinator** | `SelfHealingEngine.execute_plan` | Captures pre-change state and applies live or dry-run mutations. |
| **Independent Verifier** | `SelfHealingEngine.verify_remediation` | Executes synthetic loopback probes (adversary 403, benign 200, or AST regression tests). |
| **Rollback Manager** | `SelfHealingEngine.execute_rollback` | Reverts actions safely from pre-change snapshots and verifies clean restored state. |
| **Emergency Stop Controller** | `trigger_emergency_stop` | Locks all autonomous mutation while keeping event monitoring online. |
| **AI Remediation Advisor** | `/api/self-healing/ai-assistant` | Grounded, deterministic AI assistance for incident summaries, plan comparison, and reporting. |

---

## 3. Obsidian Sentinel UI Integration

The Self-Healing Command Center lives under **Incident Response → Self-Healing** (`#pageHealing`):
- **Remediation Overview**: 9 live KPI cards (Total Attempts, Successful, Failed, Pending Approval, Awaiting Verification, Verified Containment, Rollbacks, Avg Duration, Verification Failures).
- **Live System Protection Status**: 8-subsystem health grid (Detection Engine, Event Ingestion, Remediation Engine, Verification Engine, SOAR Engine, Database, Background Workers, ShopSphere Target).
- **14-State Lifecycle Visualizer**: Stepper showing active step, completed history, and rollback branches.
- **Activity Explorer**: Paginated, searchable execution history with quick action buttons.
- **RCA Workspace**: Color-coded cards for Confirmed Facts (Green), Probable Causes (Amber), and AI Hypotheses (Purple).
- **Remediation Planner**: Plan comparison cards with explainable risk breakdown.
- **Safety & Autonomy Modals**: Autonomy Policy Editor, Emergency Stop, Guided New Remediation, and Immutable Audit Trail.
