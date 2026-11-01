# AutoHeal v3.0 — Phase 3: Live Threat Center Design Specification

## Executive Summary

The **Live Threat Center** is the central operational telemetry and real-time defense monitoring cockpit of the AutoHeal v3.0 enterprise platform. Built upon the **Obsidian Sentinel** visual system, it bridges low-level application telemetry with autonomous cyber-defense workflows.

Unlike standard static SIEM dashboards or simulated demonstration screens, the AutoHeal Live Threat Center connects directly to the persistent SQLite WAL database (`data/shopsphere.db`), active Server-Sent Events (`/api/security/events/stream`), and the autonomous SOAR/AST defense engine. Every metric, event row, timeline node, and rule counter represents authentic, unsimulated operational telemetry.

---

## Architectural Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OBSIDIAN SENTINEL SHELL                         │
├────────────────────────────────────────────────────────────────────────┤
│ Header Ribbon: Live Status Badge | Quick Date Ranges | Stream Controls │
├────────────────────────────────────────────────────────────────────────┤
│ KPI Ribbon: Total Scope | Critical Events | High Events | Active Rules │
├────────────────────────────────────────────────────────────────────────┤
│ Detection Rule Catalog: 7 Production Rules (INJ, XSS, AUTH, RATE, etc) │
├────────────────────────────────────────────────────────────────────────┤
│ Multi-Filter Toolbar: Search | Category | Severity | Action | Client IP│
├────────────────────────────────────────────────────────────────────────┤
│ Security Event Explorer: Server-Side Paginated Telemetry Data Table    │
├────────────────────────────────────────────────────────────────────────┤
│ Side-Over Forensic Inspector: 5-Tab Dossier & Investigation Workflow   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Connection State Engine & Real-Time Monitoring

A core mandate of Phase 3 is that the UI must **never display "LIVE" or "Connected" when the telemetry stream is inactive or disconnected**. The Live Threat Center implements a four-state finite state machine (FSM) monitoring the Server-Sent Events stream:

| Connection State | Visual Indicator | Pill Token | Behavior & Diagnostics |
| :--- | :--- | :--- | :--- |
| **CONNECTED** | Emerald Green with Pulsing Dot | `.live-status-pill.connected` | EventSource active (`READY_STATE_OPEN`), heartbeats received every 3s, real-time event arrival enabled. |
| **RECONNECTING** | Amber Yellow with Spinning Icon | `.live-status-pill.reconnecting` | Stream connection temporarily interrupted; exponential backoff reconnection active. |
| **DEGRADED** | Rose Red with Warning Alert | `.live-status-pill.degraded` | Multiple SSE reconnect failures; automatic HTTP polling fallback (5s cadence) engaged. |
| **DISCONNECTED** | Slate Muted with Pause Icon | `.live-status-pill.disconnected` | Operator paused stream or terminal network loss. Live arrival suspended. |

---

## Technical KPI Ribbon Metrics

The Live Threat Center header exposes a dense, 5-card telemetry ribbon providing immediate situational awareness:

1. **Total Events in Scope (`#tcTotalEventsCount`)**:
   - Total number of raw request telemetry records in `security_events` matching the active time window and category/severity filters.
2. **Critical Threat Events (`#tcCriticalEventsCount`)**:
   - Count of events classified with `CRITICAL` severity (e.g., active SQL injection probes, multi-stage APT kill-chains).
3. **High Severity Events (`#tcHighEventsCount`)**:
   - Volume of `HIGH` severity telemetry (e.g., cross-site scripting attempts, unauthorized administrative endpoint probes).
4. **Active Detection Rules (`#tcActiveDetectionsCount`)**:
   - Ratio of online detection rules (`7 / 7`) actively inspecting traffic and enforcing autonomous responses.
5. **Last Telemetry Timestamp (`#tcLastEventTimestamp`)**:
   - Precise UTC timestamp of the most recently ingested telemetry event or sentinel heartbeat.

---

## Integration with Existing Backend Architecture

The Live Threat Center integrates seamlessly with existing AutoHeal components:
- **`AppSecProtectionMiddleware`**: Intercepts every inbound HTTP request, runs real-time detection passes, and logs structured telemetry to `security_events`.
- **`AppSecDetector`**: Evaluates injection patterns, XSS signatures, and credential stuffing vectors.
- **`AppSecResponder`**: Enforces autonomous quarantine in `blocked_clients`.
- **`event_investigations` Table**: Persists analyst notes, investigation status (`NEW`, `TRIAGED`, `INVESTIGATING`, `CLOSED`), and incident escalation links.
- **`admin_audit_logs` Table**: Records every status update and escalation action with timestamp and operator attribution.
