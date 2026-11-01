# AutoHeal Phase 7: Explainable Risk and Impact Assessment Model

## 1. Overview
The Self-Healing Command Center employs a deterministic, transparent, and explainable 4-vector risk evaluation model. In high-stakes enterprise SOC environments, remediation actions cannot rely on opaque, non-deterministic heuristics to decide when an automated system may modify code, firewall rules, or user session state. Every proposed remediation plan is scored across four orthogonal impact vectors to produce an aggregate score, an associated risk level, and a human-readable justification.

---

## 2. The 4-Vector Scoring Dimensions

The overall risk score is calculated as:
$$\text{Total Score} = \text{Severity} + \text{Scope} + \text{Reversibility} + \text{Collateral Impact}$$

The resulting score ranges from 4 to 14, mapped deterministically to four risk tiers:
- **LOW**: Score $4 - 6$ (Safe for autonomous execution under Level 1+)
- **MEDIUM**: Score $7 - 9$ (Autonomous under Level 2+ if under policy threshold)
- **HIGH**: Score $10 - 12$ (Requires dual-operator or manual confirmation under Level 2)
- **CRITICAL**: Score $13 - 14$ (Always requires explicit human authorization under Level 0–2)

### Vector 1: Threat Severity ($V_{sev} \in [1, 4]$)
Measures the intrinsic threat severity of the targeted vulnerability or security incident:
- **1 (Low)**: Information disclosure, reconnaissance, non-exploitable anomaly.
- **2 (Medium)**: Targeted scanning, low-impact parameter fuzzing, authenticated endpoint abuse.
- **3 (High)**: Active brute force, rate-limit evasion, SQL injection attempts, stored XSS.
- **4 (Critical)**: Confirmed remote code execution, active credential stuffing, database exfiltration.

### Vector 2: Operational Scope ($V_{scope} \in [1, 3]$)
Measures the blast radius and architectural tier targeted by the remediation:
- **1 (Narrow / Per-Entity)**: Affects a single remote IP address, single user session, or single auth token.
- **2 (Service / Route-Level)**: Applies rate limits to specific API routes or adjusts endpoint-specific firewall thresholds.
- **3 (Application-Wide)**: Involves live AST code patches, database schema changes, or core dependency restarts.

### Vector 3: Reversibility & Rollback Complexity ($V_{rev} \in [1, 4]$)
Measures the operational overhead and risk associated with reverting the remediation if it causes regression:
- **1 (Instant / Trivial)**: Ephemeral firewall block, in-memory rate limiter adjustment, unblock command.
- **2 (Simple / Non-Destructive)**: Database flag toggle, revoking an access token (re-authentication required).
- **3 (Moderate / Code Rollback)**: Git commit reversal, restoring a file from a pre-change snapshot.
- **4 (Complex / Irreversible)**: Permanent data deletion, schema drop, stateful credential rotation requiring customer intervention.

### Vector 4: User Collateral Impact ($V_{collat} \in [1, 3]$)
Measures the likelihood and degree of disruption experienced by legitimate end-users:
- **1 (Zero / Negligible)**: Malicious actor IP isolated; zero impact on legitimate users.
- **2 (Minor Inconvenience)**: Legitimate user must re-authenticate (session invalidation) or complete a CAPTCHA.
- **3 (Service Degradation)**: Temporary route throttling, minor API latency, or brief downtime during code redeployment.

---

## 3. Risk Mapping Matrix

| Plan Type | Target Scope | Threat Severity | Reversibility | Collateral Impact | Total Score | Risk Level | Autonomy Permitted |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `BLOCK_IP` (WAF) | Single IP (1) | Medium/High (2-3) | Instant (1) | Zero (1) | **5 - 6** | **LOW** | Level 1, 2, 3 |
| `APPLY_RATE_LIMIT` | Route (2) | High (3) | Instant (1) | Minor (2) | **8** | **MEDIUM** | Level 2, 3 |
| `REVOKE_SESSION` | Single User (1) | High/Crit (3-4) | Simple (2) | Minor (2) | **8 - 9** | **MEDIUM** | Level 2, 3 |
| `CODE_REPAIR_PATCH` | Codebase (3) | Critical (4) | Snapshot (3) | Minor/None (1-2) | **11 - 12** | **HIGH** | Level 3 (or Approved) |
| `SYSTEM_LOCKDOWN` | Global (3) | Critical (4) | Complex (4) | High (3) | **14** | **CRITICAL** | Level 3 only (Strict) |

---

## 4. Explainable Risk Reporting

Every calculated risk assessment emits an explainable justification payload stored in `self_healing_executions.risk_level` and detailed JSON payload.

### Example Justification Output
```json
{
  "total_score": 11,
  "level": "HIGH",
  "vectors": {
    "severity": 4,
    "scope": 3,
    "reversibility": 3,
    "collateral_impact": 1
  },
  "rationale": "High-risk AST code remediation targeting SQL injection in /api/products. Scope spans application codebase requiring snapshot reversal; collateral impact on legitimate users is low due to localized parameterization."
}
```

This explainable breakdown ensures that SOC analysts, compliance auditors, and automated approval engines can immediately understand *why* a remediation was categorized at a specific risk tier before authorization.
