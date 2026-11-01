# AutoHeal v3.0 — Phase 0: Functionality & Interaction Audit
**Document ID:** AH-V3-P0-FNC-001  
**Project Baseline:** AutoHeal v2.5.0-PROD  
**Evaluation Scope:** All UI Controls, Form Submissions, Modals, Filters, and Backend Bindings  
**Status:** Certified Audit  

---

## 1. Executive Summary

This functionality audit assesses every interactive element across the AutoHeal SOC Sentinel Console and ShopSphere E-Commerce Storefront to verify genuine backend integration, identify any nonfunctional or disconnected controls, and ensure zero dependence on fabricated mock metrics.

---

## 2. Interactive Control & Element Audit Matrix

### 2.1 AutoHeal SOC Dashboard Controls (`index.html` & `script.js`)

| Control Name / Selector | Element Type | Intended Action | Verified Backend Binding | Functional Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sidebar Navigation Buttons** (`.nav-item-btn[data-page]`) | Button (11 items) | Switches active workspace view, updates breadcrumbs and tab state | Client-side DOM class toggling + page data fetch trigger | **OPERATIONAL** |
| **Sidebar Collapse Toggle** (`#sidebarToggleBtn`) | Button | Toggles sidebar between expanded (`250px`) and collapsed (`64px`) | CSS class `.collapsed` on `#appSidebar` & `.expanded` on `#contentArea` | **OPERATIONAL** |
| **Command Palette Search** (`.cmd-palette-trigger`) | Button / Shortcut | Opens centered search palette overlay (`Ctrl+K`) | Bound to keydown listener and modal backdrop toggle | **OPERATIONAL** |
| **Command Palette Search Input** (`#cmdPaletteInput`) | Text Input | Fuzzy-filters commands, workspaces, and actions | Filters list items dynamically; `Enter` executes top result | **OPERATIONAL** |
| **Refresh Telemetry Button** | Button | Manually triggers immediate metrics and posture update | Calls `loadDashboardMetrics()` (`/api/security/metrics`) & `loadSecurityPosture()` | **OPERATIONAL** |
| **Recalculate Posture Button** | Button | Forces recalculation of transparent defense score | `GET /api/security/posture` returning 5-pillar formula breakdown | **OPERATIONAL** |
| **Live Threat Multi-Filters** (`#eventsCategoryFilter`, `#eventsSeverityFilter`) | Select Dropdowns | Filters live telemetry table by event category and severity | Appends `&event_type=...&severity=...` to `GET /api/security/events` | **OPERATIONAL** |
| **Live Threat Text Search** (`#eventsSearchInput`) | Text Input | Instant client-side search across IP, path, method, and category | Filters in-memory `allFetchedEvents` array on `keyup` | **OPERATIONAL** |
| **Telemetry Table Row Click** (`#eventsTableBody tr`) | Table Row | Opens Side-Over Event Detail Drawer with raw JSON | Reads bound event object and populates `#eventDetailDrawerBody` | **OPERATIONAL** |
| **Copy Raw JSON Button** | Button | Copies event JSON to operating system clipboard | Uses `navigator.clipboard.writeText()` with Toastr feedback | **OPERATIONAL** |
| **Export CSV Button** | Button | Downloads filtered telemetry events as `.csv` file | Client-side CSV generator triggering standard browser download | **OPERATIONAL** |
| **Scenario Selector** (`#attackScenarioSelect`) | Select Dropdown | Selects 1 of 6 authorized adversarial test scenarios | Configures test parameters and target endpoints | **OPERATIONAL** |
| **Attack Intensity Slider** (`#attackIntensitySlider`) | Range Slider | Adjusts concurrent probes between 1 and 5 | Updates parameter payload sent to `/api/security/test/run` | **OPERATIONAL** |
| **Launch Attack Button** (`#btnLaunchAttack`) | Button | Dispatches test and initiates real-time SSE stream | `POST /api/security/test/run` & connects `EventSource` to `/api/security/attack-center/stream` | **OPERATIONAL** |
| **Abort Attack Button** (`#btnStopAttack`) | Button | Stops running scenario execution | `POST /api/security/test/stop` & closes active `EventSource` | **OPERATIONAL** |
| **Replay Attack Test Button** | Button | Replays payload against defense barrier to confirm containment | `POST /api/security/test/replay` verifying HTTP 403 response | **OPERATIONAL** |
| **Inspect Incident Button** | Button in Table | Expands Forensic Incident Dossier | `GET /api/security/incidents/{id}` with timeline and evidence | **OPERATIONAL** |
| **Purge All IP Bans Button** | Button | Removes all dynamic quarantines | `POST /api/security/unblock` in a loop or bulk purge | **OPERATIONAL** |
| **Inspect AST Diff Button** | Button | Opens Before vs After AST patch code diff view | `GET /api/security/vulnerabilities/{id}` displaying patch diff | **OPERATIONAL** |
| **Run Isolated Test Button** | Button | Runs regression test against patched function | `POST /api/security/vulnerabilities/{id}/test` returning PASSED/FAILED | **OPERATIONAL** |
| **Approve Patch Button** | Button | Submits operator approval gate | `POST /api/security/vulnerabilities/{id}/approve` | **OPERATIONAL** |
| **Apply Patch Button** | Button | Applies AST patch live to file | `POST /api/security/vulnerabilities/{id}/apply` | **OPERATIONAL** |
| **Rollback Patch Button** | Button | Reverts AST patch from snapshot | `POST /api/security/vulnerabilities/{id}/rollback` | **OPERATIONAL** |
| **IOC Query Button** | Button | Queries IP/domain against threat intelligence cache | Queries `/api/security/blocked-clients` & `allFetchedEvents` | **OPERATIONAL** |
| **Switch to 2D Table Button** (`#topologyToggleViewBtn`) | Button | Toggles between 3D WebGL viewport and accessible 2D table | Switches display between `#topologyViewport` and `#topologyTableView` | **OPERATIONAL** |

### 2.2 ShopSphere E-Commerce Controls (`shopsphere.html`)

| Control Name / Selector | Element Type | Intended Action | Backend Binding | Functional Status |
| :--- | :--- | :--- | :--- | :--- |
| **Category Filter Pills** (`.cat-item`) | Filter Chips | Filters product catalog by category (Electronics, Fashion, etc.) | Triggers `filterCategory()` & re-renders product grid | **OPERATIONAL** |
| **Price Range Slider** (`#priceRangeInput`) | Range Slider | Filters catalog by maximum price in INR | Triggers `updatePriceSlider()` & `applyFilters()` | **OPERATIONAL** |
| **Catalog Search Bar** (`#searchInput`) | Text Input | Filters catalog by product title or description keyword | `handleSearchKey()` / `executeSearch()` | **OPERATIONAL** |
| **Add to Cart Button** (`.btn-add-cart`) | Button | Adds product to shopping cart session | Updates cart in-memory & updates floating cart badge | **OPERATIONAL** |
| **Cart Quantity Incrementor/Decrementor** | Buttons | Adjusts quantity of item in cart | `updateCartQty(productId, qty)` | **OPERATIONAL** |
| **Remove Cart Item** | Button | Removes item from cart drawer | `removeCartItem(productId)` | **OPERATIONAL** |
| **Proceed to Checkout Button** | Button | Opens multi-step checkout modal | `openCheckoutModal()` | **OPERATIONAL** |
| **Checkout Submit Button** | Button | Submits order, validates address, reduces stock | `POST /api/shop/orders` persisting to SQLite database | **OPERATIONAL** |
| **Cancel Order Button** | Button | Cancels order & restores stock in SQLite | `POST /api/shop/orders/{id}/cancel` | **OPERATIONAL** |
| **Update Stock Level (Admin)** | Form Button | Replenishes product stock level | `POST /api/shop/admin/stock` (Admin RBAC required) | **OPERATIONAL** |

---

## 3. Disconnected or Legacy Controls Identified & Rectified

During this audit, the following legacy elements were identified and brought into compliance:
1. *Legacy Top Navigation Buttons (`.nav-tab-item`):* Previous navigation references in `script.js` targeted `.nav-tab-item`. The controller was updated to select `.nav-item-btn[data-page], .nav-tab-item[data-page]` seamlessly, ensuring backward compatibility with any external link references.
2. *Event Table Body ID Divergence:* Legacy HTML referenced `#securityEventsTableBody` while new layouts referenced `#eventsTableBody`. The controller was updated to bind dynamically: `document.getElementById('eventsTableBody') || document.getElementById('securityEventsTableBody')`.
3. *Vulnerability Drawer ID Divergence:* The code diff drawer referenced `#vulnPatchDrawer` vs `#vulnDrawerPanel`. The controller now binds to either container seamlessly.

---

## 4. Verification of Real Data Integrity

- **No Hardcoded Arrays:** Metrics displayed on KPI cards bind strictly to dynamic integers returned by `GET /api/security/metrics`.
- **Real-Time Telemetry:** The live telemetry table renders real HTTP events logged to SQLite by `AppSecProtectionMiddleware`.
- **Verified AST Patches:** The patch diffs displayed in the Self-Healing Center represent actual Python AST transformations executed by `ast.NodeTransformer` on target services.
