# AutoHeal Phase 8: Relationship and Correlation Model

## 1. Overview

The AutoHeal graph architecture models relationships as directional, typed edges between security entities. To maintain strict investigative integrity, the engine differentiates between **Confirmed** relationships (established by relational keys or verified rule triggers) and **Inferred** relationships (derived from statistical, temporal, or spatial correlation).

```
+-----------------------------------------------------------------------------------------+
|                              EDGE CORRELATION CLASSIFICATION                            |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   [CONFIRMED EDGE - Solid Vector]                                                       |
|   Source Entity ================================================> Target Entity         |
|   Direct Foreign Key / Exact Event Match / Deterministic Execution Trace                |
|   Render: Solid Line (width: 2.0), Particle Flow Animation, High Glow                      |
|                                                                                         |
|   [INFERRED EDGE - Dashed Vector]                                                       |
|   Source Entity - - - - - - - - - - - - - - - - - - - - - - - - > Target Entity         |
|   Temporal Clustering (Delta T < 60s) / Subnet Proximity / Behavioral Similarity        |
|   Render: Dashed Line (dashSize: 3, gapSize: 2), Muted Purple (#818CF8)                 |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Edge Relationship Taxonomy

The engine models 7 primary relationship types:

| Relationship Type | Source Entity | Target Entity | Confidence Logic | Render Style |
| :--- | :--- | :--- | :--- | :--- |
| `TARGETS` | `SOURCE_IP` | `TARGET_ENDPOINT` | Direct HTTP request trace in `security_events` | Solid Cyan (`#38BDF8`) |
| `VIOLATES` | `SECURITY_EVENT` | `DETECTION_RULE` | Event triggered WAF/AppSec rule pattern | Solid Violet (`#A78BFA`) |
| `GENERATED` | `DETECTION_RULE` | `SECURITY_INCIDENT` | Incident created by rule violation threshold | Solid Rose (`#F43F5E`) |
| `BELONGS_TO` | `SECURITY_EVENT` | `SECURITY_INCIDENT` | Foreign key `security_events.correlation_id` | Solid Blue (`#60A5FA`) |
| `MITIGATES` | `REMEDIATION_ACTION` | `SECURITY_INCIDENT` | Execution targeting incident in `self_healing` | Solid Emerald (`#22C55E`) |
| `VERIFIES` | `VERIFICATION_PROBE` | `REMEDIATION_ACTION`| Post-repair synthetic health verification | Solid Sky (`#38BDF8`) |
| `CORRELATED_WITH` | `SOURCE_IP` / `EVENT` | `SOURCE_IP` / `EVENT` | Heuristic temporal/subnet correlation | Dashed Indigo (`#818CF8`) |

---

## 3. Mathematical & Algorithmic Correlation Models

### 3.1 Confirmed Linkage Rules
An edge is marked as `CONFIRMED` if and only if one of the following deterministic conditions is satisfied:
1. **Direct Event-to-Incident Linkage**:
   $$\text{security\_events.correlation\_id} = \text{security\_incidents.incident\_id}$$
2. **Deterministic Remediation Association**:
   $$\text{self\_healing\_executions.incident\_id} = \text{security\_incidents.incident\_id}$$
3. **Exact Rule Evaluation**:
   $$\text{security\_events.event\_type} = \text{detection\_rules.rule\_id}$$
4. **Verified Verification Probe**:
   $$\text{verification\_probes.execution\_id} = \text{self\_healing\_executions.execution\_id}$$

### 3.2 Inferred Linkage Heuristics
When explicit foreign keys are not populated, the engine executes three heuristic correlation passes:

#### A. Temporal Attack Window Clustering
Two events $E_1, E_2$ originating from the same class C subnet ($/24$) targeting identical or adjacent endpoints within time delta $\Delta t \le 60\text{ seconds}$ receive an inferred relationship:

$$\text{CorrelationScore}(E_1, E_2) = w_t \cdot \max\left(0, 1 - \frac{|t_1 - t_2|}{\Delta t_{\max}}\right) + w_s \cdot \text{SubnetMatch}(IP_1, IP_2)$$

Where weights $w_t = 0.6$, $w_s = 0.4$. If $\text{CorrelationScore} \ge 0.70$, an inferred edge `CORRELATED_WITH` is established.

#### B. Co-Targeted Endpoint Clustering
When multiple source IPs target the same endpoint within an active incident window, inferred edges connect those IPs to the primary `SECURITY_INCIDENT` with confidence:

$$\text{Confidence}_{\text{inferred}} = 0.65 \times \left(\frac{\text{EventCount}_{\text{IP}}}{10}\right)$$

Clamped to $[0.30, 0.75]$.

---

## 4. Edge Schema Specification

Edges returned by `/api/threat-topology/graph` conform to the following schema:

```json
{
  "id": "EDGE-IP-198.51.100.99->EP-cart",
  "source": "IP-198.51.100.99",
  "target": "EP-/api/cart",
  "type": "TARGETS",
  "status": "CONFIRMED",
  "style": "solid",
  "weight": 14,
  "color": "#38BDF8",
  "metadata": {
    "first_seen": "2026-11-01T15:10:02",
    "last_seen": "2026-11-01T15:24:19",
    "http_methods": ["GET", "POST"],
    "status_codes": [403, 200]
  }
}
```

---

## 5. Force-Directed Layout Stabilization

To maintain real-time performance without client-side physics lag, spatial coordinates are computed server-side in `threat_topology_models.py`:
1. **Angular Distribution**: Nodes in each orbital layer are spaced uniformly using polar coordinates:
   $$\theta_i = \frac{2\pi \cdot i}{N_{\text{layer}}} + \phi_{\text{offset}}$$
2. **Radial Offsets**: Jitter ($r \pm 5$) is introduced to prevent collinear overlap.
3. **Elevation Constraints**: $Z$-coordinates strictly reflect severity, allowing visual slicing of high-impact attack vectors.
