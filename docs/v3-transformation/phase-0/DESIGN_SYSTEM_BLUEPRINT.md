# AutoHeal v3.0 — Phase 0: Obsidian Sentinel Design System Blueprint
**Document ID:** AH-V3-P0-DSB-001  
**Visual Identity:** Obsidian Sentinel (Enterprise Cybersecurity Command Center)  
**WCAG Target:** WCAG 2.2 AA / AAA Compliant  
**Status:** Certified Blueprint  

---

## 1. Design Philosophy: Obsidian Sentinel

The **Obsidian Sentinel** visual identity delivers a calm, authoritative, high-density, and mission-critical command center experience for cybersecurity operations analysts, incident responders, and CISOs.

### Core Tenets
1. **Analytical Clarity Over Visual Gimmicks:** Every element serves an operational purpose. Eliminates neon glow, random decorative gradients, oversized cards, and artificial metrics.
2. **True Data Grounding:** Every status badge, count, chart curve, and timeline node binds to verified backend telemetry (`/api/security/*`, `/api/state`, `/api/health`).
3. **Ergonomic Information Density:** Compact, clear data tables with sticky headers, monospaced forensic identifiers, and clean hierarchy to reduce cognitive fatigue during high-stress incident responses.
4. **Dual Application Identity:**
   - **AutoHeal SOC:** Obsidian Sentinel dark command center (`#090D14` base).
   - **ShopSphere Storefront:** Polished, trustworthy consumer e-commerce interface (`#FFFFFF` / `#F1F3F6` base) with clear lineage to AutoHeal protection.

---

## 2. Reusable Design Tokens (CSS Custom Properties)

```css
:root {
    /* Base & Surface Elevation */
    --bg-base: #090D14;
    --bg-surface: #101722;
    --bg-elevated: #151F2C;
    --bg-card: #151F2C;
    --bg-card-header: #192535;
    --bg-card-subtle: #0E1622;
    --bg-input: #0D131D;
    --bg-terminal: #05080E;
    --bg-table-header: #131D2B;
    --bg-table-row-hover: #182436;

    /* Panel & Component Boundaries */
    --border-main: #253344;
    --border-subtle: #1A2534;
    --border-panel: #253344;
    --border-light: #2E3E53;
    --border-focus: #38BDF8;

    /* High-Contrast Readable Typography */
    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --text-dim: #475569;
    --text-on-primary: #090D14;

    /* Semantic Accents & Status */
    --primary: #38BDF8;
    --primary-hover: #7DD3FC;
    --primary-dark: #0284C7;
    --primary-subtle: rgba(56, 189, 248, 0.12);

    --accent-cyan: #38BDF8;
    --accent-purple: #A78BFA;
    --accent-purple-subtle: rgba(167, 139, 250, 0.12);

    --status-success: #22C55E;
    --status-success-bg: rgba(34, 197, 94, 0.12);
    --status-success-border: rgba(34, 197, 94, 0.35);

    --status-warning: #F59E0B;
    --status-warning-bg: rgba(245, 158, 11, 0.12);
    --status-warning-border: rgba(245, 158, 11, 0.35);

    --status-danger: #EF4444;
    --status-danger-bg: rgba(239, 68, 68, 0.12);
    --status-danger-border: rgba(239, 68, 68, 0.35);

    /* Fonts */
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

    /* Sizing & Radius */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-pill: 9999px;

    /* Shadows */
    --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.4);
    --shadow-card: 0 4px 14px rgba(0, 0, 0, 0.5);
    --shadow-modal: 0 20px 48px rgba(0, 0, 0, 0.8), 0 0 0 1px var(--border-panel);
    --shadow-focus: 0 0 0 2px var(--bg-base), 0 0 0 4px var(--border-focus);

    /* Layout Dimensions */
    --sidebar-width: 250px;
    --sidebar-collapsed-width: 64px;
    --topbar-height: 56px;
}
```

---

## 3. Typography Scale & Specifications

| Typography Level | Font Family | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display 1** | Inter | 24px (1.5rem) | 800 (Extra Bold) | 1.2 | Command Center Brand, Modal Headers |
| **Heading 2** | Inter | 18px (1.125rem) | 700 (Bold) | 1.3 | Workspace Page Header, Section Titles |
| **Heading 3** | Inter | 14px (0.875rem) | 700 (Bold) | 1.4 | Card Headers, Panel Titles, Drawer Headers |
| **Body Primary**| Inter | 13px (0.8125rem) | 500 (Medium) | 1.5 | Standard Table Cells, Descriptions, Inputs |
| **Body Compact**| Inter | 12px (0.75rem) | 400 (Regular) | 1.4 | Secondary Table Metadata, Filter Chips |
| **Forensic Mono**| JetBrains Mono | 11px (0.6875rem) | 600 (Semi-Bold) | 1.4 | Hashes, Timestamps, Port IDs, Code Diffs |

---

## 4. UI Component Specifications

### 4.1 Collapsible Enterprise Sidebar
- **Dimensions:** Width `250px` expanded; `64px` collapsed. Transition `0.2s cubic-bezier(0.16, 1, 0.3, 1)`.
- **Navigation Items:** 11 items grouped into "Operations", "Autonomous Defense", and "Infrastructure & Audit".
- **States:**
  - *Default:* `--text-secondary`, transparent background.
  - *Hover:* `--text-primary`, `rgba(255, 255, 255, 0.04)` background.
  - *Active:* `--text-primary`, `rgba(56, 189, 248, 0.1)` background, `3px` solid cyan left border accent.

### 4.2 Top Application Bar
- **Dimensions:** Height `56px`, sticky at top of viewport (`z-index: 900`).
- **Components:**
  - Sidebar toggle button (`#sidebarToggleBtn`).
  - Dynamic breadcrumb trail showing current module location.
  - Command Palette trigger button (`Ctrl+K` chip).
  - Sentinel status heartbeat pill with pulsing green indicator dot.
  - Live UTC + Local ISO Clock (`#currentTime`).
  - User role badge (`ROLE: SOC ADMIN`).

### 4.3 KPI Telemetry Ribbon
- Multi-column responsive grid (`repeat(auto-fit, minmax(200px, 1fr))`).
- High-contrast numerical counters in bold monospaced font.
- Dynamic color mapping based on operational thresholds (Green = Contained, Red = Critical Threat, Amber = Warning).

### 4.4 Forensic Data Table
- High-density table wrapped in `.soc-table-wrapper` with horizontal scroll protection.
- Sticky table header (`--bg-table-header`) with subtle 1px border.
- Monospaced forensic columns for IP addresses, timestamps, and correlation IDs.
- Interactive row hover (`--bg-table-row-hover`) and click-to-drawer inspection.

### 4.5 Command Palette Modal (`#cmdPaletteModal`)
- Centered overlay modal (`max-width: 600px`) with high-contrast backdrop blur (`rgba(0, 0, 0, 0.75)`).
- Instant search input matching workspaces, quick actions, recent incidents, and administrative tools.
- Full keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`, `Escape`).

### 4.6 Side-Over Event Detail Drawer (`#eventDetailDrawer`)
- Positioned on right viewport (`width: 520px; max-width: 90vw`).
- Formatted request metadata, headers, client IP, path, and raw JSON payload box.
- One-click "Copy JSON" button with toast notification.

---

## 5. State Handling Specifications

| State Type | Visual Manifestation | Component Example |
| :--- | :--- | :--- |
| **Loading State** | High-contrast spinner icon (`fa-spinner fa-spin`) + dim text | Table body while awaiting `/api/security/events` response |
| **Empty State** | Centered muted container with helpful guidance icon | "No incidents recorded yet. Launch a test from the Attack Center." |
| **Error State** | Distinct red badge / alert box with specific error message | Toastr notification + terminal red line on scenario failure |
| **Success State** | Green badge / notification + animated pulse | Verification probe confirmation (Attacker 403 / Benign 200) |

---

## 6. Responsive Breakpoints

- **Mobile (`< 768px`):** Off-canvas drawer navigation, single-column KPI stack, scrollable tables.
- **Tablet (`768px - 1023px`):** Icon-only collapsed rail (`64px`), 2-column KPI grid, stacked attack center.
- **Desktop (`1024px - 1439px`):** Full expanded sidebar (`250px`), 4-column KPI grid, side-by-side attack center.
- **Ultra-Wide (`1440px+`):** Expanded command center layout, wide high-density telemetry views, 480px 3D topology canvas.
