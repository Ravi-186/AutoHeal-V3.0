# AutoHeal Phase 8: 3D Threat Topology Architecture

## 1. Executive Overview

The **3D Threat Topology** module (`/threat-topology`) provides an interactive, spatial security visualization engine built on Three.js and WebGL. It transforms multi-dimensional security telemetry—scattered across access logs, WAF alerts, correlation rules, incident states, and automated remediations—into an intuitive, navigable 3D graph.

Security analysts can dynamically inspect relationships between external attack sources, vulnerable endpoints, targeted internal microservices, active firewall rules, confirmed incidents, and autonomous remediation actions in real time.

```
+---------------------------------------------------------------------------------------+
|                                3D THREAT TOPOLOGY ENGINE                              |
+---------------------------------------------------------------------------------------+
|  +--------------------+   +-----------------------+   +----------------------------+  |
|  |   SQLite Database  |   |   SSE Realtime Stream |   |  Three.js WebGL Viewport   |  |
|  |--------------------|   |-----------------------|   |----------------------------|  |
|  | - security_events  |-->| - /api/threat-topology|-->| - Scene, Camera, Light    |  |
|  | - security_incidents   |   /stream             |   | - 8-Entity Taxonomy Meshes |  |
|  | - self_healing     |   | - Dynamic delta-push  |   | - Solid & Dashed Edges     |  |
|  | - blocked_clients  |   | - Heartbeat & event   |   | - Force Orbit Layout       |  |
|  +--------------------+   +-----------------------+   +----------------------------+  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Architectural Pillars

### 2.1 Zero-Fabrication Telemetry Guarantee
Every single node and edge rendered within the 3D topology is derived from verified SQLite database records (`security_events`, `security_incidents`, `self_healing_executions`, `soar_executions`, `blocked_clients`, and `RULE_METADATA`). No nodes are synthesized, hallucinated, or mocked. If an entity appears in the viewport, it represents a tangible event or resource in the AutoHeal / ShopSphere runtime.

### 2.2 Dual-Style Edge Semantics (Confirmed vs Inferred)
- **Confirmed Edges (Solid Lines)**: Directly established by relational keys, explicit event-to-incident linkages, or deterministic rule triggers. Rendered as vibrant solid lines with particle flow animations.
- **Inferred Edges (Dashed Lines)**: Formed through probabilistic heuristics, temporal clustering (events from the same subnet within a 60-second window), or behavioral similarity. Rendered with distinct dash patterns and muted purple tones to prevent analyst confusion.

### 2.3 Layered Orbital Spatial Coordinate System
To prevent node occlusion and hairball clustering, entities are positioned according to a 3-layer cylindrical orbital layout:
- **Layer 0 (Core: $Y \in [-30, 30], R \in [0, 40]$)**: Incidents, Affected Assets, and Self-Healing Remediations.
- **Layer 1 (Perimeter: $Y \in [-50, 50], R \in [60, 100]$)**: Target Endpoints and Detection Rules.
- **Layer 2 (External: $Y \in [-80, 80], R \in [120, 180]$)**: External Threat Source IPs and Raw Security Events.

Node elevation ($Z$-axis) is modulated by severity: Critical ($+30$), High ($+15$), Medium ($0$), Low ($-15$), and Info ($-30$).

---

## 3. WebGL Scene Lifecycle & Subsystems

### 3.1 Scene Hierarchy & Illumination
- **Renderer**: `THREE.WebGLRenderer` configured with antialiasing, logarithmic depth buffering, and tone mapping matching the Obsidian Sentinel palette (`#090D14` background clear color).
- **Illumination Model**:
  - Ambient Light: Low-intensity ambient fill (`#151F2C`, intensity 0.8) ensuring non-lit faces remain legible.
  - Directional Sun: Primary overhead directional light (`#38BDF8`, intensity 1.2) casting crisp highlights on crystalline node geometries.
  - Point Highlights: Dynamic point lights placed at the centroids of CRITICAL incident clusters to produce localized threat blooms.

### 3.2 Raycasting & Interactive Selection
- Analysts interact with the topology using mouse clicks or touch taps. A `THREE.Raycaster` projects screen coordinates into 3D clip space, calculating intersections against interactive node meshes.
- Upon entity selection:
  1. The selected node pulses with an expanded emissive wireframe shell.
  2. The camera smooth-pans towards the entity using cubic easing.
  3. The right-hand **Entity Inspector Drawer** slides out, displaying real-time database attributes, MITRE ATT&CK mappings, recent event logs, and enforcement status.
  4. Non-connected nodes and edges reduce opacity to 25%, spotlighting the local attack subgraph.

### 3.3 Attack Sequence Timeline Engine
The module includes a chronological step-by-step attack traversal engine:
1. Gathers all security events and mitigations tied to the selected incident ordered by `timestamp ASC`.
2. Steps the analyst sequentially through the attack lifecycle (Initial Recon -> Probe -> Exploit Detection -> WAF Block -> Autonomous Patch -> Verification).
3. Automatically transitions the 3D camera to focus on each participating entity as the step is advanced.

---

## 4. Obsidian Sentinel Visual Integration

The 3D canvas adheres strictly to the **Obsidian Sentinel** color system:
- **Canvas Backdrop**: Deep Abyss `#090D14` with subtle radial gradient.
- **Grid Plane**: Subdued reference grid in `#151F2C` at $Y = -100$.
- **Nodes**:
  - `SOURCE_IP`: Glowing Orange/Red Octahedron (`#F59E0B` / `#EF4444`).
  - `TARGET_ENDPOINT`: Cyan Cylindrical Capsule (`#38BDF8`).
  - `AFFECTED_ASSET`: Emerald Dodecahedron (`#22C55E`).
  - `DETECTION_RULE`: Violet Box (`#A78BFA`).
  - `SECURITY_INCIDENT`: Pulsing Icosahedron colored by severity.
  - `REMEDIATION_ACTION`: Bright Emerald Torus (`#22C55E`).
  - `VERIFICATION_PROBE`: Sky Blue Sphere (`#38BDF8`).
- **Edges**:
  - Confirmed: Solid lines in `#38BDF8` (Event), `#22C55E` (Remediation), `#A78BFA` (Rule).
  - Inferred: Dashed lines in `#818CF8`.

---

## 5. Fallback & Low-Capability Mode

For environments where WebGL is unsupported, disabled, or underperforming (< 20 FPS), the system provides an accessible **2D Security Ledger View**:
- Tabular matrix of all entities with sortable columns: Entity ID, Type, Severity, Source IP, Target, Status, and Actions.
- Real-time updates mirrored identically from the same REST and SSE streams.
- Full ARIA accessibility and screen-reader compatibility.
