# AutoHeal v3.0 — Component Library Specification
**Document ID:** AH-V3-CMP-001  
**Architecture:** Modular CSS & Vanilla JS Micro-Components  
**Theme:** Obsidian Sentinel  

---

## 1. Atomic Design Architecture

The AutoHeal v3.0 component system follows an Atomic Design hierarchy:
- **Atoms:** Design tokens, buttons, input fields, badges, status pills, icons, monospace tags.
- **Molecules:** Search bar with shortcut chip, metric counter cards, table headers with sort indicators, breadcrumbs, user profile pills.
- **Organisms:** Collapsible sidebar navigation, forensic data tables with pagination, incident dossier workspace, 3D topology canvas, AST diff inspector modal, side-over event drawer.
- **Templates / Views:** 10 SOC workspace modules + ShopSphere e-commerce storefront.

---

## 2. Atoms & Base Elements

### 2.1 Buttons (`.btn`)
- `.btn-primary`: High-contrast cyan background (`#38BDF8`), dark text (`#090D14`), bold weight (`600`), hover lift and subtle glow.
- `.btn-secondary`: Elevated dark background (`#151F2C`), border `1px solid var(--border-panel)`, text (`#F1F5F9`).
- `.btn-danger`: Red accent background (`#EF4444`), white text (`#FFFFFF`), used strictly for destructive actions (quarantine, purge, rollback).
- `.btn-success`: Green accent background (`#22C55E`), white text, used for approvals and manual healing triggers.
- `.btn-icon`: Square or circular icon-only button with accessible `aria-label` and tooltip.

### 2.2 Status Badges & Pills (`.badge`, `.status-pill`)
- `.badge-critical`: Background `rgba(239, 68, 68, 0.15)`, text `#EF4444`, border `1px solid rgba(239, 68, 68, 0.4)`.
- `.badge-warning`: Background `rgba(245, 158, 11, 0.15)`, text `#F59E0B`, border `1px solid rgba(245, 158, 11, 0.4)`.
- `.badge-success`: Background `rgba(34, 197, 94, 0.15)`, text `#22C55E`, border `1px solid rgba(34, 197, 94, 0.4)`.
- `.badge-info`: Background `rgba(56, 189, 248, 0.15)`, text `#38BDF8`, border `1px solid rgba(56, 189, 248, 0.4)`.
- `.status-pill`: Pill container with a pulsing `.indicator-dot` for real-time daemon state (e.g., Sentinel Operational).

### 2.3 Monospace Forensics Tags (`.code-tag`, `.hash-tag`)
- Background `--bg-terminal`, font `--font-mono`, padding `2px 6px`, radius `4px`, border `1px solid var(--border-subtle)`.
- Used for IP addresses (`192.168.1.105`), CVE IDs (`CVE-2024-XXXX`), hashes (`SHA-256`), and SQL snippets.

---

## 3. Molecules

### 3.1 KPI Telemetry Tile (`.kpi-card`)
- Header with metric name, icon, and optional refresh status.
- Primary numerical counter in bold display font (`#F1F5F9`).
- Trend delta chip (e.g., `+12% vs 1h baseline` or `0 Active`).
- Subtitle explaining the metric source (e.g., `Live telemetry stream`).

### 3.2 Breadcrumb Bar (`.breadcrumb-nav`)
- Dynamic navigation trail showing current location: `AutoHeal SOC > Live Threat Center > Event #EV-8921`.
- Clickable ancestor links with accessible keyboard navigation.

### 3.3 Command Search Bar (`.cmd-search-input`)
- Embedded in top header with quick shortcut pill (`Ctrl + K`).
- Clicking launches the Command Palette modal.

---

## 4. Organisms

### 4.1 Global Application Shell
- **Sidebar (`.autoheal-sidebar`):**
  - Collapsible (260px expanded / 68px icon-only).
  - Clean brand mark with AutoHeal shield icon and v3.0 indicator.
  - 10 Navigation items with active state indicator.
  - ShopSphere storefront quick launcher.
- **Top Bar (`.autoheal-topbar`):**
  - Toggle button, breadcrumbs, search trigger, Sentinel heartbeat pill, live clock, user profile, and theme switch.

### 4.2 Forensic Data Table (`.forensic-table`)
- Sticky headers with sort arrows.
- Monospaced forensic columns.
- Row hover with subtle `#192747` highlight.
- Row click opens the Event Detail Drawer.
- Footer pagination with count summary (`Showing 1-50 of 248 events`).

### 4.3 Side-Over Event Detail Drawer (`.event-drawer`)
- Positioned on right viewport (`width: 480px`).
- Smooth slide-in transition (`transform: translateX(0)`).
- Tabs for "Formatted Inspection" and "Raw JSON".
- One-click "Copy Raw Payload" button with toast notification.

### 4.4 Incident Dossier Workspace (`.incident-dossier`)
- Dedicated incident command header with severity, status, and time elapsed.
- Two-column layout:
  - Left: Attack lifecycle timeline, attacker profile, quarantined IP indicator.
  - Right: Evidence inspector, grounded AI root-cause summary, manual response actions.

### 4.5 3D / 2.5D Threat Topology Canvas (`.topology-canvas-container`)
- Three.js WebGL canvas rendering monitored nodes (ShopSphere API, Database, Auth Server, Edge Gateway, Internal LAN).
- Node coloring reflects real-time threat state (Green = Normal, Amber = Mitigating, Red = Compromised/Attacked).
- Zoom, pan, and rotate controls.
- Accessible 2D table toggle button for screen reader and keyboard-only users.

### 4.6 Command Palette Modal (`#cmdPaletteModal`)
- Modal overlay with high-contrast backdrop blur.
- Live search input matching pages, incidents, assets, and tools.
- Grouped results with arrow-key navigation and enter-to-execute.
