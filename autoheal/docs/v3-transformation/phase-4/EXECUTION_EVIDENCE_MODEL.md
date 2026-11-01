# Execution Evidence Model & Forensic Inspector (Phase 4)
## AutoHeal Sentinel v3.0 — Immutable Telemetry Records & Forensic Dossiers

### 1. Data Model & Database Schema

All defensive security simulations, step traces, detection benchmarks, and containment outcomes are persisted immutably in the `simulation_executions` table in SQLite (`shopsphere/database.py`).

```sql
CREATE TABLE IF NOT EXISTS simulation_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT UNIQUE NOT NULL,
    scenario_id TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    risk_category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'HIGH',
    target_url TEXT NOT NULL,
    client_ip TEXT NOT NULL,
    execution_mode TEXT NOT NULL DEFAULT 'live',
    status TEXT NOT NULL DEFAULT 'PENDING',
    detection_outcome TEXT NOT NULL DEFAULT 'PENDING',
    protection_verified INTEGER NOT NULL DEFAULT 0,
    expected_rule_id TEXT,
    actual_rule_id TEXT,
    incident_id TEXT,
    request_count INTEGER NOT NULL DEFAULT 0,
    blocked_count INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms REAL,
    parameters_json TEXT,
    steps_json TEXT,
    evidence_json TEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sim_exec_id ON simulation_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_sim_scenario ON simulation_executions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_sim_status ON simulation_executions(status);
CREATE INDEX IF NOT EXISTS idx_sim_time ON simulation_executions(start_time);
```

---

### 2. Forensic Step Trace Format (`steps_json`)

Every individual network interaction during a security test is recorded as a structured step trace in `steps_json`:

```json
[
  {
    "attempt": 1,
    "method": "POST",
    "endpoint": "/api/shop/auth/login",
    "status_code": 401,
    "latency_ms": 14.2,
    "correlation_id": "corr-d831a4",
    "message": "Attempt 1/5: POST /api/shop/auth/login -> HTTP 401 (14.2ms)"
  },
  {
    "attempt": 2,
    "method": "POST",
    "endpoint": "/api/shop/auth/login",
    "status_code": 401,
    "latency_ms": 11.5,
    "correlation_id": "corr-e992b1",
    "message": "Attempt 2/5: POST /api/shop/auth/login -> HTTP 401 (11.5ms)"
  },
  {
    "step": "VERIFICATION_PROBE",
    "endpoint": "/api/shop/auth/login",
    "status_code": 403,
    "is_blocked": true,
    "latency_ms": 8.1,
    "message": "Verification Probe: HTTP 403 - PROTECTION VERIFIED (Blocked by Sentinel)"
  }
]
```

---

### 3. Forensic Evidence Dossier Schema (`evidence_json`)

The `evidence_json` payload stores cryptographic links, target endpoints, mitigation metadata, and error details:

```json
{
  "target_endpoint": "/api/shop/auth/login",
  "verification_details": "Client IP 198.51.100.42 quarantined; subsequent requests dropped with HTTP 403 Forbidden.",
  "matched_rule": "AUTH-001",
  "action": "BLOCK_IP",
  "client_ip": "198.51.100.42",
  "dual_probe_results": {
    "attacker_status": 403,
    "benign_status": 200,
    "collateral_damage_detected": false
  }
}
```

---

### 4. Forensic Evidence Drawer UX (`#simulationEvidenceDrawer`)

The slide-over 640px forensic drawer provides an interactive evidence inspection experience:

1. **Overview Header**: Displays Execution ID, Scenario Name, Target URL, Client IP, Timestamps, and verified duration.
2. **Step Traces Timeline**: Scrollable list of every probe packet with latency and color-coded status codes.
3. **Detection & Quarantine Verdict**: Expected vs actual rules, dual-probe verdict, and clickable incident link.
4. **Safely-Escaped Raw JSON Artifact**: Formatted JSON code block using `.textContent` to guarantee zero XSS vulnerability from unescaped payload strings.

---

### 5. Export Capabilities & Integrity Protection

#### 5.1 Formula-Safe CSV Export
When exporting via `GET /api/security/simulations?format=csv`, the API prevents CSV formula injection attacks (CWE-1236). Any text cell starting with `=`, `+`, `-`, or `@` is prepended with a single quote (`'`):

```python
def clean_cell(val):
    s = str(val or "")
    if s and s[0] in ("=", "+", "-", "@"):
        return "'" + s
    return s
```

#### 5.2 JSON Dossier Export
The drawer footer features an **Export JSON** control (`exportSimulationDossierJson()`) allowing tier-3 SOC investigators to download signed evidence dossiers as `.json` files for external SIEM/SOAR ingestion or compliance archiving.
