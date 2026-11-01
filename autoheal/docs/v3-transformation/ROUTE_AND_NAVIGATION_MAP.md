# AutoHeal v3.0 — Route and Navigation Map
**Document ID:** AH-V3-NAV-001  
**Architecture:** Unified Single Page Application (SPA) with Deep Linking & History API  
**Last Updated:** Phase 1 Architecture Transformation  

---

## 1. Application Shell Navigation Structure

The AutoHeal v3.0 SOC ecosystem is organized into 10 enterprise modules accessible via the collapsible vertical sidebar, top breadcrumb bar, and global Command Palette (`Ctrl+K`).

```
+----------------------------------------------------------------------------------------------------+
| TOP APPLICATION BAR (Height: 56px)                                                                 |
| [Sidebar Toggle] [Breadcrumb: AutoHeal > Module] [Ctrl+K Global Search] [Sentinel Pill] [Clock] [Role] [Target Link] |
+------------------------------------+---------------------------------------------------------------+
| COLLAPSIBLE SIDEBAR (260px / 68px) | MAIN WORKSPACE CANVAS                                         |
|                                    |                                                               |
| 1. Overview Dashboard              | Active Workspace Page Module                                  |
| 2. Live Threat Center              | (Overview, Events, Attacks, Incidents, SOAR, Self-Healing,     |
| 3. Attack Simulation Center        | Threat Intel, MITRE Matrix, Asset Topology, Admin/Audit)      |
| 4. Incident Command Center         |                                                               |
| 5. SOAR Automation Center          |                                                               |
| 6. Self-Healing & Remediation      |                                                               |
| 7. Threat Intelligence & IOCs      |                                                               |
| 8. MITRE ATT&CK Matrix             |                                                               |
| 9. Asset & Topology Map            |                                                               |
| 10. Audit & Administration         |                                                               |
|                                    |                                                               |
| [ShopSphere Storefront Link]       |                                                               |
+------------------------------------+---------------------------------------------------------------+
```

---

## 2. Comprehensive Module Route & View Matrix

| # | Module ID | Sidebar Label | Icon Class | View Scope & Capabilities | Data Source Endpoints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `pageOverview` | **Overview Dashboard** | `fas fa-chart-pie` | Executive KPI ribbon, 24h event volume trend chart, threat category distribution doughnut, real-time activity stream, quick actions | `GET /api/security/metrics`<br>`GET /api/security/posture`<br>`GET /api/security/incidents`<br>`GET /api/state` |
| **02** | `pageEvents` | **Live Threat Center** | `fas fa-satellite-dish` | High-throughput telemetry log table, column sorting, category & severity filtering, full-text search, live pagination, Side-over Event Detail Drawer | `GET /api/security/events`<br>`GET /api/security/events?limit=N` |
| **03** | `pageAttackCenter`| **Attack Simulation** | `fas fa-crosshairs` | Scenario test cards (SQLi, XSS, Credential Stuffing, DoS, Admin Probe, Health Cascade), execution config, dry-run toggle, live SSE attack timeline | `POST /api/security/test/run`<br>`POST /api/security/test/stop`<br>`GET /api/security/attack-center/stream` |
| **04** | `pageIncidents` | **Incident Command** | `fas fa-shield-virus` | Triage queue tabs (`ALL`, `OPEN`, `MITIGATING`, `CONTAINED`), deep forensics dossier, attack timeline, raw payload evidence, AI summary, manual notes | `GET /api/security/incidents`<br>`GET /api/security/incidents/{id}/ai-summary`<br>`GET /api/security/incidents/{id}/report` |
| **05** | `pageSoar` | **SOAR Automation** | `fas fa-robot` | Playbook library (Credential Stuffing Quarantine, SQLi AST Auto-Patch, DoS Adaptive Rate-Limit), visual execution flowchart, approval gates | `GET /api/security/posture`<br>`GET /api/security/blocked-clients`<br>`POST /api/security/unblock` |
| **06** | `pageHealing` | **Self-Healing Center**| `fas fa-hand-holding-medical` | Active remediation lifecycle, live AST patch manager (Before vs After diff), dual-probe verification panel (Attacker 403 vs Benign 200), rollback trigger | `GET /api/security/vulnerabilities`<br>`POST /api/security/vulnerabilities/{id}/apply`<br>`POST /api/security/vulnerabilities/{id}/rollback` |
| **07** | `pageThreatIntel`| **Threat Intelligence**| `fas fa-brain` | IOC lookup (IP, domain, hash), reputation scoring, active IP quarantine manager with countdown timer and instant unblock action | `GET /api/security/blocked-clients`<br>`POST /api/security/unblock` |
| **08** | `pageMitre` | **MITRE ATT&CK Matrix**| `fas fa-th` | Interactive ATT&CK matrix columns (Initial Access, Execution, Persistence, Defense Evasion, Credential Access, Impact) with real detection rule coverage | Internal rule mapping + incident correlation |
| **09** | `pageTopology` | **Asset & Topology Map**| `fas fa-network-wired` | Zero-trust asset inventory table, interactive 2.5D/3D network topology visualization with nodes, connections, and threat highlights; 2D table fallback | `GET /api/state`<br>`GET /api/health` |
| **10** | `pageSettings` | **Audit & Admin** | `fas fa-sliders-h` | Immutable audit log viewer, security threshold configuration (rate limit windows, failed login thresholds, quarantine TTL), system diagnostics | `GET /api/health`<br>`GET /api/security/posture` |

---

## 3. Dedicated ShopSphere Storefront Routes (`/shop`)

ShopSphere is the protected e-commerce application running in tandem with AutoHeal.

| View ID / Section | Display Title | Route / State | Core Features |
| :--- | :--- | :--- | :--- |
| `storefront-home` | **ShopSphere Catalogue** | `GET /shop` | Responsive product grid, category tabs (Electronics, Fashion, Home, Security), price range slider, rating filters, search |
| `product-modal` | **Product Detail View** | Modal Overlay | High-res image gallery, stock level indicator, specifications, Add to Cart action |
| `cart-drawer` | **Shopping Cart Drawer** | Slide-over (Right) | Item list, quantity adjustment, subtotal, free delivery threshold meter, Checkout button |
| `checkout-modal` | **Multi-step Checkout** | Multi-step Modal | Shipping address validation, payment method selector (Demo / Cash on Delivery), order confirmation |
| `orders-view` | **Customer Orders** | Sub-view Tab | Order history, order ID, items, status badge, order cancellation action with stock restoration |
| `admin-view` | **Store Administration** | Sub-view Tab | Inventory manager, stock replenishment, real-time store revenue metrics |

---

## 4. Modal Dialogs & Side-Over Drawers

1. **Command Palette (`#cmdPaletteModal`):**
   - Trigger: `Ctrl + K` or clicking search icon in top header.
   - Dismiss: `Escape` or backdrop click.
2. **Event Detail Drawer (`#eventDetailDrawer`):**
   - Trigger: Clicking any row in Live Threat Center (`#eventsTableBody`).
   - Contents: Formatted header, severity pill, source IP, URL path, HTTP method, client headers, raw JSON payload with copy-to-clipboard.
3. **Incident Forensic Dossier (`#incidentDossierModal`):**
   - Trigger: Clicking "Investigate" on any incident card or table row.
   - Contents: Severity, assigned analyst, attack vector timeline, raw payload evidence, grounded AI forensic report, verification status, action buttons (Approve Patch, Rollback, Export PDF).
4. **AST Code Diff Inspector (`#astDiffModal`):**
   - Trigger: Clicking "Inspect AST Diff" in Self-Healing Center.
   - Contents: Side-by-side or unified before/after patch code with syntax highlighting, vulnerability explanation, and test run evidence.

---

## 5. Keyboard Navigation & Accessibility Shortcuts

| Key Combination | Action | Scope |
| :--- | :--- | :--- |
| `Ctrl + K` / `Cmd + K` | Open / Close Command Palette | Global |
| `Escape` | Close any active modal, drawer, or dropdown | Global |
| `Tab` / `Shift + Tab` | Focus sequential interactive elements | Global |
| `1` - `9` (when not in input) | Quick jump to Sidebar Modules 1 through 9 | Global |
| `ArrowUp` / `ArrowDown` | Navigate list items in Command Palette & Tables | Active Container |
| `Enter` | Select / Execute highlighted item | Active Container |
