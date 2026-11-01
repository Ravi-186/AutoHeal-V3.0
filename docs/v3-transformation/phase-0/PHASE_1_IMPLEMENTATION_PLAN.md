# AutoHeal v3.0 — Phase 0: Phase 1 Implementation Plan & Work Breakdown
**Document ID:** AH-V3-P0-PIP-001  
**Project Baseline:** AutoHeal v2.5.0-PROD  
**Target Milestone:** Phase 1 Design System & Global Application Shell  
**Status:** Certified Implementation Plan  

---

## 1. Executive Summary

Having established the comprehensive frontend inventory, visual flaw audit, route mapping, functionality verification, and technology evaluation in Phase 0, this document outlines the sequential implementation blueprint for **Phase 1: Design System & Global Application Shell**.

Phase 1 establishes the structural, aesthetic, and navigational foundation upon which all subsequent module upgrades operate.

---

## 2. Phase 1 Work Breakdown Structure (WBS)

```
PHASE 1: DESIGN SYSTEM & GLOBAL APPLICATION SHELL
│
├── Step 1.1: Core Design System Tokens (style.css)
│   ├── Declare Obsidian Sentinel color variables (--bg-*, --border-*, --text-*, --status-*)
│   ├── Configure typography hierarchy (Inter + JetBrains Mono)
│   ├── Set standard spacing, radii, elevation shadows, and focus outlines
│   └── Implement WCAG 2.2 AA contrast rules and reduced-motion media query
│
├── Step 1.2: Global Shell Layout Architecture (index.html)
│   ├── Implement .app-shell flex container
│   ├── Build .autoheal-sidebar with brand header, nav items, and footer launcher
│   ├── Implement .autoheal-content-area with sticky .autoheal-topbar
│   └── Construct .autoheal-main responsive content canvas
│
├── Step 1.3: Top Application Bar Controls
│   ├── Sidebar collapse/expand toggle button (#sidebarToggleBtn)
│   ├── Dynamic breadcrumb trail (#breadcrumbActivePage)
│   ├── Global search input / Command Palette trigger button (Ctrl+K)
│   ├── Real-time pulsing Sentinel heartbeat pill (#sentinelStatusPill)
│   ├── Synchronized live UTC + Local clock (#currentTime)
│   └── User profile badge (ROLE: SOC ADMIN)
│
├── Step 1.4: Command Palette Engine (script.js)
│   ├── Keyboard shortcut listeners (Ctrl+K, Cmd+K, Escape)
│   ├── Fuzzy search input filter across all 10 modules and actions
│   └── Arrow key navigation and Enter execution
│
├── Step 1.5: Side-Over Event Detail Drawer Container
│   ├── Backdrop overlay (#eventDrawerBackdrop)
│   ├── Slide-in drawer container (#eventDetailDrawer) with 0.25s transition
│   └── Formatted inspection layout and raw JSON copy engine
│
└── Step 1.6: Quality Assurance & Automated Regression Testing
    ├── Verify template compilation and HTTP 200 delivery (server.py)
    ├── Run full 80-test suite via pytest
    └── Validate Core Web Vitals (LCP < 2.5s, INP < 200ms, CLS 0.00)
```

---

## 3. Implementation Sequence & Verification Gates

### Stage 1: CSS Design System Foundation
- **Target File:** [`web/static/css/style.css`](file:///c:/Users/bobba/Documents/AD/autoheal/web/static/css/style.css)
- **Action:** Embed all Obsidian Sentinel tokens, base resets, focus-visible indicators, typography scales, card layouts, and table styles.
- **Verification Gate 1:** Visual review confirms zero garish neon glows, pure dark backgrounds (`#090D14`), and high contrast text (`16.1:1`).

### Stage 2: HTML Shell & Navigation Refactoring
- **Target File:** [`web/templates/index.html`](file:///c:/Users/bobba/Documents/AD/autoheal/web/templates/index.html)
- **Action:** Re-structure document into the collapsible sidebar shell, sticky topbar, and modular `<section class="workspace-page">` containers.
- **Verification Gate 2:** `GET /` returns HTTP 200 with all 10 workspace section containers present and cleanly hidden via CSS (`display: none`) except the active overview page.

### Stage 3: JavaScript Controller Enhancements
- **Target File:** [`web/static/js/script.js`](file:///c:/Users/bobba/Documents/AD/autoheal/web/static/js/script.js)
- **Action:** Implement `initSidebar()`, `initCommandPalette()`, `initNavigationTabs()`, `switchToTab()`, `openEventDetailDrawer()`, and `copyDrawerRawJson()`.
- **Verification Gate 3:** Keyboard shortcut `Ctrl+K` opens the Command Palette; clicking sidebar items switches views and updates breadcrumbs without page reloads.

### Stage 4: Starlette Template Delivery Fix
- **Target File:** [`server.py`](file:///c:/Users/bobba/Documents/AD/autoheal/server.py)
- **Action:** Fix `templates.TemplateResponse(request=request, name="index.html")` keyword argument calling style.
- **Verification Gate 4:** TestClient verifies `GET /` and `GET /shop` return HTTP 200 with zero server exceptions.

### Stage 5: Full Regression Testing
- **Command:** `pytest tests`
- **Verification Gate 5:** All 80 automated unit, API, simulator, and adversarial pipeline tests pass with 0 failures.

---

## 4. Risk Assessment & Mitigation Strategies

| Risk Description | Severity | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Breaking Existing Element IDs:** Modifying HTML IDs could break legacy JavaScript queries or automated tests. | High | Low | Retain all existing IDs (`statTotalEvents`, `statActiveIncidents`, `postureScoreVal`, `overviewChart`, `eventsTableBody`). Support fallback queries (`#eventsTableBody || #securityEventsTableBody`). |
| **CSS Specificity Clashes:** New layout rules conflicting with legacy styles. | Medium | Low | Use standard CSS custom properties and scoped class names (`.autoheal-sidebar`, `.autoheal-topbar`). |
| **Starlette Template Call Crash:** Newer Starlette versions requiring `request` keyword argument. | High | High | Explicitly call `templates.TemplateResponse(request=request, name="...")` across all routes in `server.py`. |
| **Mobile Layout Breakage:** Complex tables causing horizontal overflow on mobile viewports. | Medium | Low | Enforce `overflow-x: auto` wrappers and collapsible mobile navigation drawer. |
