# AutoHeal v3.0 — AutoHeal & ShopSphere Integration Architecture
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Integration Lead:** Principal Full-Stack & DevSecOps Engineer  
**Date:** November 1, 2026  

---

## 1. Integration Paradigm

The relationship between **AutoHeal** and **ShopSphere** represents an enterprise-grade cybersecurity testing architecture:
- **ShopSphere** functions as a high-fidelity business target application (consumer e-commerce).
- **AutoHeal** acts as the autonomous cybersecurity monitoring, defense, and self-healing control plane.

```mermaid
graph TD
    subgraph TrafficFlow["Traffic Ingress & Filtering"]
        Request[Shopper / Attacker Traffic] --> WAF[AppSecProtectionMiddleware]
    end

    subgraph DefenseInterception["Perimeter Decision"]
        WAF -->|Benign Traffic (200 OK)| ShopCore[ShopSphere Business Logic]
        WAF -->|Malicious Payload (403 Blocked)| BlockResponse[Sentinel Block Response]
    end

    subgraph TelemetryBus["Asynchronous Observation Bus"]
        WAF -.->|Async Event Write| DB_Events[(security_events Table)]
        BlockResponse -.->|Correlated Incident| DB_Incidents[(security_incidents Table)]
    end

    subgraph SOCLoop["Autonomous Defense & Verification Loop"]
        DB_Incidents --> SOC[AutoHeal Incident Command Center]
        SOC --> SOAR[SOAR Playbook Execution]
        SOC --> SHE[Self-Healing Engine]
        SHE --> Verifier[Synthetic Dual-Probe Verifier]
        Verifier -->|Probe 1: Benign Shopper| ShopCore
        Verifier -->|Probe 2: Replay Exploit| WAF
    end
```

---

## 2. In-Process Observation & Protection Pipeline

### A. Non-Blocking Ingress Interception
Every HTTP request targeting ShopSphere (`/shop` or `/api/shop/*`) traverses `AppSecProtectionMiddleware`:
1. The request payload, query parameters, and headers are parsed and checked against regex detection rules.
2. If benign, the request proceeds immediately to ShopSphere domain services (`CatalogService`, `CartService`, `OrderService`).
3. If an attack signature matches (e.g. `INJ-001`), the middleware intercepts execution, generates an incident, records an audit event, and returns `HTTP 403 Forbidden` with the correlation ID. **The malicious payload never touches ShopSphere database or domain models.**

### B. Shared Relational Persistence
Both applications share the SQLite WAL database (`shopsphere.db`):
- ShopSphere reads and writes to business tables (`products`, `orders`, `users`, `cart_items`).
- AutoHeal reads and writes to cyber defense tables (`security_events`, `security_incidents`, `soar_playbooks`).
- Shared access operates without lock contention due to SQLite's Write-Ahead Logging mode.

---

## 3. The Synthetic Dual-Probe Verification Loop

To prevent false claims of remediation, AutoHeal implements an independent verification mechanism:
1. When a remediation action (e.g., IP quarantine or WAF hotpatch) is executed, AutoHeal does not assume success from API exit codes.
2. The `AppSecVerifier` (`src/appsec/verifier.py`) dispatches two independent synthetic HTTP probes against ShopSphere:
   - **Probe 1 (Benign Shopper Probe):** Makes a normal, valid request to `/api/shop/products` from a benign IP. **Expects HTTP 200 OK.**
   - **Probe 2 (Attacker Exploit Probe):** Replays the exact attack payload from the quarantined attacker IP. **Expects HTTP 403 Forbidden.**
3. **Dual Invariant Requirement:** The incident is marked `VERIFIED_CONTAINED` **only if both probes pass**. If Probe 1 fails (normal shopping broken), the system flags an over-blocking error and triggers automated rollback. If Probe 2 fails (attack still succeeds), containment is flagged as incomplete.

---

## 4. Educational Vulnerability Sandbox Integration

In addition to perimeter WAF defenses, ShopSphere includes an educational vulnerability sandbox (`autoheal_engine.py`):
- Supports controlled simulation of business logic defects (e.g. cart subtotal discount calculation bug).
- Features an automated 11-step verification cycle accessible via the floating AutoHeal dock on the storefront.
- Steps include: Seed State -> Inject Anomaly -> Detect Anomaly -> Triage -> Generate Patch -> Verify Patch -> Deploy -> Re-Verify -> Final Report.

---

## 5. Target Allowlisting & SSRF Prevention

To prevent accidental targeting of external networks:
- The configuration variable `ALLOWLISTED_TARGETS` strictly restricts attack simulations, SOAR actions, and synthetic verification probes to:
  ```text
  http://localhost:8000, http://127.0.0.1:8000
  ```
- Any attempt to target external URLs or IP addresses outside this allowlist is rejected immediately with `HTTP 400 Bad Request: Target address is not in authorized allowlist`.

---

## 6. Integration Architecture Sign-Off

The AutoHeal-ShopSphere integration provides a complete, robust, and safe environment for autonomous security validation.
