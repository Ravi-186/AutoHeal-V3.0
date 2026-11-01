# AutoHeal v3.0 — Responsive Design & Viewport Adaptability Report
**Document ID:** AH-V3-RSP-001  
**Target Viewports:** Mobile (360px - 767px), Tablet (768px - 1023px), Desktop / Laptop (1024px - 1439px), Ultra-Wide Command Centers (1440px+)  
**Status:** Validated  

---

## 1. Executive Summary

AutoHeal v3.0 and ShopSphere feature a fully fluid, responsive layout architecture engineered to support security operations centers across diverse display hardware—ranging from analysts reviewing telemetry on mobile or tablet devices during on-call rotations to multi-monitor 4K SOC video walls.

---

## 2. Breakpoint Grid Architecture

| Viewport Category | Screen Width Range | Sidebar State | Topbar Behavior | Grid Configurations |
| :--- | :--- | :--- | :--- | :--- |
| **Mobile** | `< 768px` | Off-canvas drawer (hidden by default, toggled via hamburger menu with slide-in animation) | Compact topbar, search button icon, clock truncated | Single column KPI stack (`1fr`), scrollable tables with sticky first columns |
| **Tablet** | `768px - 1023px` | Icon-only rail (`64px`) or auto-collapsing drawer | Full topbar with breadcrumb truncation | 2-column KPI grid (`repeat(2, 1fr)`), attack center controls stacked above live stream |
| **Desktop / Laptop** | `1024px - 1439px` | Expanded (`250px`) or user-collapsed (`64px`) | Full breadcrumbs, active status pill, live UTC clock | 4-column KPI grid, 2-column attack center (`1fr 1.5fr`), side-by-side incident dossier |
| **Ultra-Wide SOC Wall**| `1440px+` | Expanded (`250px`) | Full breadcrumbs, search trigger, status pill, user role, live clock | 4-column KPI grid, high-density telemetry tables, expanded 3D WebGL topology viewport |

---

## 3. Module-by-Module Responsive Audit

### 3.1 Global Shell & Navigation
- **Collapsible Sidebar:** Implemented with CSS transitions (`width 0.2s cubic-bezier(0.16, 1, 0.3, 1)`). When collapsed, labels and badges cleanly hide while SVG icons remain centered and interactive with hover tooltips.
- **Top Application Bar:** Sticky header with `z-index: 900` preserves breadcrumbs, real-time clock, status pill, and `Ctrl+K` command search across all scroll positions.
- **Mobile Drawer:** On viewports under 768px, clicking `#sidebarToggleBtn` slides the drawer into view over a dark scrim overlay (`z-index: 1000`). Clicking any item automatically closes the drawer and navigates to the target page.

### 3.2 Main Overview Dashboard (`pageOverview`)
- **KPI Summary Ribbon:** Fluid CSS Grid with `repeat(auto-fit, minmax(200px, 1fr))` automatically reflows from 4 columns on desktop to 2 columns on tablet and 1 column on mobile without clipping or horizontal scrollbars.
- **Security Posture Scorecard:** 3-column layout (`180px 1.4fr 1.2fr`) gracefully collapses to a single stacked column on tablets and mobile screens, maintaining full legibility of the score circular gauge, defense pillar progress bars, and scoring formula breakdown.
- **Chart & Telemetry Grid:** 2-column layout (`1.2fr 1fr`) stacks vertically on screens below 1024px to ensure Chart.js canvas maintains optimal height (240px) and touch readability.

### 3.3 Live Threat Center (`pageEvents`)
- **Filter Bar:** Multi-select filter inputs reflow from a 4-column horizontal grid to a stacked configuration on mobile.
- **Forensic Table:** Encapsulated in `.soc-table-wrapper` with `overflow-x: auto` and `-webkit-overflow-scrolling: touch`. Allows smooth horizontal panning for wide telemetry logs without breaking page layout.
- **Side-Over Event Detail Drawer:** Smooth slide-over drawer (`width: 520px; max-width: 90vw`) adapts automatically to mobile screens, taking full screen width with a sticky close button.

### 3.4 Attack Simulation Center (`pageAttackCenter`)
- **Execution Grid:** Reflows from side-by-side (`1fr 1.5fr`) on desktop to stacked (`1fr`) on tablet/mobile.
- **5-Stage Stepper:** Responsive step circles with flex-wrap and responsive typography prevent step label overlap.
- **Terminal Viewport:** Monospaced terminal container features a fixed 300px height with native touch scrolling and word-break protection.

### 3.5 Incident Command Center (`pageIncidents`)
- **Triage Queue Table:** High-density table displays core columns (ID, Detected, Vector, Severity, Action) with responsive ellipsis for long endpoint paths.
- **Forensic Dossier Workspace:** Dynamic side-by-side evidence and AI root-cause layout stacks cleanly on viewports under 1024px.

### 3.6 SOAR Automation Center (`pageSoar`)
- **Playbook Flowchart:** Horizontal node pipeline with overflow-x scrolling and arrow connectors allows analysts on smaller screens to scroll smoothly across the 5 execution stages.

### 3.7 Threat Topology & Asset Map (`pageTopology`)
- **3D WebGL Canvas:** Dynamically adjusts renderer width and aspect ratio on container resize.
- **Accessible 2D Table Fallback:** High-contrast tabular view accessible on all screen sizes and compatible with screen magnifiers.

### 3.8 ShopSphere E-Commerce Storefront (`/shop`)
- **Customer Navigation:** Sticky navbar with responsive search bar, shopping cart badge, and wishlist count.
- **Product Grid:** Responsive CSS Grid (`repeat(auto-fill, minmax(240px, 1fr))`) ensuring 4 products per row on desktop, 2 per row on tablet, and 1 per row on mobile.
- **Slide-Out Cart & Checkout:** Slide-over cart drawer (`max-width: 440px`) and centered multi-step checkout modal adapt to full-screen on mobile devices.

---

## 4. Verification & Defect Prevention

- **Zero Horizontal Body Overflow:** Verified `overflow-x: hidden` on root elements and strict `box-sizing: border-box` across all components.
- **Touch Target Sizing:** All buttons and interactive tabs maintain a minimum touch target of 36px x 36px (WCAG 2.5.8 compliant).
- **Viewport Meta Tag:** Strictly configured: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
