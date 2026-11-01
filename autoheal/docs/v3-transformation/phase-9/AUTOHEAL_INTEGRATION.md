# AutoHeal SOC Integration Architecture
## Phase 9: Real-Time Security Telemetry, Incident Correlation & Autonomous Self-Healing

### 1. Dual Mission of ShopSphere
ShopSphere fulfills a dual mission within the AutoHeal platform:
1. **Commercial Storefront**: Serves as a consumer e-commerce marketplace featuring product discovery, verified ratings, coupons, and transactional multi-step checkout.
2. **Security Target Node**: Serves as the real target application for AutoHeal's authorized attack simulations, detection validation, incident correlation, SOAR playbook automation, and autonomous self-healing.

---

### 2. Live Telemetry Pipeline

```
  Inbound HTTP Request to ShopSphere (/shop, /api/shop/*)
                           │
                           ▼
             [AppSecProtectionMiddleware]
                           │
              Inspects URI, Headers, Payload
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
 [Clean Benign Traffic]             [Adversarial Threat]
         │                          (SQLi, XSS, Bursts)
         │                                   │
         ▼                                   ▼
 [Executes Store Service]            [Rule Triggered]
         │                           - Log security_events
         │                           - Quarantine IP (blocked_clients)
         │                           - Create security_incidents
         ▼                                   │
 [Returns 200 OK Response]                   ▼
                                     [SSE Streamer to AutoHeal SOC]
```

---

### 3. Attack Simulation Compatibility
Existing authorized test scenarios from the Attack Simulation Center continue to execute against ShopSphere without friction:
- **`SQLI-001` Probe**: Sends injection patterns to `/api/shop/products` and `/api/shop/cart/add`. Intercepted by AppSec middleware, returning HTTP 403 and streaming live security events.
- **`RATE-001` Burst**: Sends rapid request bursts. Sliding-window tracker triggers HTTP 429 Too Many Requests.
- **`AUTH-001` Brute Force**: Fires failed login sequences to `/api/shop/auth/login`. Telemetry streams to the Threat Topology graph and SOC Copilot.

---

### 4. Interactive AutoHeal Demonstration Console
Embedded directly into the storefront is the **Floating AutoHeal Demonstration Console**:
- **Baseline Test**: Executes unit invariants to confirm clean financial math.
- **Inject Bug**: Sets `SIMULATE_CART_BUG = True` in memory, corrupting delivery fee logic.
- **Run Regression**: Executes regression tests, detecting the financial invariant defect.
- **AI Diagnosis**: Performs AST and stack trace analysis, determining root-cause.
- **Apply Surgical Fix**: Deploys the patch, restoring invariants in under 10ms.
- **Run Full 11-Step Demo**: Executes the complete autonomous lifecycle end-to-end with visual step progression in the storefront dock.
