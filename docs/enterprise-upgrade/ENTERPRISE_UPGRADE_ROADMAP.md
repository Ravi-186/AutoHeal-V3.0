# AutoHeal: Enterprise Upgrade Roadmap

**Author:** Principal Software Architect & Program Management Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `ROADMAP-001`  

---

## 1. Upgrade Strategy & Phase Alignment

This roadmap translates the findings from the Initial Enterprise Audit into a staged engineering execution plan. In accordance with the project's absolute engineering rules, every stage preserves working functionality, maintains backward compatibility, introduces regression tests for all fixes, and validates implementations with concrete evidence.

```mermaid
gantt
    title AutoHeal Enterprise Modernization Roadmap
    dateFormat  YYYY-MM-DD
    section Discovery & Baseline
    Stage 1: Discovery & Inventory       :done, s1, 2026-11-01, 1d
    Stage 2: Baseline Builds & Tests     :done, s2, 2026-11-01, 1d
    section Stabilization & Security
    Stage 3: Security & Auth Hardening   :active, s3, 2026-11-01, 1d
    Stage 4: Prioritized Bug Fixing      :s4, 2026-11-01, 1d
    Stage 5: Database Optimization       :s5, 2026-11-02, 1d
    section SOC Core Capabilities
    Stage 6: API & Metrics Clean-Up      :s6, 2026-11-02, 1d
    Stage 7: Detection & Telemetry       :s7, 2026-11-02, 1d
    Stage 8: Incident Lifecycle          :s8, 2026-11-03, 1d
    Stage 9: SOAR & Self-Healing Engine  :s9, 2026-11-03, 1d
    section Presentation & Verification
    Stage 10: AI Advisor & MITRE ATT&CK  :s10, 2026-11-03, 1d
    Stage 11: Performance & Observability:s11, 2026-11-04, 1d
    Stage 12: End-to-End Regression      :s12, 2026-11-04, 1d
    Stage 13: Final Certification        :s13, 2026-11-04, 1d
```

---

## 2. Detailed Stage Execution Plans

### STAGE 1 & 2: Discovery, Inventory & Baseline Builds
- **Status:** **COMPLETED**
- **Deliverables:**
  - Complete file, API, database, and feature inventories.
  - Installed missing dependencies (`fastapi`, `plotly`, `pytest`, `coverage`) in `.venv`.
  - Initial Git repository initialized on `enterprise-upgrade` branch.
  - Verified 68/68 passing unit and integration tests.

---

### STAGE 3: Security Hardening & Authorization
- **Focus:** Eliminate critical security vulnerabilities.
- **Tasks:**
  1. Remove hardcoded backdoor token `token_admin_shopsphere_secret` from `shopsphere/api.py` and `database.py`.
  2. Implement database-backed role-based access control (RBAC) supporting `admin`, `analyst`, and `customer` roles.
  3. Enforce authorization dependencies on sensitive SOC APIs (`/api/security/unblock`, `/api/device/*/block`, `/api/security/vulnerabilities/*`).
  4. Restrict CORS to authorized enterprise origins.
  5. Add regression tests validating that unauthenticated access to admin and SOC endpoints is properly blocked with HTTP 401/403.

---

### STAGE 4: Prioritized Defect Remediation
- **Focus:** Fix functional defects discovered during audit.
- **Tasks:**
  1. Fix `PostureScorer` import mismatch in `dashboard/app.py` so real security posture scores render dynamically.
  2. Consolidate duplicate export endpoint definitions in `src/appsec/api.py`.
  3. Implement full functional body for `replay_attack_comparison` in `src/appsec/api.py`.
  4. Update `verifier.py` to allow optional in-memory ASGI client passing for zero-socket CLI verification.
  5. Run regression suite after each fix.

---

### STAGE 5: Database & Data Integrity Optimization
- **Focus:** Performance indexing and transactional atomicity.
- **Tasks:**
  1. Add composite indexes on `security_events`, `blocked_clients`, and `security_incidents`.
  2. Wrap multi-entity checkouts in explicit database transactions to guarantee stock consistency.
  3. Add table migration helper to safely add any missing columns or indexes without losing existing records.

---

### STAGE 6: Removal of Metric Fabrication & API Modernization
- **Focus:** Ensure 100% genuine data telemetry (Rule 6).
- **Tasks:**
  1. Replace `len(devices) * 1152 + 14` with true monitored asset counts.
  2. Eliminate hardcoded `"remediation_time_ms": 842` and synthetic `+ 12` ms latency additions; record true nanosecond monotonic durations (`time.perf_counter()`).
  3. Dynamically calculate `"average_remediation_ms"` in `/api/security/metrics` from real database records.
  4. Ensure all dashboard metrics reflect actual database rows.

---

### STAGE 7 - 9: Threat Detection, Incident Management & Self-Healing Verification
- **Focus:** Deepen SOC capabilities.
- **Tasks:**
  1. Standardize normalized event envelope schema.
  2. Formalize incident lifecycle states: `NEW -> TRIAGED -> INVESTIGATING -> CONTAINMENT -> REMEDIATION -> VERIFICATION -> RESOLVED`.
  3. Implement verifiable closed-loop remediation playbooks:
     - IP Quarantine
     - Session Revocation
     - Cart Logic Healing
     - Feature Rollback
  4. Require independent verification pass before marking any incident remediated.

---

### STAGE 10 - 13: Presentation, Verification & Production Certification
- **Focus:** End-to-end integration, performance, and documentation.
- **Tasks:**
  1. Verify Streamlit 3D Command Center live telemetry with real posture score.
  2. Run end-to-end simulation from ShopSphere exploit -> AutoHeal detection -> WAF block -> probe verification -> PDF report generation.
  3. Conduct load benchmark measuring throughput and query latency.
  4. Compile final enterprise report `AUTOHEAL_ENTERPRISE_TRANSFORMATION_REPORT.md`.
