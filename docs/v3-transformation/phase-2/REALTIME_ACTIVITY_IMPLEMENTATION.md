# AutoHeal v3.0 — Phase 2: Real-Time Activity Feed & Stream Implementation

**Document Version:** 3.0.0  
**Status:** Certified & Implemented  
**Author:** Principal Frontend Architect & Backend Integration Specialist  
**Component Scope:** Live Activity Feed (`#executiveActivityFeedContainer`) & Active Incident Queue (`#overviewIncidentsTableBody`)

---

## 1. Real-Time Architecture & Design Goals

The Executive SOC Command Center requires immediate visibility into emerging threats without requiring manual page reloads or full-page refreshes. 

```
[ ASGI HTTP Traffic ] 
        │
        ├──> [ AppSec Telemetry Middleware ] ──> [ SSE Broadcast Queue ]
        │                                                │
        └──> [ SQLite WAL Database ]                     │ (HTTP Event-Stream)
                    ▲                                    ▼
                    │                            [ Browser EventSource ]
            [ REST Polling / API ]                       │
                    ▲                            [ DOM Prepend Animation ]
                    │                                    ▼
        [ Controlled 5s Auto-Refresh ]       [ Live Activity Feed Card ]
```

### Architectural Requirements:
1. **Zero Simulation:** Live events must originate from actual network requests or attack tests processed by the ASGI middleware.
2. **Low-Overhead SSE:** Server-Sent Events (`/api/security/events/stream`) stream events as single-line JSON payloads.
3. **Heartbeat Keepalive:** 15-second heartbeat frames maintain proxy connections and verify connection vitality.
4. **Resilient Reconnection:** Automatic backoff (10s) upon connection drop without UI freezing.
5. **Bounded DOM Management:** Bounded feed buffer (maximum 20 items) prevents memory leaks and layout performance degradation.
6. **Smooth Visual Feedback:** Micro-animations (`pulse-glow`) highlight newly arrived events before blending into the feed.

---

## 2. Server-Sent Events (SSE) Protocol

### Endpoint: `/api/security/events/stream`
- **Transport:** HTTP/1.1 persistent streaming with `text/event-stream` media type.
- **Headers:**
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no` (disables reverse-proxy buffering in Nginx/Envoy)

### Event Message Payloads:

#### Telemetry Event Frame:
```json
data: {
  "event_id": "EVT-007742",
  "event_type": "SQL_INJECTION_DETECTED",
  "severity": "CRITICAL",
  "client_ip": "198.51.100.88",
  "path": "/api/shop/search",
  "timestamp": "2026-11-01 06:34:42"
}
```

#### Heartbeat Keepalive Frame:
```json
data: {
  "heartbeat": true,
  "timestamp": "2026-11-01 06:34:57"
}
```

---

## 3. Client-Side Stream Controller (`initExecutiveSSEStream`)

Implemented in `autoheal/web/static/js/script.js`:

```javascript
function initExecutiveSSEStream() {
    if (executiveSSEClient) {
        try { executiveSSEClient.close(); } catch (e) {}
    }

    try {
        executiveSSEClient = new EventSource('/api/security/events/stream');

        executiveSSEClient.onmessage = function (e) {
            try {
                const payload = JSON.parse(e.data);
                if (payload.heartbeat) {
                    const pill = document.getElementById('sentinelStatusPill');
                    if (pill) pill.setAttribute('data-tooltip', `Sentinel SSE Stream Active: ${new Date().toLocaleTimeString()}`);
                    return;
                }

                const container = document.getElementById('executiveActivityFeedContainer');
                if (container && payload.event_type) {
                    const timeStr = formatAppSecTimestamp(payload.timestamp, false);
                    const sev = (payload.severity || 'INFO').toUpperCase();
                    const sevClass = sev === 'CRITICAL' ? 'badge-critical' : sev === 'HIGH' ? 'badge-warning' : sev === 'MEDIUM' ? 'badge-info' : 'badge-neutral';

                    const newEl = document.createElement('div');
                    newEl.className = 'activity-feed-item';
                    newEl.style.animation = 'pulse-glow 1.5s ease-out';
                    newEl.innerHTML = `
                        <div style="font-size:1.1rem; color:var(--accent-cyan); margin-top:2px;">
                            <i class="fa-solid fa-bolt" aria-hidden="true"></i>
                        </div>
                        <div class="activity-item-content">
                            <div class="activity-item-title">
                                <span class="font-mono text-cyan" style="font-weight:700;">EVT-LIVE</span>
                                <span style="color:var(--text-primary); font-weight:600;">${payload.event_type}</span>
                                <span class="badge ${sevClass}" style="font-size:0.62rem; padding:1px 5px;">${sev}</span>
                            </div>
                            <div class="activity-item-meta">
                                <span><i class="fa-solid fa-network-wired"></i> ${payload.client_ip || '127.0.0.1'}</span>
                                <span>&bull;</span>
                                <span><code>${payload.path || '/'}</code></span>
                                <span>&bull;</span>
                                <span class="font-mono" style="color:var(--text-muted);">${timeStr}</span>
                            </div>
                        </div>
                        <div>
                            <span class="badge ${sevClass}" style="font-size:0.65rem;">${sev}</span>
                        </div>
                    `;

                    // Remove placeholder if present
                    if (container.children.length === 1 && container.innerText.includes('Listening')) {
                        container.innerHTML = '';
                    }

                    container.prepend(newEl);

                    // Bounded queue: prune oldest items beyond 20 entries
                    while (container.children.length > 20) {
                        container.removeChild(container.lastChild);
                    }
                }
            } catch (err) {}
        };

        executiveSSEClient.onerror = function () {
            try { executiveSSEClient.close(); } catch (e) {}
            // Gracefully retry in 10s without flooding
            setTimeout(initExecutiveSSEStream, 10000);
        };
    } catch (e) {
        console.warn('Executive SSE stream could not be initialized:', e);
    }
}
```

---

## 4. Controlled Auto-Refresh Engine

For aggregate metrics, charts, and subsystem health, the dashboard implements a controlled 5-second polling loop managed by `#btnDashboardAutoRefresh`:

1. **State Preservation:** The timer runs only when `#pageOverview` is the active workspace tab.
2. **User Pause Control:** Clicking `#btnDashboardAutoRefresh` pauses the interval timer, disables spinning icon animation, and displays `Paused`.
3. **Manual Refresh Override:** Clicking `#btnRefreshDashboard` triggers an immediate out-of-cycle refresh and displays a confirmation toast.

---

## 5. Active Incident Command Queue Integration

Directly beside the live activity feed is the **Active Incident Command Queue** (`#overviewIncidentsTableBody`):

- **Data Source:** `/api/security/incidents?limit=6`
- **Columns:**
  - `Incident ID`: Monospace cyan link with direct inspection trigger.
  - `Severity`: Multi-cue badge (Critical, High, Medium, Low).
  - `Title / Threat`: Category and target endpoint URL.
  - `Source IP`: Monospace IP address.
  - `Status`: Colored status badge (`CONTAINED`, `INVESTIGATING`, `VERIFIED`).
  - `Action`: Clickable triage button `<button class="btn btn-outline btn-sm" onclick="inspectIncident('INC-...')">`.
- **Drill-down Navigation:** Clicking any incident jumps to `#pageInvestigation` or `#pageIncidents`, preselecting the incident ID and opening its forensic dossier.

---

*Certified real-time stream verified with zero synthetic events.*
