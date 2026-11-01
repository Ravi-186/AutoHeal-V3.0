# AutoHeal v3.0 — Phase 2: Security Analytics & Visualization Implementation

**Document Version:** 3.0.0  
**Status:** Certified & Implemented  
**Author:** Data Visualization Architect & Senior Frontend Engineer  
**Component Scope:** `#pageOverview` Analytics Rows 1, 2, and 3

---

## 1. Overview & Visualization Philosophy

Phase 2 replaces the legacy dashboard's static mockups and randomized line chart with 6 real analytical visualizations:

1. **Security Event Volume Timeline:** Uniform 12-slice temporal bucketing with category and severity filtering.
2. **Threat Severity Distribution Doughnut:** Dual-mode breakdown (Events vs Incidents) with monospace count counters.
3. **Autonomous Incident Lifecycle Pipeline:** 7-stage connected flow tracking incident progression from detection to verified resolution.
4. **Detection Rule Distribution Matrix:** Live tabular coverage across all 7 operational detection rules mapped to MITRE ATT&CK techniques.
5. **Remediation & Patch Verification Analytics:** High-impact success percentage gauge with zero-false-fix accounting.
6. **Autonomous Self-Healing Status:** Independent dual-probe verification panel displaying perimeter quarantine (403) and customer availability (200 OK).

---

## 2. Visualization 1: Security Event Volume Timeline

### Architecture & Bucketing Engine
The timeline chart binds to `<canvas id="securityEventTimelineCanvas"></canvas>`. Rather than relying on browser-side synthetic points, it requests aggregated time slices from `/api/security/analytics/timeline`.

```
[Start Timestamp: T0] --------------------------------------------- [End Timestamp: T1]
      |               |               |               |               |
   Slice 1         Slice 2         Slice 3         Slice 4         Slice 12
  [Count, Sev]    [Count, Sev]    [Count, Sev]    [Count, Sev]    [Count, Sev]
```

### Dynamic Filters:
- **Category Filter (`#timelineCategorySelect`):**
  - `ALL`: All security event categories.
  - `INJ`: SQL Injection (`INJ-001`).
  - `AUTH`: Credential stuffing & brute force (`AUTH-001`).
  - `XSS`: Cross-site scripting (`XSS-001`).
  - `RATE`: Request rate anomalies (`RATE-001`).
- **Severity Filter (`#timelineSeveritySelect`):**
  - `ALL`, `CRITICAL`, `HIGH`, `MEDIUM`, `INFO`.

### Chart.js Configuration Tokens:
- **Type:** `line`
- **Border Color:** `#00d4ff` (Obsidian Cyan)
- **Gradient Fill:** `rgba(0, 212, 255, 0.28)` to `rgba(0, 212, 255, 0.01)`
- **Tension:** `0.35` (smooth cubic interpolation)
- **Point Radius:** `3px` with `#070b14` border ring, expanding to `5px` on hover.
- **Tooltips:** Custom Obsidian Sentinel tooltip with `JetBrains Mono` bold numeric typography.

---

## 3. Visualization 2: Threat Severity Distribution

### Dual-Mode Toggle (`#sevModeEventsBtn` / `#sevModeIncidentsBtn`)
Security analysts can toggle the doughnut chart between two perspectives:
1. **Raw Telemetry Events Mode (`events`):** Displays severity distribution of all raw HTTP security events (predominantly INFO and MEDIUM).
2. **Correlated Incidents Mode (`incidents`):** Displays severity distribution of actionable security incidents (predominantly CRITICAL and HIGH).

### Visual Structure & Palette:
- **Cutout Ratio:** `72%` (thin elegant ring).
- **Severity Colors:**
  - `Critical`: `#ef4444` (Ruby Red)
  - `High`: `#f59e0b` (Amber)
  - `Medium`: `#00d4ff` (Cyan)
  - `Low`: `#22c55e` (Emerald)
  - `Info`: `#64748b` (Slate Gray)
- **Tabular Monospace Counter Bar (`#severityBreakdownNumbers`):**
  Displays exact numeric counts under the chart with tabular font alignment.

---

## 4. Visualization 3: Autonomous Incident Lifecycle Pipeline

The 7-stage pipeline visualizes the progression of incidents through AutoHeal's autonomous defense stages:

```
[1. New] ➔ [2. Triaged] ➔ [3. Investigating] ➔ [4. Containment] ➔ [5. Remediate] ➔ [6. Verify] ➔ [7. Resolved]
```

### Stage Definitions & Database Mapping:

| Stage ID | Title | CSS ID | Active Condition | DB State Mapping |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | New | `#stageStepNew` | Count > 0 | `status IN ('OPEN', 'NEW')` |
| **Stage 2** | Triaged | `#stageStepTriaged` | Count > 0 | Initial rule correlation executed |
| **Stage 3** | Investigating | `#stageStepInvestigating` | Count > 0 | `status = 'INVESTIGATING'` |
| **Stage 4** | Containment | `#stageStepContainment` | Count > 0 | `status = 'CONTAINED'` |
| **Stage 5** | Remediate | `#stageStepRemediation` | Count > 0 | `status = 'REMEDIATED'` |
| **Stage 6** | Verify | `#stageStepVerification` | Count > 0 | `verification_status = 'PENDING'` |
| **Stage 7** | Resolved | `#stageStepResolved` | Count > 0 | `status IN ('RESOLVED', 'CLOSED')` |

Each step dynamically displays its active count in `#lifecycleCount<Stage>` and illuminates when active.

---

## 5. Visualization 4: Detection Rule Distribution Analysis

The Command Center provides a dedicated forensic table (`#detectionRulesTableBody`) displaying real-time coverage across all 7 production detection rules:

| Rule ID | Rule Name / Attack Vector | Category | Severity | MITRE Technique | Incident Count | Detection Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `INJ-001` | SQL Injection Attack | Injection | `CRITICAL` | `T1190` | 234 | 468 |
| `AUTH-001`| Credential Stuffing / Brute Force | Credential Access | `HIGH` | `T1110.001`| 103 | 206 |
| `XSS-001` | Cross-Site Scripting (XSS) | Client Execution | `HIGH` | `T1059.007`| 27 | 54 |
| `AUTH-002`| Unauthorized Admin Access Probe | Privilege Escalation | `HIGH` | `T1078` | 39 | 78 |
| `RATE-001`| Request-Rate Anomaly / Scraping | Denial of Service | `MEDIUM` | `T1499` | 41 | 82 |
| `CORR-001`| Multi-Step Attack Correlation | Advanced Threat | `CRITICAL` | `T1190/T1078` | 0 | 0 |
| `HEALTH-001`| Clustered Exception Cascade | Reliability Degradation | `HIGH` | `T1499.004`| 8 | 16 |

---

## 6. Visualization 5 & 6: Remediation & Self-Healing Status

### Remediation Analytics Card
- **Success Rate Gauge (`#remediationSuccessRateVal`):** Large tabular figure (42px, 900 weight, Emerald `#22c55e`).
- **Formula:**
  $$\text{Success Rate} = \frac{\text{Successful Fixes}}{\text{Successful Fixes} + \text{Failed Fixes} + \text{Rolled Back}} \times 100$$
- **Metric Tiles:** Successful Fixes (3), Verification Failures (37), Rolled Back Actions (1), Pending Approvals (1).

### Autonomous Self-Healing Status Card
- **Dual-Probe Status Panel:**
  - **Attacker Probe (`#healingAttackerProbeStatus`):** Displayed in red border box: `QUARANTINED (403 Forbidden)` with context *"Perimeter isolation confirmed"*.
  - **Benign Shopper Probe (`#healingBenignProbeStatus`):** Displayed in green border box: `UNIMPAIRED (200 OK)` with context *"Zero business disruption"*.
- **Last Verified Remediation Dossier:**
  - Displays Incident ID (`#healingLastIncidentId`, e.g. `INC-2026-0F493FFE`) and mitigation details (`#healingLastActionText`).

---

*Certified implemented with responsive Chart.js instances and real database queries.*
