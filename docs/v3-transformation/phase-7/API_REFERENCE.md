# AutoHeal Phase 7: REST API Reference

## 1. Overview
The Self-Healing Command Center exposes a RESTful API mounted at `/api/self-healing`. All endpoints communicate via JSON, require no third-party cloud runtime dependencies, and execute real database queries against SQLite tables (`self_healing_executions`, `self_healing_policies`, `self_healing_audit_logs`).

---

## 2. Endpoints Specification

### 1. Persistent Dashboard & Protection Status

#### `GET /api/self-healing/overview`
Retrieves live persistent KPIs calculated across all historical executions.
- **Response (`200 OK`)**:
```json
{
  "total_attempts": 42,
  "successful_remediations": 39,
  "failed_remediations": 3,
  "pending_approvals": 2,
  "awaiting_verification": 1,
  "verified_containment": 38,
  "rollback_count": 3,
  "avg_duration_ms": 312.4,
  "verification_failures": 1
}
```

#### `GET /api/self-healing/protection-status`
Returns live readiness, operational status, and health metrics for the 8 protection subsystems.
- **Response (`200 OK`)**:
```json
{
  "subsystems": [
    {"id": "waf", "name": "WAF & Perimeter Shield", "status": "HEALTHY", "active_rules": 14, "blocked_ips": 3},
    {"id": "rate_limiter", "name": "Sliding-Window Rate Limiter", "status": "HEALTHY", "window_sec": 8.0, "max_rpm": 15},
    {"id": "ast_patcher", "name": "AST Code Repair Engine", "status": "READY", "target": "CartService / ProductService"},
    {"id": "verification", "name": "Dual-Probe Verifier", "status": "ARMED", "mode": "Functional + Exploit Probes"},
    {"id": "soar", "name": "SOAR Playbook Orchestrator", "status": "HEALTHY", "active_playbooks": 5},
    {"id": "db_sentinel", "name": "Database Integrity Guard", "status": "NOMINAL", "active_connections": 1},
    {"id": "audit_ledger", "name": "Immutable Audit Ledger", "status": "SYNCHRONIZED", "total_records": 128},
    {"id": "threat_intel", "name": "Threat Intelligence Correlation", "status": "STREAMING", "confidence_floor": 0.85}
  ]
}
```

---

### 2. Execution Management & Lifecycle State Machine

#### `GET /api/self-healing/activity`
Returns paginated remediation execution history with optional stage filtering.
- **Query Parameters**:
  - `limit` (int, default `20`)
  - `offset` (int, default `0`)
  - `stage` (string, optional, e.g. `AWAITING_APPROVAL`, `VERIFIED`)
- **Response (`200 OK`)**:
```json
{
  "total": 42,
  "limit": 20,
  "offset": 0,
  "executions": [...]
}
```

#### `GET /api/self-healing/executions/{execution_id}`
Retrieves full details for a single execution record.
- **Response (`200 OK`)**:
```json
{
  "execution_id": "EXEC-20261101-A1B2C3D4",
  "incident_id": "INC-INJ-1004",
  "threat_category": "SQL Injection",
  "severity": "CRITICAL",
  "lifecycle_stage": "VERIFIED",
  "affected_asset": "ShopSphere:ProductCatalog",
  "root_cause_analysis": { ... },
  "selected_plan": { ... },
  "risk_level": "HIGH",
  "approval_state": "APPROVED",
  "verification_state": "VERIFIED",
  "rollback_state": "NONE",
  "pre_change_state": { ... },
  "duration_ms": 284.1,
  "created_at": "2026-11-01T10:05:00Z"
}
```

#### `POST /api/self-healing/executions/create`
Initializes a new remediation lifecycle execution.
- **Request Body**:
```json
{
  "incident_id": "INC-AUTH-1002",
  "threat_category": "Credential Stuffing",
  "severity": "HIGH",
  "affected_asset": "UserService:login"
}
```

---

### 3. Diagnosis & Planning Engine

#### `GET /api/self-healing/diagnose/{incident_id}`
Executes root cause analysis separating evidence-proven facts from hypotheses.
- **Response (`200 OK`)**:
```json
{
  "incident_id": "INC-AUTH-1002",
  "confirmed_facts": [
    "Source IP 198.51.100.99 originated 48 consecutive failed logins within 60s",
    "Affected endpoint: /api/auth/login",
    "Targeted account identity: admin@shopsphere.local"
  ],
  "probable_causes": [
    "Distributed dictionary password spraying targeting administrative accounts",
    "Automated brute-force botnet probe lacking credential cache"
  ],
  "ai_hypotheses": [
    "Potential credential leak from third-party breach dump (Collection #1)",
    "Attacker attempting to trigger account lockout denial of service"
  ]
}
```

#### `POST /api/self-healing/plans/generate`
Formulates viable remediation options with 4-vector risk scores.
- **Request Body**:
```json
{
  "incident_id": "INC-AUTH-1002"
}
```
- **Response (`200 OK`)**:
```json
{
  "incident_id": "INC-AUTH-1002",
  "plans": [
    {
      "plan_id": "PLAN-IP-01",
      "action_type": "BLOCK_IP",
      "target": "198.51.100.99",
      "risk_level": "LOW",
      "risk_score": 5,
      "reversibility": "INSTANT",
      "description": "Quarantine malicious source IP 198.51.100.99 in WAF for 3600s."
    },
    {
      "plan_id": "PLAN-SESS-02",
      "action_type": "REVOKE_SESSION",
      "target": "admin@shopsphere.local",
      "risk_level": "MEDIUM",
      "risk_score": 8,
      "reversibility": "SIMPLE",
      "description": "Invalidate active session tokens for targeted user identity."
    }
  ]
}
```

---

### 4. Execution, Approval, Verification & Rollback

#### `POST /api/self-healing/approve`
Authorizes execution for remediation plans requiring operator sign-off.
- **Request Body**:
```json
{
  "execution_id": "EXEC-20261101-A1B2C3D4",
  "approver": "senior_analyst@sentinel.sec",
  "notes": "Reviewed RCA; IP block authorized."
}
```

#### `POST /api/self-healing/execute`
Executes an approved remediation plan.
- **Request Body**:
```json
{
  "execution_id": "EXEC-20261101-A1B2C3D4",
  "plan": {
    "action_type": "BLOCK_IP",
    "target": "198.51.100.99"
  },
  "is_dry_run": false
}
```

#### `POST /api/self-healing/verify`
Manually triggers independent dual-probe verification.
- **Request Body**:
```json
{
  "execution_id": "EXEC-20261101-A1B2C3D4"
}
```

#### `POST /api/self-healing/rollback`
Reverts executed state changes using the stored pre-change snapshot.
- **Request Body**:
```json
{
  "execution_id": "EXEC-20261101-A1B2C3D4",
  "reason": "False positive affecting customer branch office",
  "actor": "lead_soc@sentinel.sec"
}
```

---

### 5. Policies & Safety Controls

#### `GET /api/self-healing/policies`
Returns active autonomy policy settings and safety guardrails.

#### `PUT /api/self-healing/policies`
Updates autonomy levels, approval thresholds, and allowlists.
- **Request Body**:
```json
{
  "autonomy_level": 2,
  "max_risk_level": "HIGH",
  "approval_risk_threshold": "HIGH",
  "action_allowlist": ["BLOCK_IP", "APPLY_RATE_LIMIT", "REVOKE_SESSION", "CODE_REPAIR_PATCH"],
  "target_allowlist": ["127.0.0.1", "localhost", "ShopSphere"],
  "actor": "ciso@sentinel.sec"
}
```

#### `POST /api/self-healing/emergency-stop`
Engages the master circuit breaker.

#### `POST /api/self-healing/emergency-resume`
Deactivates the master circuit breaker.

#### `GET /api/self-healing/audit-logs`
Returns chronologically ordered audit logs.

#### `POST /api/self-healing/ai-assistant`
Interacts with the grounded AI Self-Healing Assistant.
