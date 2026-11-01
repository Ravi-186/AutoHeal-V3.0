# AutoHeal v3.0: Enterprise Frontend Architecture & Design Specification

**Architect:** Senior Frontend Architect & Systems Lead  
**Scope:** Architecture Blueprint, Component Hierarchy, State Management, and Design Token System  
**Baseline Version:** AutoHeal v2.5.0-PROD  
**Target Version:** AutoHeal v3.0-ENTERPRISE  
**Theme:** **Obsidian Sentinel** (Cybersecurity Command Center Visual Identity)  
**Classification:** **TECHNICAL ARCHITECTURE SPECIFICATION**

---

## 1. Architectural Philosophy & Principles

The AutoHeal v3.0 frontend architecture is built on five core engineering principles:

1. **Mission-Critical Clarity:** Security analysts under pressure require immediate cognitive clarity. Critical information (threat severity, affected asset, containment status) is prioritized in the visual hierarchy over decorative elements.
2. **Zero-Latency Ingestion & Rendering:** Telemetry streams, incident queues, and live event tables must render smoothly without UI freeze or input latency.
3. **Deterministic State Synchronization:** Real-time events received via Server-Sent Events (SSE) or polling updates synchronize with local view state deterministically without race conditions or duplicated DOM elements.
4. **Architectural Backward-Compatibility:** The frontend layer operates on top of the established FastAPI backend routes and SQLite database schemas without requiring breaking modifications to working APIs.
5. **Universal Accessibility & Responsiveness:** Conforms strictly to WCAG 2.2 AA standards, supporting full keyboard navigation (including `Ctrl+K` command palette), semantic ARIA bindings, and responsive layouts from mobile (375px) to ultra-wide displays (2560px).

---

## 2. High-Level Component Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION SHELL                                       │
│ ┌───────────────────────────┬────────────────────────────────────────────────────────┐ │
│ │    COLLAPSIBLE SIDEBAR    │                    TOP APPLICATION BAR                 │ │
│ │ • Brand & Version Badge   │ • Breadcrumbs navigation  • System Status Sentinel     │ │
│ │ • 10 Module Nav Items     │ • Global Search (Ctrl+K)  • Notification Center        │ │
│ │ • Role / Security Level   │ • Live UTC Clock Display  • Operator Profile & Theme   │ │
│ └───────────────────────────┴────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                  VIEWPORT ROUTER                                       │
│ ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. Executive SOC Overview    • Real-time KPI Ribbon, Posture Gauge, Event Trends  │ │
│ │ 2. Live Threat Center        • Virtualized event table, multi-filter, detail drawer│ │
│ │ 3. Attack Simulation Center  • Scenario selector, SSE timeline, live diffs        │ │
│ │ 4. Incident Command Center   • Forensic dossier, attack timeline, analyst actions  │ │
│ │ 5. SOAR Automation Center    • Interactive visual playbook builder & execution log │ │
│ │ 6. Self-Healing Center       • Remediation lifecycle, AST diffs, rollback history  │ │
│ │ 7. Threat Intelligence       • IOC search, reputation scoring, enrichment feeds    │ │
│ │ 8. MITRE ATT&CK Matrix       • Interactive technique grid with rule coverage       │ │
│ │ 9. Asset Management          • Device inventory, zero-trust zones, risk ranking    │ │
│ │ 10. Reports & Administration • PDF/Markdown export, audit logs, RBAC management    │ │
│ └────────────────────────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                             MODALS, OVERLAYS & NOTIFICATIONS                           │
│ • Global Command Palette (Ctrl+K)   • Event Detail Drawer   • Patch Diff Modal         │
│ • Incident Triage Dialog            • Toastr Notification System (Auto-Dismiss)        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Obsidian Sentinel Design Token System

AutoHeal v3.0 establishes a comprehensive design token system defined via CSS custom properties in `:root`:

### 3.1 Color Palette
```css
:root {
    /* Primary Backgrounds */
    --obsidian-bg-base: #090D14;       /* Main canvas background */
    --obsidian-bg-surface: #101722;    /* Card and panel background */
    --obsidian-bg-elevated: #151F2C;   /* Modals, drawers, and active hover */
    --obsidian-bg-glass: rgba(16, 23, 34, 0.85); /* Backdrops with blur */

    /* Borders & Dividers */
    --obsidian-border-subtle: #1C2735;
    --obsidian-border-default: #253344;
    --obsidian-border-focus: #38BDF8;

    /* Typography & Content */
    --obsidian-text-primary: #F1F5F9;   /* High contrast body and headings */
    --obsidian-text-secondary: #94A3B8; /* Subtitles, labels, and metadata */
    --obsidian-text-muted: #64748B;     /* Placeholders, disabled states */
    --obsidian-text-accent: #38BDF8;    /* Interactive links, active items */

    /* Semantic Status Indicators */
    --obsidian-status-success: #22C55E; /* Contained, verified, normal */
    --obsidian-status-info: #38BDF8;    /* Telemetry, probes, notifications */
    --obsidian-status-warning: #F59E0B; /* Elevated risk, pending approval */
    --obsidian-status-danger: #EF4444;  /* Critical threat, active breach */
    --obsidian-status-purple: #A78BFA;  /* AI-Advisor, automated remediation */

    /* Elevation Shadows */
    --obsidian-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
    --obsidian-shadow-md: 0 4px 16px rgba(0, 0, 0, 0.5);
    --obsidian-shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.7);
    --obsidian-shadow-glow: 0 0 20px rgba(56, 189, 248, 0.15);
}
```

### 3.2 Typography Tokens
```css
:root {
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', "Fira Code", monospace;

    /* Typographic Scale */
    --text-xs: 0.75rem;    /* 12px - Labels, tags, timestamps */
    --text-sm: 0.875rem;   /* 14px - Table data, navigation items */
    --text-base: 1rem;     /* 16px - Body text, standard inputs */
    --text-lg: 1.125rem;   /* 18px - Subheaders, card titles */
    --text-xl: 1.25rem;    /* 20px - Section headings */
    --text-2xl: 1.5rem;    /* 24px - Page titles, modal headers */
    --text-3xl: 2rem;      /* 32px - Metric KPI values */
}
```

---

## 4. State Management & Real-Time Data Flow

### 4.1 Client-Side State Model
The frontend uses a structured reactive state model encapsulated in `autohealApp`:
- `state.activeTab`: Currently visible module view (`overview`, `threats`, `attack`, `incidents`, `soar`, `healing`, `intel`, `mitre`, `assets`, `reports`).
- `state.metrics`: Live KPI counts (`total_events`, `active_incidents`, `quarantined_ips`, `avg_remediation_ms`).
- `state.events`: Ring buffer of recent security events (max 500 records).
- `state.incidents`: List of incident summaries with active filters.
- `state.selectedIncident`: Currently inspected incident dossier.
- `state.vulnerabilities`: Tracked vulnerabilities, proposed patches, and verification states.
- `state.assets`: Monitored network devices, roles, zones, and risk scores.
- `state.quarantinedIPs`: Active blocklist items with expiration countdowns.

### 4.2 Real-Time Event Ingestion
1. **SSE Streaming (Attack Center):** When an attack scenario is launched, an `EventSource` connection binds to `/api/security/attack-center/stream`. Incoming execution chunks are appended to the live timeline in real time.
2. **Periodic Telemetry Polling (Background Sentinel):** A non-blocking asynchronous timer polls `/api/security/metrics` and `/api/security/events` every 5 seconds. If the user navigates away or switches tabs, polling pauses via `document.visibilityState` to preserve client CPU resources.
3. **Instant Action Dispatch:** User actions (such as unblocking an IP, approving a patch, or triggering a remediation) execute immediately via `fetch` and synchronously update relevant local state.

---

## 5. Navigation & Viewport Routing Architecture

Navigation is governed by an enterprise tab routing system:
- Each module is encapsulated in a dedicated `<section class="soc-page-view" id="page{Name}">`.
- Switching views activates the selected container, updates breadcrumbs, pushes hash history (`#threats`, `#incidents`, etc.), and refreshes the corresponding data feed.
- URL hash routing (`window.location.hash`) allows direct linking and bookmarking for security analysts.

---

## 6. Accessibility & Keyboard Navigation (WCAG 2.2 AA)

- **Command Palette (`Ctrl+K` / `Cmd+K`):** Global keyboard shortcut opens a focused search modal allowing rapid navigation across incidents, assets, tools, and actions.
- **Escape Key Handling:** Closes open modals, drawers, and dropdowns.
- **Visible Focus Rings:** Every interactive button, input, and tab maintains high-contrast `outline: 2px solid var(--obsidian-border-focus)`.
- **Screen Reader Bindings:** Semantic `<main>`, `<nav>`, `<aside>`, `<header>`, and ARIA attributes (`aria-selected`, `aria-expanded`, `role="status"`).

---

## 7. Performance Budget & Optimization

| Metric | Budget Target | Strategy |
| :--- | :--- | :--- |
| **First Contentful Paint (FCP)** | $\le 0.8\text{ s}$ | Zero compilation build step; lightweight critical CSS |
| **Largest Contentful Paint (LCP)** | $\le 1.8\text{ s}$ | Direct ASGI streaming, CDN font caching, optimized SVG icons |
| **Interaction to Next Paint (INP)** | $\le 100\text{ ms}$| Event delegation, decoupled DOM updates, asynchronous fetch |
| **Cumulative Layout Shift (CLS)** | $\le 0.05$ | Explicit aspect ratio and fixed-dimension chart containers |
| **Total JavaScript Bundle Size** | $< 150\text{ KB}$ | Vanilla ES6+ architecture without multi-megabyte frameworks |

---

## 8. Summary & Next Steps
With the frontend architecture established, Phase 1 commences immediately to construct the global design system tokens, collapsible enterprise sidebar, top navigation bar, command palette, and module containers.
