# AutoHeal Phase 7: Database Schema Changes

## 1. Overview
Phase 7 extends AutoHeal's unified SQLite database schema (`autoheal/shopsphere/database.py`) with three high-performance, normalized tables (Tables 22, 23, and 24), six B-tree indexes, and deterministic baseline seeding. This ensures all self-healing state transitions, policies, snapshots, and audit events are durably persisted without in-memory transient data loss.

---

## 2. Table Schemas

### Table 22: `self_healing_executions`
Tracks the complete 14-stage lifecycle of each remediation attempt, including root cause facts, explainable risk calculations, pre-change snapshots, and dual-probe verification outcomes.

```sql
CREATE TABLE IF NOT EXISTS self_healing_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT UNIQUE NOT NULL,
    incident_id TEXT,
    lifecycle_stage TEXT NOT NULL DEFAULT 'DETECTED',
    threat_category TEXT NOT NULL,
    severity TEXT NOT NULL,
    affected_asset TEXT,
    root_cause_analysis_json TEXT,
    selected_plan_json TEXT,
    risk_level TEXT DEFAULT 'LOW',
    risk_score INTEGER DEFAULT 0,
    approval_state TEXT DEFAULT 'NOT_REQUIRED',
    approver TEXT,
    approval_notes TEXT,
    approved_at TIMESTAMP,
    verification_state TEXT DEFAULT 'UNVERIFIED',
    verification_details_json TEXT,
    rollback_state TEXT DEFAULT 'NONE',
    rollback_reason TEXT,
    rolled_back_at TIMESTAMP,
    pre_change_state_json TEXT,
    duration_ms REAL DEFAULT 0.0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table 23: `self_healing_policies`
Manages system-wide autonomy levels (0–3), safety guardrails, target/action allowlists, and the master Emergency Stop flag.

```sql
CREATE TABLE IF NOT EXISTS self_healing_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT UNIQUE NOT NULL,
    policy_name TEXT NOT NULL,
    autonomy_level INTEGER NOT NULL DEFAULT 2,
    emergency_stop INTEGER NOT NULL DEFAULT 0,
    emergency_stop_reason TEXT,
    emergency_stop_at TIMESTAMP,
    emergency_stop_by TEXT,
    action_allowlist_json TEXT NOT NULL,
    target_allowlist_json TEXT NOT NULL,
    max_risk_level TEXT NOT NULL DEFAULT 'HIGH',
    approval_risk_threshold TEXT NOT NULL DEFAULT 'HIGH',
    max_concurrent_executions INTEGER NOT NULL DEFAULT 5,
    require_dual_approval INTEGER NOT NULL DEFAULT 0,
    auto_rollback_on_failure INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table 24: `self_healing_audit_logs`
An append-only, immutable audit ledger capturing all policy modifications, emergency stop events, and lifecycle state changes.

```sql
CREATE TABLE IF NOT EXISTS self_healing_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT,
    policy_id TEXT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details_json TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Performance Indexes

Six dedicated indexes optimize high-velocity queries across dashboard filters, correlation lookups, and audit inspections:

```sql
CREATE INDEX IF NOT EXISTS idx_sh_exec_status ON self_healing_executions (lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_sh_exec_incident ON self_healing_executions (incident_id);
CREATE INDEX IF NOT EXISTS idx_sh_exec_verification ON self_healing_executions (verification_state);
CREATE INDEX IF NOT EXISTS idx_sh_exec_approval ON self_healing_executions (approval_state);
CREATE INDEX IF NOT EXISTS idx_sh_audit_action ON self_healing_audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_sh_audit_exec ON self_healing_audit_logs (execution_id);
```

---

## 4. Seeding & Baseline Initialization

During database initialization (`init_db()`), `seed_self_healing_defaults()` executes:
1. **Default Policy**: Inserts `POLICY-SENTINEL-DEFAULT` (Autonomy Level 2, Auto-rollback enabled, allowlisting local ShopSphere components).
2. **Baseline Executions**: Seeds four representative executions across realistic threat categories (`SQL Injection`, `Credential Stuffing`, `High-Frequency Scraping`, `AST Logic Flaw`) with verified metrics.
3. **Audit Records**: Seeds corresponding baseline audit events documenting system policy bootstrap.
