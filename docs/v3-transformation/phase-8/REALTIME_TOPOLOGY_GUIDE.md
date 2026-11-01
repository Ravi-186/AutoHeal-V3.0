# AutoHeal Phase 8: Real-Time Topology Operator Guide

## 1. Overview

The AutoHeal 3D Threat Topology module features bidirectional telemetry streaming and interactive 3D spatial manipulation. This guide provides SOC analysts and operators with instructions for interacting with the 3D scene, consuming live Server-Sent Events (SSE), utilizing camera controls, and stepping through chronological attack sequences.

---

## 2. Real-Time Telemetry Streaming (SSE)

### 2.1 Connection Architecture
The client connects to `/api/threat-topology/stream` using the standard browser `EventSource` API:

```javascript
const sse = new EventSource('/api/threat-topology/stream');

sse.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'INIT':
            // Initial full graph hydrate
            initialize3DGraph(data.graph);
            break;
        case 'EVENT_APPEND':
            // New security event ingested; add node and edge
            handleLiveEvent(data.event);
            break;
        case 'INCIDENT_UPDATE':
            // Incident status or severity transitioned
            updateNodeState(data.incident);
            break;
        case 'REMEDIATION_TRIGGERED':
            // Autonomous remediation commenced
            spawnRemediationNode(data.remediation);
            break;
        case 'HEARTBEAT':
            // Connection keepalive
            updateStreamHeartbeat(data.timestamp);
            break;
    }
};
```

### 2.2 Reconnection & Backoff Policy
If the SSE connection drops due to network blips or server restarts:
1. Client automatically attempts reconnection after 3 seconds.
2. Exponential backoff is applied ($3\text{s} \to 6\text{s} \to 12\text{s} \dots \max 30\text{s}$).
3. A HUD banner displays connection health (`CONNECTED`, `RECONNECTING`, `OFFLINE`).

---

## 3. Interactive Camera & Navigation Controls

### 3.1 Mouse and Touch Controls
The 3D canvas is equipped with enhanced `THREE.OrbitControls`:

| Action | Mouse Gesture | Touch Gesture |
| :--- | :--- | :--- |
| **Orbit / Rotate** | Left-Click + Drag | Single-finger drag |
| **Pan / Translate** | Right-Click + Drag (or Shift + Left Drag) | Two-finger swipe |
| **Dolly / Zoom** | Mouse Scroll Wheel | Two-finger pinch |
| **Inspect Entity** | Left-Click on node geometry | Single tap on node |
| **Deselect** | Left-Click on empty canvas space | Single tap on empty space |

### 3.2 Keyboard Navigation Shortcuts

| Key | Action | Description |
| :---: | :--- | :--- |
| `R` | **Reset Camera** | Restores default isometric perspective $[X: 180, Y: 140, Z: 240]$ |
| `F` | **Focus Selected** | Smooth-dollies camera to center on the active selected entity |
| `Space` | **Pause / Resume** | Toggles real-time particle animation and node rotation pulses |
| `Escape` | **Deselect** | Clears entity selection and closes Inspector Drawer |
| `1` - `5` | **Filter Severity** | Filters graph: 1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW, 5=ALL |
| `T` | **Toggle 2D View** | Switches between 3D WebGL viewport and 2D Accessible Ledger |

---

## 4. Entity Inspector Drawer

When an analyst clicks any node, the right-hand **Inspector Drawer** animates open:

```
+-------------------------------------------------------------+
| ENTITY INSPECTOR                                        [X] |
+-------------------------------------------------------------+
| Entity ID:        IP-198.51.100.99                          |
| Entity Type:      SOURCE_IP                                 |
| Current Severity: CRITICAL                                  |
| Status:           BLOCKED (Active Firewall Drop)            |
+-------------------------------------------------------------+
| ATTRIBUTION & THREAT INTELLIGENCE                           |
| AbuseIPDB Score:  94% Confidence (Known Botnet Scanner)     |
| Geolocation:      United States (AS13335)                   |
| MITRE Technique:  T1190 - Exploit Public-Facing Application |
+-------------------------------------------------------------+
| ASSOCIATED ACTIONS                                          |
| [Investigate in Copilot]    [Trigger Full SOAR Playbook]    |
+-------------------------------------------------------------+
```

Clicking **"Investigate in Copilot"** immediately transfers the entity context into the AI SOC Copilot module with pre-populated evidence dossiers.

---

## 5. Attack Sequence Timeline Traversal

The collapsible timeline tray at the bottom of the screen enables chronological playback of complex multi-stage attacks:

1. **Step Indicator**: Displays current step (e.g., `Step 3 of 6: WAF Rule SQLI-001 Blocked Payload`).
2. **Previous / Next Controls**: Steps forward and backward through telemetry.
3. **Auto-Play**: Automatically traverses the attack timeline at 2-second intervals.
4. **Camera Synchronization**: At each step, the 3D camera smoothly flies to and focuses on the entity executing or receiving the action.
