# AutoHeal v3.0 — End-User Operations Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Audience:** Security Analysts, SOC Operators, and E-Commerce Shoppers  
**Date:** November 1, 2026  

---

## 1. Introduction

This guide provides operational walkthroughs for both user roles interacting with the platform:
1. **The SOC Security Analyst:** Operating the AutoHeal cybersecurity command portal (`/dashboard`).
2. **The E-Commerce Shopper:** Experiencing the ShopSphere consumer storefront (`/shop`).

---

## 2. Part 1: Security Analyst Workflow (AutoHeal SOC Portal)

The AutoHeal command portal is accessible at `http://localhost:8000/dashboard` and styled in the **Obsidian Sentinel** cyber defense theme.

### A. Navigation & Global Controls
- **Collapsible Sidebar:** Click the chevron toggle icon or press `[` to collapse the sidebar for wider forensic tables.
- **Global Command Palette:** Press `Ctrl + K` at any time to open the omni-search modal. Type destination keywords (e.g. `Threat`, `Incidents`, `SOAR`, `Topology`) to jump directly.
- **Heartbeat & Telemetry Monitor:** The glowing radar indicator in the top right confirms active connection to the backend telemetry stream.

### B. Executive SOC Overview
- **Time Range Filtering:** Select `1h`, `24h`, `7d`, or `all` to dynamically aggregate security event metrics.
- **KPI Monitoring:** Review real-time cards tracking Total Events, Active Incidents, MTTD (1.8s), MTTR (1.2s), and System Availability.
- **Timeline Interactivity:** Hover over data points on the Event Volume Timeline to inspect exact event counts per category. Click category legend chips to toggle filters.

### C. Live Threat Center & Event Explorer
- **Real-Time Stream:** Live events ingested from WAF middleware stream into the table in real time via Server-Sent Events.
- **Event Inspection:** Click any row in the event explorer to open the **5-Tab Forensic Drawer**:
  - *Tab 1 (Overview):* Identifies source IP, target endpoint, and attack categorization.
  - *Tab 2 (Evidence):* Inspects raw query strings and regex trigger tokens (e.g. `' OR 1=1--`).
  - *Tab 3 (Detection):* Cites MITRE ATT&CK technique and rule confidence gauge.
  - *Tab 4 (Correlation):* Automatically groups related events sharing the same trace ID or IP.
  - *Tab 5 (Raw Event):* Copy sanitized JSON payloads for external ticket creation.

### D. Incident Command & Triage
1. Navigate to **Incident Center** (`#pageIncidents`).
2. Click on an incident row to inspect the full incident dossier.
3. Advance lifecycle status using the status buttons:
   - `NEW` -> `TRIAGED` (Acknowledge and prioritize)
   - `TRIAGED` -> `INVESTIGATING` (Assign to analyst)
   - `INVESTIGATING` -> `CONTAINMENT` (Deploy perimeter IP ban or rate limit)
   - `CONTAINMENT` -> `VERIFICATION` (Run dual-probe synthetic check)
   - `VERIFICATION` -> `RESOLVED` (Provide resolution notes and close)
4. Click **Generate Report** to download an executive Markdown summary.

### E. Visual SOAR Automation & Approval Gates
- **Playbook Canvas:** Navigate to **SOAR Automation** to view visual node workflows.
- **Human Approval Gates:** When a playbook with an approval gate executes, the workflow pauses in status `WAITING_FOR_APPROVAL`.
- **Authorizing Action:** Review the proposed action in the **Pending Approvals** tray and click **Approve** to resume automated execution.

### F. 3D Threat Topology
- **Interactive Orbit:** Left-click and drag to rotate the spatial graph; scroll wheel to zoom; right-click to pan.
- **Node Selection:** Click any red or purple node to view asset metadata, connection hops, and calculated blast radius.
- **2D Accessible Fallback:** Click the "Table View" toggle if 3D WebGL acceleration is unavailable.

### G. AI SOC Copilot
- Click the Copilot chat button in the bottom-right corner.
- Enter queries such as:
  - *"Summarize incident INC-2026-D6DC8C55 and show grounded evidence."*
  - *"What playbooks are recommended for this SQL injection attempt?"*
- Copilot generates responses with clickable database citations referencing concrete event and rule records.

---

## 3. Part 2: Consumer Shopper Workflow (ShopSphere Storefront)

The ShopSphere storefront is accessible at `http://localhost:8000/shop`.

### A. Browsing & Product Discovery
- **Category Pills:** Click category chips (Electronics, Audio, Wearables, Accessories) to filter products instantly.
- **Search:** Enter search terms into the top search bar (e.g. `AirPods`, `Watch`, `Headphones`) to filter by title or description.
- **Price Range & Sorting:** Use the price slider to constrain budgets, and sort by Price: Low-to-High, High-to-Low, or Rating.

### B. Customer Authentication
- Click the **Sign In** button in the header.
- Use demo credentials:
  - Email: `rahul.shopper@example.com`
  - Password: `Demo@123`
- *Alternatively, switch to the "Register" tab to create a new customer account.*

### C. Shopping Cart & Discount Coupons
1. Click **Add to Cart** on any product card. The slide-out cart drawer opens automatically.
2. Adjust item quantities using the `+` and `-` buttons. The free delivery meter recalculates dynamically.
3. Enter promotional coupon code `WELCOME10` or `SAVE20` in the coupon widget and click **Apply**.
4. The discount is deducted server-side from the subtotal.

### D. Transactional Checkout
1. Click **Proceed to Checkout**.
2. Verify customer details (Name, Address, City, Pincode pre-fill from profile).
3. Select payment method (`Cash on Delivery` or `Simulated Sandbox Card`).
4. Click **Place Order**.
5. The order confirmation modal displays your unique order reference (e.g., `ORD-2026-XXXX`).

### E. Customer Reviews & Support
- Open any product detail modal to view verified customer ratings and star distribution bars.
- Submit a review with headline, rating (1 to 5 stars), and feedback comments.

---

## 4. User Guide Sign-Off

Both user portals provide responsive, intuitive, and accessible workflows certified for enterprise operations.
