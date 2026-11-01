# GLOBAL APPLICATION SHELL SPECIFICATION & IMPLEMENTATION REPORT
**AutoHeal v3.0 — Phase 1: Obsidian Sentinel Design System & Global Application Shell**
**Date:** November 1, 2026  
**Document Version:** 1.0.0-ENTERPRISE  
**Classification:** Proprietary Enterprise Architecture Documentation

---

## 1. Executive Architecture Summary

The AutoHeal v3.0 Global Application Shell establishes the persistent, responsive, and role-governed frame supporting all security workflows within the Autonomous Security Operations Center (SOC). Engineered according to the **Obsidian Sentinel** design philosophy, the shell balances dense forensic readability with fluid interaction ergonomics, rigorous accessibility compliance (WCAG 2.2 AA), and zero-fake-route telemetry.

The shell encompasses two persistent navigation vectors:
1. **The Obsidian Sentinel Primary Sidebar**: A collapsible multi-group hierarchical navigation panel accommodating 18 fully connected operational modules across 6 security domains.
2. **The Sentinel Global Command Topbar**: An ambient telemetry and action strip integrating real-time system connection states, unified breadcrumbs, omnidirectional search, Ctrl+K command palette trigger, theme contrast switching, live UTC synchronizer, notification popovers, analyst profile management, and accessible session termination.

---

## 2. Global Shell Layout & Grid Geometry

The application shell utilizes an adaptive dual-rail CSS Grid and Flexbox layout structure designed for zero-horizontal-overflow across all viewport widths.

```
+------------------------------------------------------------------------------------+
|  SIDEBAR (260px / 72px)  |  GLOBAL COMMAND TOPBAR (h: 60px)                        |
|  [Logo & Sentinel Pulse] |  [Toggle] [Breadcrumbs] [Search/Ctrl+K] [Pill] [Clock]  |
|                          |  [Theme] [Notifications] [User Profile]                |
|  ----------------------- +---------------------------------------------------------+
|  GROUP 1: OVERVIEW       |  ACTIVE VIEWPORT CONTAINER (<main class="autoheal-main">)|
|  - SOC Overview          |                                                         |
|  GROUP 2: THREAT OPS     |  - Active Section (e.g., #pageOverview, #pageEvents)    |
|  - Live Threat Center    |  - Real-time SSE / REST Data Stream                     |
|  - Attack Simulator      |  - Responsive Card Grid / Forensic Tables / Metrics     |
|  - Security Events       |                                                         |
|  - Threat Intelligence   |                                                         |
|  - MITRE ATT&CK          |                                                         |
|  GROUP 3: INCIDENT RESP  |                                                         |
|  - Incident Center       |                                                         |
|  - Investigation         |                                                         |
|  - SOAR Automation       |                                                         |
|  - Self-Healing          |                                                         |
|  GROUP 4: ASSETS         |                                                         |
|  - Asset Explorer        |                                                         |
|  - Security Posture      |                                                         |
|  GROUP 5: ANALYTICS      |                                                         |
|  - Reports               |                                                         |
|  - Security Analytics    |                                                         |
|  GROUP 6: ADMIN          |                                                         |
|  - Users and Roles       |                                                         |
|  - Audit Logs            |                                                         |
|  - System Health         |                                                         |
|  - Settings              |                                                         |
+------------------------------------------------------------------------------------+
```

### Layout Dimensional Tokens

| Element | Expanded Desktop | Collapsed Desktop | Tablet / Laptop | Mobile (<768px) |
| :--- | :--- | :--- | :--- | :--- |
| **Sidebar Width** | `260px` | `72px` | `72px` (icons only) | `280px` (off-canvas drawer) |
| **Sidebar Position** | `fixed` / left: `0` | `fixed` / left: `0` | `fixed` / left: `0` | `fixed` / left: `-280px` |
| **Topbar Height** | `60px` | `60px` | `60px` | `60px` |
| **Main Margin-Left**| `260px` | `72px` | `72px` | `0` |
| **Main Max-Width** | `1920px` (centered)| `1920px` (centered)| `100%` | `100%` |
| **Z-Index Hierarchy**| Sidebar: `1000` | Topbar: `900` | Backdrop: `999` | Modals: `2000` |

---

## 3. Sidebar Architecture & Module Routing

The sidebar provides structured access to all 18 security modules organized into 6 operational categories. In compliance with strict engineering guidelines, **no fake navigation destinations exist**. Every navigation link binds directly to an active DOM viewport container managed by `switchToTab(pageId)` in `script.js` and hydrated by live REST/SSE endpoints.

### Module Directory & Route Mapping

| Group | Navigation Item | Target Element ID | Route / Backend Data Source | Purpose & Operational Functionality |
| :--- | :--- | :--- | :--- | :--- |
| **OVERVIEW** | SOC Overview | `#pageOverview` | `/api/security/metrics` | High-level autonomous SOC dashboard, attack pulse, active posture gauge |
| **THREAT OPERATIONS** | Live Threat Center | `#pageEvents` | SSE `/api/security/events/stream` | Real-time live threat event stream with dynamic playback and filtering |
| **THREAT OPERATIONS** | Attack Simulator | `#pageAttackCenter` | `/api/security/simulate` | Adversarial injection console (SQLi, XSS, Brute Force, Token Hijacking) |
| **THREAT OPERATIONS** | Security Events | `#pageEventsTable` | `/api/security/events` | High-density forensic event log with severity filters, pagination, and search |
| **THREAT OPERATIONS** | Threat Intelligence | `#pageThreatIntel` | `/api/threat-intel/indicators` | External indicator feeds, malicious IP blocklists, and threat actor profiles |
| **THREAT OPERATIONS** | MITRE ATT&CK | `#pageMitre` | `/api/mitre/coverage` | TTP matrix mapping, detection coverage, kill-chain progression heatmaps |
| **INCIDENT RESPONSE** | Incident Center | `#pageIncidents` | `/api/security/incidents` | Unified incident queue, severity triage, lifecycle status management |
| **INCIDENT RESPONSE** | Incident Investigation | `#pageInvestigation` | `/api/security/incidents/{id}` | Deep forensic root-cause analysis, chronological event replay, raw artifacts |
| **INCIDENT RESPONSE** | SOAR Automation | `#pageSoar` | `/api/soar/playbooks` | Autonomous remediation playbooks, conditional execution trees, rate controls |
| **INCIDENT RESPONSE** | Self-Healing | `#pageHealing` | `/api/state`, `/api/health` | Autonomous recovery actions, service restarts, canary rollback verification |
| **ASSET MANAGEMENT** | Asset Explorer | `#pageTopology` | `/api/topology` | Real-time network and service dependency topology, host inventory |
| **ASSET MANAGEMENT** | Security Posture | `#pagePosture` | `/api/security/posture` | 7-pillar zero-trust defense posture, hardening score, firewall status |
| **ANALYTICS** | Reports | `#pageReports` | `/api/reports/generate` | Executive compliance summaries, incident trend exports, PDF/CSV downloads |
| **ANALYTICS** | Security Analytics | `#pageAnalytics` | `/api/security/metrics` | MTTD/MTTR analytics, 7-day velocity charts, attack vector distribution |
| **ADMINISTRATION** | Users and Roles | `#pageUsers` | `/api/security/users` | RBAC directory, role privilege matrix, analyst session audits |
| **ADMINISTRATION** | Audit Logs | `#pageAudit` | `/api/security/audit-trail` | Cryptographically signed, immutable administrative change logs |
| **ADMINISTRATION** | System Health | `#pageHealth` | `/api/health` | Service daemon status, database latency, memory load, SSE broker health |
| **ADMINISTRATION** | Settings | `#pageSettings` | `/api/settings` | Notification webhooks, agent sensitivity thresholds, retention policies |

### Sidebar Ergonomics & State Mechanics

1. **Collapsible State Handling**:
   - Toggled via the Topbar hamburger button (`#sidebarToggleBtn`) or keyboard shortcut.
   - When collapsed, the sidebar transitions smoothly (`transition: width 0.25s cubic-bezier(0.16, 1, 0.3, 1)`).
   - Module labels fade out with `opacity: 0`, preserving icon alignments and activating native tooltips (`[data-tooltip]`) for hover readability.
   - The main content area shifts dynamically (`margin-left: 72px`), maximizing analytical canvas area.
2. **Mobile Drawer Behavior**:
   - On viewports `< 768px`, the sidebar transitions off-canvas (`transform: translateX(-100%)`).
   - Triggering the menu injects an accessible backdrop overlay (`.sidebar-backdrop`) that traps focus and intercepts outside clicks, cleanly dismissing the drawer.
3. **Active Route Indication**:
   - Active routes receive an elevated visual signature: cyan border accent (`border-left: 3px solid #38BDF8`), elevated background (`#151F2C`), and high-contrast icon rendering.
   - Updates dynamically when navigating via sidebar clicks, command palette entries, or deep links.

---

## 4. Sentinel Global Command Topbar

The persistent top navigation bar acts as the mission-control header for the SOC analyst, providing contextual telemetry and global command capabilities.

### Topbar Functional Components

```
+---------------------------------------------------------------------------------------------------------+
| [=]  Threat Operations > Security Events   [  Search Ctrl+K  ]   (o) SENTINEL ACTIVE  11:32:04 UTC      |
|                                                                  [Contrast] [Bell (3)] [Admin J.Doe v]  |
+---------------------------------------------------------------------------------------------------------+
```

1. **Sidebar Toggle Button (`#sidebarToggleBtn`)**:
   - Aria-labeled `aria-label="Toggle navigation sidebar"`.
   - Accessible keyboard target (`tabindex="0"`) triggering smooth expansion/collapse across all viewport tiers.
2. **Dynamic Breadcrumb Trail (`#breadcrumbActivePage`)**:
   - Computes operational hierarchy in real time based on the active tab (e.g., `Threat Operations / Security Events`).
   - Ensures analysts maintain clear situational awareness within deep investigation flows.
3. **Omni-Search & Command Palette Trigger (`.cmd-palette-trigger`)**:
   - Visual search input proxy showing shortcut badge `Ctrl K` (or `Cmd K` on macOS).
   - Clicking or typing `Ctrl+K` immediately opens the accessible Command Palette modal (`#commandPaletteModal`), enabling keyboard-driven navigation across all 18 modules.
4. **Sentinel Live Heartbeat Indicator (`#sentinelStatusPill`)**:
   - Connected to SSE stream heartbeat and daemon health telemetry.
   - Renders a pulsing security green radar ring (`#22C55E`) indicating active real-time autonomous monitoring.
   - Equipped with tooltip: `"Sentinel Autonomous Engine Active — SSE Live Stream Connected"`.
5. **Live Synchronized UTC Clock (`#currentTime`)**:
   - Formatted in ISO-8601 UTC notation (`HH:MM:SS UTC`) using JetBrains Mono tabular numeric typography (`font-variant-numeric: tabular-nums`).
   - Eliminates timezone ambiguity during cross-border incident triage.
6. **High-Contrast Theme Toggle (`#themeToggleBtn`)**:
   - Toggles `data-theme="high-contrast"` on the root document element.
   - Instantly adjusts panel borders to `#38BDF8`, primary text to `#FFFFFF`, and enforces WCAG AAA contrast ratios for low-light or outdoor incident command stations.
7. **Notification Popover Center (`#notificationContainer`)**:
   - Displays real-time critical alert counter badge (`#notificationBadge`).
   - Interactive popover reveals recent autonomous containment actions, threat spikes, and policy violations.
   - Features a one-click `"Clear All"` action and direct drill-down links to incident investigations.
8. **Analyst Profile & Role Simulation (`#userProfileContainer`)**:
   - Displays analyst avatar, name (`SecOps Admin`), and security role badge.
   - Clicking opens the User Profile Dropdown featuring:
     - Profile metadata and email address.
     - **Role-Aware Simulation Switcher**: Allows toggling between `Security Admin (Full Access)`, `SOC Lead (Incident & SOAR Control)`, `Analyst Tier 1 (Triage & Threat Ops)`, and `Auditor (Read-Only)`.
     - Direct link to Session Security Settings.
     - Accessible **Sign Out** trigger.
9. **Accessible Logout Confirmation Dialog (`#logoutConfirmModal`)**:
   - Implements WCAG-compliant modal trapping, focus management, and keyboard handling (`Escape` to cancel, `Enter` to confirm).
   - Eliminates accidental session termination during critical incident response operations.

---

## 5. Security & Authentication Integration

1. **Authoritative Backend Security**:
   - The shell strictly respects existing authentication headers and cookies.
   - Simulated role switching in the UI dynamically tests role-aware visibility without overwriting backend session tokens or tampering with database authority.
2. **Zero Sensitive Token Leakage**:
   - No JWT secrets, passwords, or session tokens are stored in unencrypted `localStorage`.
   - State indicators rely solely on authenticated `/api/*` endpoints.

---

## 6. Verification and Visual QA Checklist

| Component | Test Case | Expected Behavior | Observed Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **Sidebar Collapse** | Click `#sidebarToggleBtn` | Sidebar narrows to 72px; labels fade; main content margin updates to 72px | Smooth transition; icons centered; zero layout breakage | **PASS** |
| **Mobile Drawer** | Viewport width 500px, click menu | Sidebar slides from left (`280px`); backdrop displays; main stays full width | Responsive off-canvas navigation verified | **PASS** |
| **Module Navigation** | Click each of 18 navigation links | Active state toggles; target DOM container displays; breadcrumb updates | All 18 views render corresponding backend data | **PASS** |
| **Command Palette** | Press `Ctrl+K` | Command palette modal opens with focus inside search input | Verified across all pages; `Esc` closes modal | **PASS** |
| **Notification Popover**| Click bell icon | Dropdown reveals alerts; clicking outside dismisses popover | Popover opens/closes cleanly; dismiss listener verified | **PASS** |
| **Profile & Role Switch**| Select "Analyst Tier 1" | Role updates in UI; badge refreshes; screen reader announces change | Verified; dynamic role preview operational | **PASS** |
| **Theme Toggle** | Click contrast button | Document gains `data-theme="high-contrast"`; borders and badges brighten | Verified; high contrast style tokens apply instantly | **PASS** |
| **Logout Modal** | Click Sign Out | Backdrop appears; modal gains focus; Confirm/Cancel work cleanly | Modal traps focus; cancels cleanly; redirects on confirm | **PASS** |

---

## 7. Architectural Conclusion

The Global Application Shell implementation for AutoHeal v3.0 establishes an uncompromised, production-ready operational workstation. By consolidating 18 live security modules into an ergonomic 6-domain hierarchy and delivering instant situational awareness through the Sentinel Global Command Topbar, Phase 1 provides the solid architectural bedrock required for subsequent module deep-dives.
