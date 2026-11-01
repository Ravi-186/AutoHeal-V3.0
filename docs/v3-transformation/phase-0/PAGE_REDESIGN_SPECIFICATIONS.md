# AutoHeal v3.0 — Phase 0: Page-by-Page Redesign Specifications
**Document ID:** AH-V3-P0-PRS-001  
**Project Baseline:** AutoHeal v2.5.0-PROD  
**Target Visual Theme:** Obsidian Sentinel  
**Status:** Certified Engineering Blueprint  

---

## 1. Overview of Redesign Specifications

This document defines the architectural, data, interaction, and responsive specifications for all 22 screens across the AutoHeal v3.0 SOC platform and ShopSphere E-Commerce ecosystem.

---

## PART I: AUTOHEAL ENTERPRISE SOC MODULES

### 1. SOC Executive Overview (`pageOverview`)
- **Layout:** Executive header ribbon -> 4-card KPI summary ribbon -> Autonomous Security Posture Scorecard -> 2-column lower grid (Recent Telemetry Table + Chart.js Trend Canvas).
- **Components:** Total Events counter, Active Incidents tile, Quarantined IPs tile, Contained Threats tile, circular posture gauge, 5 defense pillar tracks, velocity line chart with peak threat badge.
- **Data Requirements:** Aggregate telemetry metrics, active incidents count, active quarantine list length, security posture formula breakdown.
- **User Interactions:** "Launch Security Test" (switches to Attack Center), "Refresh Telemetry" (re-polls metrics), "Recalculate Posture" (re-runs posture formula).
- **API Dependencies:** `GET /api/security/metrics`, `GET /api/security/posture`, `GET /api/security/incidents?limit=5`.
- **Permissions:** Read-only for SOC Operators; Full Access for SOC Admins.
- **Responsive Behavior:** 4-column KPI grid reflows to 2 columns on tablet and 1 column on mobile. Lower 2-column grid stacks vertically on screens $< 1024\text{px}$.
- **Loading & Error States:** Table rows render spinner during initial load; failure displays retry button with toast notification.

---

### 2. Live Threat Center (`pageEvents`)
- **Layout:** Header with export controls -> Multi-column filter bar -> Full-width high-throughput telemetry table with pagination footer -> Side-Over Event Detail Drawer.
- **Components:** Category filter dropdown, Severity filter dropdown, Real-time text search input, Auto-refresh toggle button, Telemetry data table with sortable headers, Export CSV button.
- **Data Requirements:** Paginated array of security events (event ID, timestamp, category, client IP, HTTP method, path, status code, severity, correlation ID).
- **User Interactions:** Multi-filter selection, client-side keyword search, row click to open event drawer, "Copy JSON" action in drawer, "Export CSV" trigger.
- **API Dependencies:** `GET /api/security/events?limit=100&event_type=...&severity=...`.
- **Permissions:** Analyst / Operator.
- **Responsive Behavior:** Filter inputs stack vertically on mobile. Table maintains horizontal scroll without breaking viewport boundaries.
- **Loading & Error States:** Centered spinner during API fetch; explicit empty state message when no events match filter criteria.

---

### 3. Attack Simulation Center (`pageAttackCenter`)
- **Layout:** Executive header ribbon with replay trigger -> 2-column grid (Dispatch Configuration Panel + Live Stepper & Terminal Console) -> Bottom Healing Result Evidence Card.
- **Components:** Scenario dropdown (6 scenarios), Intensity range slider (1 to 5), Execution mode radios (Live vs Dry-run), "Launch Simulation" button, "Abort Test" button, 5-stage visual stepper, Monospaced terminal container, Dual-probe verification evidence card.
- **Data Requirements:** Real-time Server-Sent Events (SSE) streaming JSON event messages (`phase`, `request`, `detection`, `verification`, `complete`).
- **User Interactions:** Scenario selection, intensity adjustment, launching simulation, aborting simulation, replaying attack against defense barrier.
- **API Dependencies:** `POST /api/security/test/run`, `POST /api/security/test/stop`, `POST /api/security/test/replay`, `GET /api/security/attack-center/stream`.
- **Permissions:** Restricted to authorized SOC Engineers; targets strictly validated to localhost boundary.
- **Responsive Behavior:** Side-by-side grid stacks into a single column on tablet/mobile. Stepper wraps responsively.
- **Loading & Error States:** Buttons disable and show spinner while test is active; terminal logs errors in red text.

---

### 4. Incident Command Center (`pageIncidents`)
- **Layout:** Header ribbon -> Status filter tabs (`ALL`, `OPEN`, `MITIGATING`, `CONTAINED`) -> Incidents summary table -> Expandable Forensic Dossier Panel.
- **Components:** Triage table (Incident ID, Detected, Vector, Target Endpoint, Severity, Action Taken, Verification Status), "Inspect" action button.
- **Data Requirements:** Incident records list with correlation IDs, affected endpoints, mitigation history.
- **User Interactions:** Status tab filtering, clicking "Inspect" to expand the dossier panel.
- **API Dependencies:** `GET /api/security/incidents`.
- **Permissions:** SOC Analyst / Incident Responder.
- **Responsive Behavior:** Table scrolls horizontally on small screens; long paths truncate with ellipsis.
- **Loading & Error States:** Empty state indicates "No active incidents. Perimeter clear."

---

### 5. Incident Investigation Workspace (`#incidentDetailPanel`)
- **Layout:** Integrated dossier workspace embedded in Incident Command Center or opened via dedicated modal.
- **Components:** Dossier header with incident identifier and severity pill, Attack Vector Timeline stepper, Evidence Payload viewer, Grounded AI Root-Cause Summary card with MITRE ATT&CK alignment.
- **Data Requirements:** Deep incident metadata, raw attack payload evidence, AI summary text, MITRE technique ID.
- **User Interactions:** Step-by-step timeline review, payload copying, closing dossier view.
- **API Dependencies:** `GET /api/security/incidents/{id}`, `GET /api/security/incidents/{id}/ai-summary`.
- **Permissions:** SOC Analyst / Lead SecOps.
- **Responsive Behavior:** Side-by-side evidence and AI summary stack vertically on tablets and mobile screens.

---

### 6. SOAR Automation Center (`pageSoar`)
- **Layout:** Header ribbon -> Visual Playbook Execution Flowchart card -> Active Dynamic IP Quarantine Registry card.
- **Components:** 5-node visual pipeline (Ingress Telemetry -> ML & Rule Engine -> Dynamic Quarantine -> AST Self-Healing -> Dual-Probe Verification), Active quarantine data table, "Unblock All IPs" bulk purge action, individual "Unblock" row buttons.
- **Data Requirements:** Active blocked clients list (IP, reason, blocked_at, expires_at, block_count).
- **User Interactions:** Visual inspection of active playbook logic, unblocking specific IPs, purging all bans.
- **API Dependencies:** `GET /api/security/blocked-clients`, `POST /api/security/unblock`.
- **Permissions:** SOC Admin (unblock actions require elevated privileges).
- **Responsive Behavior:** Playbook flowchart scrolls horizontally with touch momentum; quarantine table reflows cleanly.

---

### 7. Self-Healing Center (`pageHealing`)
- **Layout:** Header ribbon -> Verified AST Patch Inventory card -> Expandable AST Code Patch Inspector (`#vulnDrawerPanel`).
- **Components:** Patch inventory table (Vuln ID, CWE/Type, Component Path, Status, Regression Test Result, Action Buttons), Before (Vulnerable Code) vs After (Patched AST Code) diff viewer, Action buttons: "Run Isolated Test", "Approve Patch", "Apply Live", "Rollback".
- **Data Requirements:** Vulnerability inventory records, before/after code diff text, test execution status.
- **User Interactions:** Inspecting code diff, triggering regression test, approving patch gate, applying patch, rolling back patch.
- **API Dependencies:** `GET /api/security/vulnerabilities`, `GET /api/security/vulnerabilities/{id}`, `POST .../test`, `POST .../approve`, `POST .../apply`, `POST .../rollback`.
- **Permissions:** Lead SecOps Engineer (patch approval & application restricted).
- **Responsive Behavior:** Side-by-side diff boxes stack vertically on mobile screens.

---

### 8. Threat Intelligence Center (`pageThreatIntel`)
- **Layout:** Header ribbon -> 2-column grid (IOC Reputation Lookup Panel + Observed Attacker Vectors Table).
- **Components:** Indicator search input (IP, domain, URL, or hash), "Query" button, Reputation scorecard (Threat Score 0-100, Risk Level, Quarantine Status, Correlated Records count), Observed attacker table.
- **Data Requirements:** Active quarantine records and observed telemetry event history.
- **User Interactions:** Submitting search query, viewing risk evaluation, inspecting attacker profiles.
- **API Dependencies:** `GET /api/security/blocked-clients`, client-side correlation against `allFetchedEvents`.
- **Permissions:** Open to all SOC roles.
- **Responsive Behavior:** 2-column grid stacks into a single column on tablet and mobile.

---

### 9. MITRE ATT&CK Explorer (`pageMitre`)
- **Layout:** Header ribbon -> Full-width 5-column ATT&CK Matrix Grid card.
- **Components:** 5 Tactic Columns: Initial Access, Execution, Credential Access, Defense Evasion, Impact. Technique cards displaying Technique ID (e.g. `T1190`, `T1059.007`), name, and green coverage tags indicating verified active detection rules.
- **Data Requirements:** Detection rule registry and incident mappings.
- **User Interactions:** Hovering over technique cards to view coverage descriptions.
- **API Dependencies:** Detection rule registry (client-side map validated against active middleware rules).
- **Permissions:** Open to all SOC roles.
- **Responsive Behavior:** Grid supports horizontal panning on screens $< 1024\text{px}$.

---

### 10. Asset Management (`pageTopology`)
- **Layout:** Header ribbon with view mode toggle -> Interactive 3D WebGL Topology Viewport (`#topologyCanvas`) -> Accessible 2D Monitored Asset Directory table (`#topologyTableView`).
- **Components:** Three.js 3D canvas rendering device nodes and connections with real-time threat pulsing, Legend box, "Switch to 2D Table" toggle button, Tabular asset directory (ID, Role, Zone, IP, Security State, Risk Score).
- **Data Requirements:** Live monitored devices array from `/api/state`.
- **User Interactions:** Rotating/panning 3D canvas, toggling between 3D canvas and accessible 2D table view.
- **API Dependencies:** `GET /api/state`.
- **Permissions:** Open to all SOC roles.
- **Responsive Behavior:** WebGL canvas auto-resizes to container width; 2D table provides complete mobile accessibility.

---

### 11. Reports and Analytics (`pageReports`)
- **Layout:** Header ribbon with refresh trigger -> Formal Incident Reports table.
- **Components:** Reports table with Report ID, Incident ID, Timestamp, Attack Vector, Severity, Resolution, and "Download" triggers.
- **Data Requirements:** Persisted incident reports list.
- **User Interactions:** Refreshing reports list, downloading markdown/JSON reports.
- **API Dependencies:** `GET /api/security/incidents`.
- **Permissions:** SOC Operator / Auditor.
- **Responsive Behavior:** Table scrolls horizontally on narrow viewports.

---

### 12. User Administration (`pageSettings` Tab A)
- **Layout:** Embedded in Admin & Audit module.
- **Components:** User profile card, active role badge (`SOC ADMIN`), permission scope indicators.
- **Data Requirements:** Active session user profile.
- **User Interactions:** Viewing active role and permissions.
- **Permissions:** Admin.

---

### 13. Audit Log Explorer (`pageSettings` Tab B)
- **Layout:** Embedded in Admin & Audit module.
- **Components:** Immutable audit table displaying operational events (Patch applied, IP unblocked, Attack test launched).
- **Data Requirements:** System audit log records.
- **Permissions:** Auditor / Admin.

---

### 14. System Health Diagnostics (`pageSettings` Tab C)
- **Layout:** System Diagnostics card in Admin & Audit module.
- **Components:** Overall health status pill (`OPERATIONAL`), Service health items list (FastAPI Server, SQLite DB, ML Engine, AST Engine, Loopback Target Boundary).
- **Data Requirements:** Health check payload from `/api/health`.
- **User Interactions:** "Health Diagnostics" trigger button.
- **API Dependencies:** `GET /api/health`.
- **Permissions:** Open to all roles.

---

### 15. Security Threshold Settings (`pageSettings` Tab D)
- **Layout:** Active Defense Thresholds card.
- **Components:** Failed Login Threshold input (AUTH-001), Rate-Limit Window input (RATE-001), Quarantine TTL input, "Purge All Active IP Bans" danger button.
- **Data Requirements:** Runtime defense parameters.
- **User Interactions:** Purging all IP bans, reviewing threshold configurations.
- **API Dependencies:** `POST /api/security/unblock`.
- **Permissions:** Admin.

---

## PART II: SHOPSPHERE E-COMMERCE STOREFRONT

### 16. ShopSphere Storefront Homepage (`/shop`)
- **Layout:** Sticky top navigation bar -> Category pills strip -> Promotional banner card -> Multi-column main content grid (Left sidebar filters + Right product catalogue grid).
- **Components:** Search bar, Cart badge, Wishlist badge, Category chips, Promo banner, Product cards grid.
- **Data Requirements:** Product catalog array from `/api/shop/products`.
- **User Interactions:** Category selection, keyword search, price slider filtering.
- **API Dependencies:** `GET /api/shop/products`.
- **Permissions:** Public consumer.

---

### 17. Product Catalogue & Grid View
- **Layout:** Responsive CSS Grid (`repeat(auto-fill, minmax(240px, 1fr))`).
- **Components:** Product cards featuring high-res SVG image, category tag, title, price in INR, rating stars, stock badge, "Add to Cart" button, "Buy Now" button.
- **Data Requirements:** Product list with stock counts and pricing.
- **User Interactions:** Adding item to cart, clicking card to open modal.
- **API Dependencies:** `GET /api/shop/products`.

---

### 18. Product Details Modal (`#productModal`)
- **Layout:** Centered modal overlay (`max-width: 800px`) with 2-column layout (Left: Product Image Gallery, Right: Details & Purchase Actions).
- **Components:** High-res image display, stock availability indicator, price, product specifications list, quantity selector, "Add to Cart" button.
- **Data Requirements:** Single product details record from `/api/shop/products/{id}`.
- **User Interactions:** Quantity adjustment, closing modal with `Escape` or backdrop click.
- **API Dependencies:** `GET /api/shop/products/{id}`.

---

### 19. Shopping Cart Drawer (`#cartDrawer`)
- **Layout:** Slide-over right drawer (`width: 440px; max-width: 90vw`).
- **Components:** Header with item count, Itemized cart rows (Image, Title, Price, Quantity `+`/`-` buttons, Remove button), Free Delivery Progress Bar, Subtotal summary, "Proceed to Checkout" button.
- **Data Requirements:** Client-side cart state and persisted session records.
- **User Interactions:** Quantity increments/decrements, item removal, launching checkout.

---

### 20. Multi-step Checkout Modal (`#checkoutModal`)
- **Layout:** Centered modal overlay with step progression indicators (1. Shipping Address -> 2. Payment Method -> 3. Order Summary).
- **Components:** Full Name, Phone, Email, Address, PIN Code form fields, Payment selector (Demo Checkout / Cash on Delivery), Order Total breakdown, "Place Order" button.
- **Data Requirements:** Active cart contents and shipping details.
- **User Interactions:** Form input validation, selecting payment, placing order.
- **API Dependencies:** `POST /api/shop/orders`.

---

### 21. Customer Account & Authentication (`#authModal`)
- **Layout:** Centered auth modal with Login / Register tabs.
- **Components:** Email input, Password input, Demo credentials quick-fill buttons, "Sign In" button.
- **Data Requirements:** User authentication payload.
- **User Interactions:** Submitting credentials, switching between login and register.
- **API Dependencies:** `POST /api/shop/auth/login`.

---

### 22. Order Management & Store Admin (`#adminModal`)
- **Layout:** Admin modal accessible to users with `role: admin`.
- **Components:** Store metrics summary (Revenue, Total Orders, Low Stock Items), Product stock management table with editable stock quantity inputs and "Update Stock" buttons.
- **Data Requirements:** Store statistics and complete product inventory.
- **User Interactions:** Updating stock levels, reviewing store metrics.
- **API Dependencies:** `GET /api/shop/admin/stats`, `POST /api/shop/admin/stock`.
- **Permissions:** Admin role strictly enforced by backend.
