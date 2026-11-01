# AutoHeal Phase 8: Evidence Retrieval and Grounding Engine

## 1. Overview

In autonomous and AI-assisted security operations, hallucinated findings create dangerous operational noise and misallocated analyst bandwidth. The AutoHeal **Evidence Retrieval and Grounding Engine** guarantees that all AI Copilot analyses are anchored to empirical database telemetry.

Every assertion emitted by the Copilot includes traceable citations referencing specific database records, timestamps, and parameters.

---

## 2. Seven-Source Telemetry Retrieval Pipeline

When an analyst opens an incident or initiates a chat investigation, the `EvidenceRetriever` queries 7 authoritative tables:

```
+-----------------------------------------------------------------------------------------+
|                                7-SOURCE TELEMETRY PIPELINE                              |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [1. security_incidents]      [2. security_events]        [3. self_healing_executions]  |
|  - Title, severity, status    - Raw HTTP method, path     - Applied patches             |
|  - Confidence, MITRE ID       - Status code, client IP    - Verification results        |
|  - Affected endpoints         - Action taken, headers     - Rollback status             |
|                                                                                         |
|  [4. soar_executions]          [5. blocked_clients]       [6. RULE_METADATA]            |
|  - Triggered playbooks        - Firewall drops            - CVEs, CWE references        |
|  - Node execution traces      - Expiration timestamps     - Detection patterns          |
|                                                                                         |
|                               [7. threat_intel]                                         |
|                               - AbuseIPDB reputation                                    |
|                               - Geolocation, ASN data                                   |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Evidence Normalization & Citation Architecture

### 3.1 Citation Object Schema
Each grounded evidence item generates a structured citation:

```json
{
  "id": "EVT-1004",
  "type": "EVENT",
  "source_field": "security_events",
  "timestamp": "2026-11-01T15:20:10",
  "claim": "GET /api/cart -> HTTP 403 (BLOCKED)"
}
```

### 3.2 Citation Types
- `INCIDENT`: Root incident record (`security_incidents`).
- `EVENT`: Individual network request or probe (`security_events`).
- `REMEDIATION`: Autonomous patch or self-healing execution (`self_healing_executions`).
- `SOAR`: Automated response playbook execution (`soar_executions`).
- `INTEL`: Threat intelligence reputation score (`threat_intel`).

---

## 4. Separation of Facts vs Hypotheses

The engine strictly partitions investigative findings into two distinct categories:

### 4.1 Confirmed Facts (`facts`)
Statements that can be proven via direct database queries. For example:
- "Client IP `198.51.100.99` submitted 14 requests to `/api/cart` resulting in HTTP 403."
- "WAF Rule `SQLI-001` triggered on payload `' OR 1=1--`."
- "Firewall blocked client IP at 2026-11-01 15:20:12."

### 4.2 Investigative Hypotheses (`hypotheses`)
Inferences, potential attack objectives, or speculative risks that require manual human validation or further investigation. For example:
- "The attacker is likely scanning for unauthenticated second-order SQL injection vulnerabilities."
- "Adjacent IPs in `198.51.100.0/24` may belong to the same automated vulnerability scanner infrastructure."

Each hypothesis is assigned a confidence metric and an explicit warning indicating that it represents an inferred hypothesis, not an established fact.

---

## 5. Mathematical Confidence Scoring Model

The Copilot calculates a calibrated confidence score $C \in [0.0, 1.0]$ for each investigation:

$$C = \min\left(1.0, \; w_e \cdot \min\left(1.0, \frac{N_{\text{events}}}{10}\right) + w_i \cdot C_{\text{incident}} + w_v \cdot V + w_t \cdot T\right)$$

Where:
- $w_e = 0.30$: Weight for event volume ($N_{\text{events}}$ is the count of linked events).
- $w_i = 0.35$: Weight for baseline incident detection confidence ($C_{\text{incident}}$ from rule engine).
- $w_v = 0.20$: Verification weight ($V = 1.0$ if post-heal verification passed; $0.5$ if pending; $0.0$ if failed).
- $w_t = 0.15$: Threat intel weight ($T = \text{AbuseScore} / 100$).

### Confidence Tiers
- **$\ge 0.85$ (CRITICAL CONFIDENCE)**: Direct telemetry match, high threat reputation, verified remediation.
- **$0.70 - 0.84$ (HIGH CONFIDENCE)**: Solid event logs and rule triggers; verification pending.
- **$0.50 - 0.69$ (MODERATE CONFIDENCE)**: Partial event telemetry, heuristic correlation.
- **$< 0.50$ (LOW / ADVISORY)**: Sparse telemetry; manual triage required.
