# AutoHeal v3.0 — Phase 0: Complete Frontend Inventory
**Document ID:** AH-V3-P0-INV-001  
**Project Baseline:** AutoHeal v2.5.0-PROD (`bf47d7a` / `06bb2e8`)  
**Assessment Date:** November 1, 2026  
**Status:** Certified Audit  

---

## 1. Executive Summary

This document establishes the exhaustive baseline inventory of every frontend asset, template, stylesheet, script, WebGL component, and presentation layer in the AutoHeal and ShopSphere repository. 

The platform currently comprises two distinct frontend presentation systems:
1. **Primary FastAPI Web Application (`autoheal/web/`):** High-throughput, low-latency Single Page Application (SPA) providing the AutoHeal SOC Sentinel Console at `GET /` and the Flipkart-style ShopSphere e-commerce storefront at `GET /shop`.
2. **Streamlit Data Science & Security Dashboard (`autoheal/dashboard/`):** Python-driven data exploration, Plotly analytics, and 3D WebGL background visualization suite running as a secondary administrative analysis tool.

---

## 2. Exhaustive File & Asset Manifest

### 2.1 Primary Web Application Assets (`autoheal/web/`)

| File Path | File Size | Line Count | Format / Tech | Role & Primary Functionality |
| :--- | :--- | :--- | :--- | :--- |
| `web/templates/index.html` | ~72 KB | 794 lines | Jinja2 / HTML5 | Main AutoHeal SOC Sentinel workspace shell, containing all 10 module layouts, modals, and drawers. |
| `web/templates/shopsphere.html`| ~99 KB | 2,583 lines | Jinja2 / HTML5 | Standalone Flipkart-style e-commerce storefront, catalog grid, cart drawer, checkout modal, and store admin. |
| `web/static/css/style.css` | ~28 KB | 1,024 lines | Vanilla CSS3 | Core design system stylesheet, custom properties, typography, cards, tables, drawers, and animations. |
| `web/static/js/script.js` | ~98 KB | 2,265 lines | Vanilla ES6+ JS | Frontend controller: navigation, polling, SSE streaming, Chart.js trends, Three.js topology, and API clients. |
| `web/static/img/bg.jpg` | ~739 KB | Binary (JPEG) | Static Image | Background image asset referenced in legacy CSS layouts. |

### 2.2 Streamlit Security & Data Science Dashboard (`autoheal/dashboard/`)

| File Path | File Size | Line Count | Format / Tech | Role & Primary Functionality |
| :--- | :--- | :--- | :--- | :--- |
| `dashboard/app.py` | ~71 KB | 1,375 lines | Python / Streamlit | 7-tab security analytics console with Plotly gauges, LangGraph reasoning displays, and attack simulations. |
| `dashboard/background3d.py` | ~8.3 KB | 172 lines | Python / HTML | Generates dynamic Three.js WebGL particle background and embeds it into Streamlit via `st.components.v1.html`. |
| `dashboard/attack_path3d.py` | ~0.7 KB | 23 lines | Python / Component | Custom Streamlit component wrapper for rendering 3D attack path topology. |
| `dashboard/assets/scene.html` | ~13 KB | 284 lines | Standalone HTML | Three.js interactive 3D particle sphere and node visualization embedded in Streamlit. |
| `dashboard/assets/attack_path_component/index.html` | ~6.3 KB | 175 lines | HTML / Three.js | WebGL force-directed 3D graph renderer visualizing compromised network device paths. |
| `dashboard/assets/bg.jpg` | ~929 KB | Binary (JPEG) | Static Image | Dark textured background image for Streamlit canvas. |

---

## 3. Screen & View Inventory

### 3.1 AutoHeal SOC Web Console Screens (`index.html`)

| Screen / Workspace ID | Display Label | DOM Selector | Core Functionality | Active Data Source |
| :--- | :--- | :--- | :--- | :--- |
| **W-01** | Overview Dashboard | `#pageOverview` | KPI ribbon, Security Posture Integrity gauge, recent telemetry events, velocity chart | `/api/security/metrics`<br>`/api/security/posture`<br>`/api/security/incidents` |
| **W-02** | Live Threat Center | `#pageEvents` | Real-time event explorer table, multi-select filters, search input, pagination | `/api/security/events` |
| **W-03** | Attack Simulation Center | `#pageAttackCenter` | Scenario selection (6 tests), intensity slider, dry-run mode, 5-stage SSE stepper, terminal logs | `/api/security/test/run`<br>`/api/security/test/stop`<br>`/api/security/attack-center/stream` |
| **W-04** | Incident Command Center | `#pageIncidents` | Triage queue, incident dossier workspace, attack timeline, evidence inspector, AI summary | `/api/security/incidents`<br>`/api/security/incidents/{id}` |
| **W-05** | SOAR Automation Center | `#pageSoar` | Visual 5-node playbook flowchart, dynamic IP quarantine registry, instant unblock trigger | `/api/security/blocked-clients`<br>`/api/security/unblock` |
| **W-06** | Self-Healing Center | `#pageHealing` | Verified AST patch inventory, code diff viewer, dual-probe verification, atomic rollback | `/api/security/vulnerabilities`<br>`/api/security/vulnerabilities/{id}/*` |
| **W-07** | Threat Intelligence & IOCs | `#pageThreatIntel` | IOC search (IP, domain, hash), reputation scorecard, observed adversary vector profiles | `/api/security/blocked-clients`<br>`/api/security/events` |
| **W-08** | MITRE ATT&CK Matrix | `#pageMitre` | 5-tactic matrix grid mapping verified detection rules (T1190, T1059.007, T1110, T1078, T1499) | Detection rule registry & incidents |
| **W-09** | Asset & Topology Map | `#pageTopology` | Interactive Three.js WebGL network topology canvas with node pulsing; accessible 2D table fallback | `/api/state` |
| **W-10** | Incident Reports | `#pageReports` | Export-ready incident reports list with timestamp, vector, severity, and download triggers | `/api/security/incidents` |
| **W-11** | Administration & Audit | `#pageSettings` | Security threshold configuration, system diagnostics health matrix, target boundary status | `/api/health` |

### 3.2 Modal & Side-Drawer Components (`index.html`)

| Component ID | DOM Selector | Trigger Mechanism | Contents & Actions |
| :--- | :--- | :--- | :--- |
| **M-01** | Global Command Palette | `#cmdPaletteBackdrop` | Keyboard `Ctrl+K` or search trigger button | Fuzzy search input matching workspaces, quick actions, recent incidents; arrow key navigation |
| **M-02** | Event Detail Drawer | `#eventDetailDrawer` | Clicking any row in `#eventsTableBody` | Request metadata, client IP, path, headers, formatted payload, raw JSON pre with copy button |
| **M-03** | Incident Dossier Panel | `#incidentDetailPanel` | Clicking "Inspect" on an incident | Forensic attack timeline, evidence payload inspector, grounded AI root-cause analysis |
| **M-04** | AST Code Diff Inspector | `#vulnDrawerPanel` | Clicking "Inspect Diff" on AST patch | Side-by-side Before (Vulnerable) vs After (Patched) code view with regression test button |

### 3.3 ShopSphere E-Commerce Views (`shopsphere.html`)

| Screen / View ID | Component Name | DOM Selector | Functionality | Data Source |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Storefront Homepage | `.main-container` | Responsive product catalogue, category pills, promo banner, search bar | `/api/shop/products` |
| **S-02** | Product Quick View | `#productModal` | High-res gallery, stock counter, specifications, "Add to Cart", "Buy Now" | `/api/shop/products/{id}` |
| **S-03** | Shopping Cart Drawer | `#cartDrawer` | Slide-over cart, quantity adjustment, subtotal, free delivery progress meter | In-memory session / `/api/shop/cart` |
| **S-04** | Wishlist Drawer | `#wishlistDrawer` | Saved items, quick move-to-cart action | In-memory session |
| **S-05** | Multi-step Checkout | `#checkoutModal` | Address form, shipping options, payment method selector (Demo / COD) | `/api/shop/orders` |
| **S-06** | Order Confirmation | `#orderSuccessModal` | Order ID, items summary, delivery estimation, stock reduction confirmation | `/api/shop/orders/{id}` |
| **S-07** | User Authentication | `#authModal` | Login / Register modal, demo credentials autofill | `/api/shop/auth/login` |
| **S-08** | Store Administration | `#adminModal` | Product inventory table, stock level replenishment inputs, store revenue stats | `/api/shop/admin/*` |
| **S-09** | Live AutoHeal Monitor | `#autohealMonitorPanel` | Floating bottom console displaying real-time security events & AST fix buttons | `/api/security/events` |

### 3.4 Streamlit Analytics Tabs (`dashboard/app.py`)

| Tab ID | Tab Display Title | Core Components | Data Dependencies |
| :--- | :--- | :--- | :--- |
| **ST-01** | SOC Command Center | Posture gauge (Plotly), live telemetry counters, threat velocity sparklines | SQLite DB, network simulator |
| **ST-02** | Live AppSec Test Runner | Scenario selection, target parameter inputs, live attack injection execution | `ShopSphereSecurityTester` |
| **ST-03** | LangGraph Agent Reasoning | Multi-agent state visualization (Detection -> Response -> Verification) | LangGraph `AutoHealGraph` state |
| **ST-04** | 3D Topology & Attack Path | Force-directed 3D network topology graph with infected node highlighting | `extract_attack_path` |
| **ST-05** | Incident Triage & Forensics | Dataframe table of correlated security incidents, severity filters | SQLite `security_incidents` |
| **ST-06** | Vulnerabilities & Patches | Surgical AST code patches, before/after diffs, approval checkboxes | `VulnerabilityManager` |
| **ST-07** | SOAR Policies & Governance | Policy toggle modes (Autonomous, HITL, Audit), rate-limit tuning | Streamlit session state |

---

## 4. Third-Party Libraries & Asset Dependencies

| Library / Resource | Version | Source | Usage Scope | Loading Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **FontAwesome** | 6.4.0 | cdnjs CDN | UI glyphs, navigation icons, status dots | `<link rel="stylesheet">` |
| **Google Fonts (Inter)** | Variable | Google Fonts CDN | General interface typography, headings, tables | `@import url(...)` |
| **Google Fonts (JetBrains Mono)** | Variable | Google Fonts CDN | Monospaced forensic logs, hashes, IPs, diffs | `@import url(...)` |
| **Chart.js** | Latest (v4.x) | jsdelivr CDN | Real-time velocity stream chart (`#overviewChart`) | `<script src="...">` |
| **Three.js** | r128 | cdnjs CDN | 3D WebGL network topology canvas (`#topologyCanvas`) | `<script src="...">` |
| **jQuery** | 3.7.1 | code.jquery.com | Toastr dependency & DOM helpers | `<script src="...">` |
| **Toastr.js** | 2.1.4 | jsdelivr CDN | Real-time security alert toasts & operational feedback| `<script src="...">` + CSS |
| **Plotly** | 5.x | PyPI / Python | Streamlit gauge and trend charts | Python dependency in `dashboard/` |
