# AutoHeal Phase 8: Graph Entity Schema & Taxonomy

## 1. Overview

The AutoHeal 3D Threat Topology categorizes all telemetry into an 8-entity normalized taxonomy. This specification details the properties, data sources, visual geometry, and color encodings for each entity type within the graph.

```
       [SOURCE_IP] ────(TARGETS)────> [TARGET_ENDPOINT] ────(HOSTED_ON)────> [AFFECTED_ASSET]
            │                                 │
      (GENERATED)                         (VIOLATES)
            ▼                                 ▼
    [SECURITY_EVENT] ──(TRIGGERED)──> [DETECTION_RULE]
            │                                 │
        (BELONGS_TO)                      (EVALUATES)
            ▼                                 ▼
   [SECURITY_INCIDENT] ──(MITIGATED_BY)──> [REMEDIATION_ACTION] ──(VERIFIED_BY)──> [VERIFICATION_PROBE]
```

---

## 2. Entity Taxonomy Specification

### 2.1 Entity Types Table

| Entity Type | Description | Primary Data Source | Three.js Geometry | Primary Color | Emissive Accent |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SOURCE_IP` | Originating client IP or threat actor address | `security_events.client_ip` | `OctahedronGeometry(6)` | `#F59E0B` (Amber) | `#EF4444` if blocked |
| `TARGET_ENDPOINT` | HTTP path / API route under attack | `security_events.path` | `CylinderGeometry(4, 4, 10)` | `#38BDF8` (Sky Blue) | `#0284C7` |
| `AFFECTED_ASSET` | Internal service, database, or container | Inferred / Architecture Map | `DodecahedronGeometry(7)` | `#22C55E` (Emerald) | `#15803D` |
| `DETECTION_RULE` | Security detection rule or WAF signature | `RULE_METADATA` | `BoxGeometry(8, 8, 8)` | `#A78BFA` (Violet) | `#7C3AED` |
| `SECURITY_EVENT` | Individual telemetry event or HTTP probe | `security_events` | `SphereGeometry(4)` | Severity Color | Matches Severity |
| `SECURITY_INCIDENT`| Aggregated correlated security incident | `security_incidents` | `IcosahedronGeometry(9)` | Severity Color | Pulsing Wireframe |
| `REMEDIATION_ACTION`| Self-healing execution or SOAR playbook | `self_healing_executions` | `TorusGeometry(6, 2.2, 16, 32)` | `#22C55E` (Emerald) | `#4ADE80` |
| `VERIFICATION_PROBE`| Post-heal verification synthetic test | `self_healing_executions` | `TetrahedronGeometry(5)` | `#38BDF8` (Cyan) | `#0EA5E9` |

---

## 3. Node Schema & Properties

Every node returned by `/api/threat-topology/graph` adheres to the following JSON schema:

```json
{
  "id": "IP-198.51.100.99",
  "label": "198.51.100.99",
  "type": "SOURCE_IP",
  "entity_type": "SOURCE_IP",
  "severity": "CRITICAL",
  "status": "BLOCKED",
  "position": {
    "x": 128.45,
    "y": -12.30,
    "z": 30.00
  },
  "color": "#EF4444",
  "degree": 8,
  "metadata": {
    "raw_id": "198.51.100.99",
    "threat_intel": {
      "reputation": "MALICIOUS",
      "abuse_score": 94,
      "asn": "AS13335 Cloudflare Test",
      "country": "US"
    },
    "enforcement_status": {
      "is_blocked": true,
      "blocked_at": "2026-11-01T15:20:10",
      "block_reason": "SQL Injection probe threshold exceeded"
    },
    "event_count": 14,
    "incident_ids": ["INC-1004", "INC-1007"]
  }
}
```

### Field Definitions

1. `id` (`string`, required): Unique graph identifier formatted with entity prefix (e.g., `IP-`, `EP-`, `ASSET-`, `RULE-`, `EVT-`, `INC-`, `REM-`, `VER-`).
2. `label` (`string`, required): Human-readable display label rendered on billboard text sprites in the 3D scene.
3. `type` / `entity_type` (`string`, required): One of the 8 canonical entity taxonomy strings.
4. `severity` (`string`, required): Normalized severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
5. `status` (`string`, required): Operational state (`OPEN`, `RESOLVED`, `BLOCKED`, `ALLOW`, `ACTIVE`, `VERIFIED`, `FAILED`).
6. `position` (`object`, required): Calculated spatial coordinates (`x`, `y`, `z`) in Three.js world units.
7. `color` (`string`, required): Primary hex color conforming to the Obsidian Sentinel palette.
8. `degree` (`integer`, required): Number of connected graph edges, used to scale node visual radius dynamically.
9. `metadata` (`object`, required): Entity-specific enrichment, including threat intelligence, firewall status, and relational IDs.

---

## 4. Visual Mesh Instantiation Rules

### 4.1 Materials
- **Standard Node Material**: `THREE.MeshStandardMaterial` configured with:
  - `roughness: 0.25`
  - `metalness: 0.80`
  - `emissiveIntensity: 0.45`
  - Dynamic opacity based on focus/filtering state ($1.0$ when active, $0.25$ when dim).

### 4.2 Status Glow & Rings
- **Blocked Entities**: Rendered with an outer red wireframe sphere (`THREE.WireframeGeometry`) that slowly pulses in scale ($1.0 \to 1.15 \to 1.0$).
- **Active Remediation**: Rendered with a rotating emerald outer torus indicating active containment or self-healing.
- **Critical Incidents**: Emissive pulse frequency is synchronized to severity level (Critical: 2.0 Hz; High: 1.0 Hz; Medium: 0.5 Hz).
