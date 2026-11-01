# AutoHeal v3.0: Initial UI/UX & Frontend Architecture Audit

**Author:** Principal Product Designer, UI/UX Architect & Frontend Systems Lead  
**Assessment Date:** November 2026  
**Project Phase:** Phase 0 — Workspace Discovery & Baseline Evaluation  
**Target Applications:** AutoHeal Autonomous SOC Platform & ShopSphere E-Commerce  
**Baseline Version:** AutoHeal v2.5.0-PROD (`bf47d7a` / `06bb2e8`)  
**Target Version:** AutoHeal v3.0-ENTERPRISE  
**Classification:** **ENGINEERING & DESIGN SPECIFICATION**

---

## 1. Executive Summary & Discovery Findings

Before proposing or implementing any visual or architectural alterations, an exhaustive audit of the existing repository was performed to identify the actual technology stack, active frontend assets, backend services, database schemas, and integration contracts.

### Discovered Technology Stack Summary
1. **Backend Framework:** **FastAPI 0.162.0** running on Starlette 1.7.0 with Uvicorn 0.54.0 under Python 3.13.7.
2. **Primary Web Applications:**
   - **AutoHeal SOC Sentinel:** Served via FastAPI `server.py` at `GET /` rendering Jinja2 template [`web/templates/index.html`](file:///c:/Users/bobba/Documents/AD/autoheal/web/templates/index.html) with external stylesheet [`web/static/css/style.css`](file:///c:/Users/bobba/Documents/AD/autoheal/web/static/css/style.css) and client controller [`web/static/js/script.js`](file:///c:/Users/bobba/Documents/AD/autoheal/web/static/js/script.js).
   - **ShopSphere E-Commerce:** Served at `GET /shop` rendering [`web/templates/shopsphere.html`](file:///c:/Users/bobba/Documents/AD/autoheal/web/templates/shopsphere.html) as a full-stack, client-rendered storefront and administrative portal.
3. **Secondary Data Science Interface:** **Streamlit 1.64.0** application in [`dashboard/app.py`](file:///c:/Users/bobba/Documents/AD/autoheal/dashboard/app.py) featuring Three.js iframe integration via [`dashboard/background3d.py`](file:///c:/Users/bobba/Documents/AD/autoheal/dashboard/background3d.py) and [`dashboard/assets/scene.html`](file:///c:/Users/bobba/Documents/AD/autoheal/dashboard/assets/scene.html).
4. **Data Visualization Libraries:** Chart.js 4.x (via CDN in web UI), Plotly Express/Graph Objects (in Streamlit).
5. **Real-Time Streaming:** Server-Sent Events (SSE) native streaming at `GET /api/security/attack-center/stream` powered by FastAPI `StreamingResponse` and client-side `EventSource`.
6. **Database Engine:** SQLite 3 in WAL mode (`autoheal/data/shopsphere.db`) with 12 structured relational tables.
7. **Node / NPM Availability:** Node.js v22.20.0 and npm 10.9.3 are available on the host environment, but no Node build tooling was configured in the repository.

---

## 2. Evaluation of Existing Frontend Architectures

### 2.1 The Streamlit Dashboard (`dashboard/app.py`)
* **Strengths:** Rapid data-science prototyping, built-in Plotly charts, Python-native state bindings.
* **Severe Enterprise Limitations:**
  - **Full-Page Rerun Flashing:** Every user interaction or slider change triggers a complete Python script execution and virtual DOM re-render, creating noticeable UI stutter and scroll resets.
  - **No Real-Time SSE/WebSocket Streaming:** Streamlit cannot natively maintain asynchronous persistent event streams or real-time packet timelines without complex workarounds or session hacks.
  - **Rigid Layout & Component Styling:** Overriding Streamlit CSS with `st.markdown('<style>...', unsafe_allow_html=True)` is brittle, breaks on library upgrades, and prevents standard accessible navigation.
  - **Single-Threaded Execution Bottlenecks:** Under multi-user operations, Streamlit's execution loop degrades significantly compared to asynchronous ASGI servers.
* **Verdict:** Streamlit is retained as a secondary data-science exploration tool, but is **insufficient** as the primary enterprise commercial SOC product.

### 2.2 The FastAPI Web Application (`web/templates/index.html` & `static/`)
* **Strengths:**
  - High-performance, low-latency execution directly served by FastAPI ASGI.
  - Native asynchronous event handling (`fetch`, SSE `EventSource`).
  - Pure CSS3 custom properties with zero external build-step compilation overhead.
  - Fast page loads (LCP < 0.5s, no multi-megabyte JavaScript vendor bundle).
* **Current UI/UX Pain Points in v2.5.0:**
  1. **Visual Inconsistency:** Uses a mix of saturated neon cyans (`#00e5ff`), dark slate backgrounds (`#0a1020`), and inconsistent card elevations.
  2. **Navigation Rigidity:** Uses a flat horizontal button list across the top rather than a modern, collapsible enterprise vertical sidebar with breadcrumbs and hierarchical groups.
  3. **Information Density & Discoverability:** The Incident Details tab and Healing tab present dense JSON blocks and nested text without structured timeline steppers or visual investigation flows.
  4. **Lack of Global Search / Command Palette:** No quick-navigation shortcut (Ctrl+K) to find incidents, assets, or run actions.
  5. **Missing Advanced Enterprise Modules:** No dedicated SOAR Playbook builder, no interactive Threat Topology graph, no MITRE ATT&CK technique matrix explorer, and limited Asset Management.
  6. **ShopSphere Visual Identity:** ShopSphere currently looks like a consumer discount portal rather than a sleek, modern commercial e-commerce brand that integrates seamlessly with AutoHeal.

---

## 3. Comprehensive Inventory of Existing Routes & Endpoints

### 3.1 Web Pages & HTML Views
| URL Path | Template File | Application | Description |
| :--- | :--- | :--- | :--- |
| `GET /` | `web/templates/index.html` | AutoHeal SOC | Primary Security Operations Command Center |
| `GET /shop` | `web/templates/shopsphere.html`| ShopSphere | Storefront, product catalog, cart, checkout, admin |
| `GET /api/docs` | Swagger UI | AutoHeal API | Interactive OpenAPI documentation |

### 3.2 Core API Endpoints
* **SOC Telemetry & Incidents:**
  - `GET /api/security/metrics`: KPI summaries (events, incidents, blocked IPs, remediation times).
  - `GET /api/security/events`: Telemetry event log stream with query filters.
  - `GET /api/security/incidents`: Incident listing with status and severity filters.
  - `GET /api/security/incidents/{id}`: Full forensic incident dossier.
  - `GET /api/security/incidents/{id}/report`: Markdown forensic report.
  - `GET /api/security/incidents/{id}/export`: JSON / PDF / Markdown downloads.
  - `GET /api/security/incidents/{id}/ai-summary`: AI-grounded summary with MITRE ATT&CK alignment.
  - `POST /api/security/incidents/{id}/remediate`: Remediation recording and status update.
  - `POST /api/security/incidents/{id}/verify`: Autonomous verification agent execution.
* **Perimeter Quarantine & Threat Testing:**
  - `GET /api/security/blocked-clients`: List active quarantined IPs.
  - `POST /api/security/unblock`: Unblock quarantined IP.
  - `POST /api/security/scan-telemetry`: Trigger sliding-window correlation scan.
  - `POST /api/security/test/run`: Run controlled attack scenario.
  - `POST /api/security/test/stop`: Cancel running attack test.
  - `GET /api/security/attack-center/stream`: Live SSE stream of attack progression.
  - `POST /api/security/test/replay`: Replay comparison (before vs after state).
* **Vulnerability Management:**
  - `GET /api/security/vulnerabilities`: List tracked vulnerabilities and patch proposals.
  - `GET /api/security/vulnerabilities/{id}`: Detailed vulnerability dossier and code diff.
  - `POST /api/security/vulnerabilities/{id}/test`: Run isolated regression test.
  - `POST /api/security/vulnerabilities/{id}/approve`: Operator approval gate.
  - `POST /api/security/vulnerabilities/{id}/apply`: Apply surgical code patch with verification.
  - `POST /api/security/vulnerabilities/{id}/rollback`: Revert code patch to previous baseline.
* **Security Posture & Network State:**
  - `GET /api/security/posture`: Transparent 0-100 defense score with pillar breakdown.
  - `GET /api/state`: Monitored assets, roles, IP addresses, threat states, zones, and risk scores.
  - `GET /api/health`: Service health and model status.
* **ShopSphere E-Commerce Endpoints:**
  - `GET /api/shop/products`, `GET /api/shop/products/{id}`, `GET /api/shop/categories`
  - `POST /api/shop/auth/register`, `POST /api/shop/auth/login`, `GET /api/shop/auth/me`, `POST /api/shop/auth/logout`
  - `GET /api/shop/cart`, `POST /api/shop/cart/add`, `POST /api/shop/cart/update`, `POST /api/shop/cart/remove`, `POST /api/shop/cart/clear`
  - `GET /api/shop/wishlist`, `POST /api/shop/wishlist/toggle`
  - `POST /api/shop/checkout`, `GET /api/shop/orders/{id}`, `POST /api/shop/orders/{id}/cancel`
  - `GET /api/admin/metrics`, `GET /api/admin/orders`, `POST /api/admin/products`, `PUT /api/admin/products/{id}`, `GET /api/admin/audit-logs`

---

## 4. Modernization Strategy for AutoHeal v3.0

### Strategic Architectural Decision: Enhanced Modular SPA
Rather than introducing heavy external JavaScript framework dependencies (such as React or Next.js) that would require a complex Node compilation toolchain, break the clean single-command FastAPI deployment, and invalidate existing Starlette middleware, we will execute an **architectural evolution of the native FastAPI Web Application**:
1. **Design System "Obsidian Sentinel":** Implement a comprehensive CSS design token system with dark-mode dominance (`#090D14`, `#101722`, `#151F2C`, `#253344`) and precise typography (Inter + JetBrains Mono).
2. **Enterprise Command Shell:** Modernize `index.html` into a professional SOC shell with a collapsible vertical sidebar, top application bar, breadcrumbs, command palette (Ctrl+K), notification center, and role-aware navigation.
3. **10 Dedicated Advanced SOC Modules:**
   - 1. Executive SOC Overview & Dynamic KPI Ribbon
   - 2. Live Threat Center (real-time virtualized event explorer, filters, detail drawer)
   - 3. Attack Simulation Center (SSE live timeline, risk labels, before/after diffs)
   - 4. Incident Command Center (structured investigation timeline, forensic evidence, analyst notes)
   - 5. SOAR Automation Center (interactive visual playbook workflow with real executing actions)
   - 6. Self-Healing Center (signature feature: active remediation lifecycle, before/after code diffs, verification status)
   - 7. Threat Intelligence Center (IOC lookups, IP/domain reputation, enrichment data)
   - 8. MITRE ATT&CK Matrix Explorer (interactive technique grid mapped to implemented detections)
   - 9. Asset Management (real monitored assets, zero-trust zones, posture, and risk scores)
   - 10. Reports & Administration (audit log explorer, RBAC management, PDF/Markdown report generation)
4. **Interactive 2.5D / 3D Threat Topology:** Integrate an interactive canvas/SVG and Three.js topology visualization directly into the web application, mapping actual monitored assets, threat connections, and quarantine states.
5. **ShopSphere UI Elevation:** Modernize `shopsphere.html` with an independent, clean, premium e-commerce design language, responsive product catalog, dynamic filtering, quick-view modals, and cart drawer.

---

## 5. Non-Regression & Engineering Safeguards
- **Zero API Contract Breaking:** All existing API endpoints, query parameters, and response schemas remain 100% backward-compatible.
- **Security Hardening Preserved:** All v2.5.0 security remediations (token entropy, 7-day TTL, constant-time compare, server-side logout, defense headers, atomic checkout) are strictly preserved.
- **No Mock or Fabricated Metrics:** Every metric, chart series, and status badge binds to verified backend endpoints.
