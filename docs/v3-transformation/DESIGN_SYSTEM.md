# AutoHeal v3.0 — Obsidian Sentinel Design System Specification
**Document ID:** AH-V3-DS-001  
**Target Product Ecosystem:** AutoHeal SOC Sentinel & ShopSphere  
**Visual Identity:** Obsidian Sentinel (Enterprise Cybersecurity Command Center)  
**WCAG Compliance:** WCAG 2.2 AA / AAA where applicable  

---

## 1. Executive Design Philosophy

The **Obsidian Sentinel** visual identity delivers a calm, authoritative, high-density, and mission-critical command center experience for cybersecurity operations analysts, incident responders, and CISOs.

### Core Tenets
1. **Analytical Clarity Over Visual Gimmicks:** Every element serves an operational purpose. Eliminates neon glow, random decorative gradients, oversized cards, and artificial metrics.
2. **True Data Grounding:** Every status badge, count, chart curve, and timeline node binds to verified backend telemetry (`/api/security/*`, `/api/state`, `/api/health`).
3. **Ergonomic Information Density:** Compact, clear data tables with sticky headers, monospaced forensic identifiers, and clean hierarchy to reduce cognitive fatigue during high-stress incident responses.
4. **Dual Application Identity:**
   - **AutoHeal SOC:** Obsidian Sentinel dark command center (`#090D14` base).
   - **ShopSphere Storefront:** Polished, trustworthy consumer e-commerce interface (`#FFFFFF` / `#F8FAFC` base) with clear lineage to AutoHeal protection.

---

## 2. Color System & Design Tokens

### 2.1 Color Tokens (Dark Mode - Default SOC Sentinel)

| Token Name | Hex Value | Semantic Purpose | WCAG Contrast vs #090D14 |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#090D14` | Primary viewport application canvas | 1:1 (Base) |
| `--bg-surface` | `#101722` | Secondary background, sidebar, header | 1.15:1 |
| `--bg-elevated` | `#151F2C` | Content cards, modal containers, panels | 1.35:1 |
| `--bg-card-header` | `#192535` | Card header bands, active filter chips | 1.55:1 |
| `--bg-input` | `#0D131D` | Form inputs, search fields, textareas | 1.08:1 |
| `--bg-terminal` | `#05080E` | Forensic raw log & code viewer terminals | 1:1 |
| `--border-subtle` | `#1E2A3A` | Subtle dividers and table row borders | 1.4:1 |
| `--border-panel` | `#253344` | Panel outlines, card boundaries, input borders | 1.7:1 |
| `--border-active` | `#38BDF8` | Focus rings, active tabs, selected states | 8.2:1 |
| `--text-primary` | `#F1F5F9` | Primary headings, titles, key telemetry | **16.1:1 (AAA)** |
| `--text-secondary` | `#94A3B8` | Body descriptions, labels, column headers | **7.4:1 (AA)** |
| `--text-muted` | `#64748B` | Timestamps, metadata, inactive indicators | **4.6:1 (AA)** |
| `--accent-cyan` | `#38BDF8` | Telemetry, active state, telemetry links | **8.2:1 (AAA)** |
| `--accent-purple` | `#A78BFA` | Autonomous AI / ML engine, graph workflow | **7.9:1 (AAA)** |
| `--status-green` | `#22C55E` | Verified, contained, healthy, resolved | **8.8:1 (AAA)** |
| `--status-amber` | `#F59E0B` | Warning, mitigating, unverified patch | **9.1:1 (AAA)** |
| `--status-red` | `#EF4444` | Critical incident, attacker probe, active threat | **5.4:1 (AA)** |

### 2.2 Semantic Status Palette Mapping

```css
:root {
    --status-green-bg: rgba(34, 197, 94, 0.12);
    --status-green-border: rgba(34, 197, 94, 0.35);
    
    --status-amber-bg: rgba(245, 158, 11, 0.12);
    --status-amber-border: rgba(245, 158, 11, 0.35);

    --status-red-bg: rgba(239, 68, 68, 0.12);
    --status-red-border: rgba(239, 68, 68, 0.35);

    --status-cyan-bg: rgba(56, 189, 248, 0.12);
    --status-cyan-border: rgba(56, 189, 248, 0.35);

    --status-purple-bg: rgba(167, 139, 250, 0.12);
    --status-purple-border: rgba(167, 139, 250, 0.35);
}
```

---

## 3. Typography Hierarchy

### 3.1 Typeface Families
- **Interface Font (`--font-sans`):** `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
  - High legibility, neutral grotesk architecture, excellent micro-scale rendering.
- **Forensic Monospace (`--font-mono`):** `'JetBrains Mono', 'Fira Code', Consolas, monospace`
  - Distinct glyphs for `0` vs `O`, `1` vs `l`, full ligature support, strict column alignment for hashes, IP addresses, payloads, and AST diffs.

### 3.2 Typography Scale

| Level | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display 1** | 24px (1.5rem) | 800 (Extra Bold) | 1.2 | Command Center Brand, Modal Titles |
| **Heading 2** | 18px (1.125rem) | 700 (Bold) | 1.3 | Workspace Page Header, Section Titles |
| **Heading 3** | 15px (0.9375rem) | 600 (Semi-Bold) | 1.4 | Card Headers, Panel Titles, Drawer Headers |
| **Body Primary**| 13px (0.8125rem) | 500 (Medium) | 1.5 | Standard Table Cells, Descriptions, Inputs |
| **Body Compact**| 12px (0.75rem) | 400 (Regular) | 1.4 | Secondary Table Metadata, Filter Chips |
| **Caption / Code**| 11px (0.6875rem) | 600 (Semi-Bold) | 1.3 | Hashes, Timestamps, Port IDs, Badges |

---

## 4. Spacing, Elevation & Layout Grid

### 4.1 Spacing Scale
- `var(--space-1)` = `4px`
- `var(--space-2)` = `8px`
- `var(--space-3)` = `12px`
- `var(--space-4)` = `16px`
- `var(--space-5)` = `20px`
- `var(--space-6)` = `24px`
- `var(--space-8)` = `32px`

### 4.2 Border Radius Scale
- `var(--radius-sm)` = `4px` (Inputs, tags, micro-badges)
- `var(--radius-md)` = `8px` (Cards, buttons, dropdown menus)
- `var(--radius-lg)` = `12px` (Workspaces, modal dialogs, drawers)
- `var(--radius-pill)` = `9999px` (Status pills, counter chips)

### 4.3 Elevation & Shadows
- `var(--shadow-subtle)`: `0 1px 3px rgba(0, 0, 0, 0.4)`
- `var(--shadow-card)`: `0 4px 12px rgba(0, 0, 0, 0.5)`
- `var(--shadow-modal)`: `0 20px 48px rgba(0, 0, 0, 0.8), 0 0 0 1px var(--border-panel)`
- `var(--shadow-focus)`: `0 0 0 2px var(--bg-base), 0 0 0 4px var(--accent-cyan)`

---

## 5. Component Style Specifications

### 5.1 Collapsible Enterprise Sidebar
- **Default Width:** `260px`
- **Collapsed Width:** `68px`
- **Transition:** `width 0.2s cubic-bezier(0.16, 1, 0.3, 1)`
- **Item States:**
  - Default: `--text-secondary`, transparent background.
  - Hover: `--text-primary`, `rgba(255, 255, 255, 0.04)` background.
  - Active: `--text-primary`, `rgba(56, 189, 248, 0.1)` background, `3px` solid cyan left border accent.

### 5.2 Command Center Header
- **Height:** `56px`
- **Background:** `--bg-surface` with bottom border `1px solid var(--border-panel)`.
- **Elements:**
  - Sidebar toggle button.
  - Dynamic breadcrumb path (`AutoHeal SOC / Live Threat Center`).
  - Search trigger shortcut button (`Ctrl + K` badge).
  - Sentinel status heartbeat pill (pulsing green dot + latency / status).
  - Live UTC + Local ISO Clock.
  - User role badge (`ROLE: SOC ADMIN`).
  - Quick link to ShopSphere storefront (`Target App`).

### 5.3 KPI Telemetry Ribbon
- Multi-column responsive grid (`repeat(auto-fit, minmax(200px, 1fr))`).
- Real-time numerical counter, trend delta pill, historical sparkline placeholder, and descriptive subtitle.
- Strict data binding: No mock numbers.

### 5.4 Forensic Data Table
- Sticky table header with subtle contrast background (`--bg-surface`).
- Monospaced forensic columns (`Timestamp`, `Source IP`, `Incident ID`, `Hash`).
- Interactive row selection triggering the Side-over Event Detail Drawer.
- Live pagination controls with page size selector (`25`, `50`, `100`).

### 5.5 Command Palette (`Ctrl + K`)
- Centered overlay modal (`max-width: 640px`) with high-contrast backdrop blur.
- Live fuzzy-matching input across:
  - Navigation targets (Overview, Events, Incidents, Healing, SOAR, Topology, ShopSphere).
  - Active incidents and threat records.
  - Quick actions (Launch Simulation, Trigger Rollback, Export Incident Report).
- Full keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`, `Escape`).
