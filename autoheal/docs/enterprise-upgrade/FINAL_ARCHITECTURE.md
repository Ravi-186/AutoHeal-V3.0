# AutoHeal & ShopSphere: Final Enterprise Architecture Specification

**Author:** Principal Software Architect & Cybersecurity Architecture Lead  
**Document Classification:** Enterprise Architecture Standard  
**Revision:** 2.5.0-PROD  
**Date:** 2026-11-01  

---

## 1. Architectural Vision & Topology

AutoHeal is an autonomous enterprise Security Operations Center (SOC) and Security Orchestration, Automation, and Response (SOAR) platform paired with ShopSphere, a Flipkart-inspired full-stack e-commerce application serving as the controlled, authorized target environment.

```
+---------------------------------------------------------------------------------------------------+
|                                  OPERATOR & ANALYST INTERFACES                                    |
|                                                                                                   |
|  +--------------------------------------------+  +---------------------------------------------+  |
|  |       AutoHeal SOC 3D WebGL Dashboard      |  |         ShopSphere Storefront Portal        |  |
|  |     (Streamlit on port 8501 / Glassmorphism)|  |         (HTML5 / TailwindCSS / REST UI)     |  |
|  +--------------------------------------------+  +---------------------------------------------+  |
+----------------------------------------|---------------------------------|------------------------+
                                         | REST / SSE                      | REST / JSON
                                         v                                 v
+---------------------------------------------------------------------------------------------------+
|                                  APPLICATION GATEWAY & PERIMETER WAF                              |
|                                                                                                   |
|  [AutoHeal Application Security Sentinel (src/appsec/detector.py / WAF Interceptor)]              |
|   - Real-time URI Query & Body Decoding (urllib unquote + regex)                                  |
|   - SQL Injection Filter (Tautology, Stacked, UNION SELECT - Rule INJ-001)                        |
|   - Cross-Site Scripting Filter (Executable tags, event handlers - Rule XSS-001)                   |
|   - Dynamic IP Blocklist Quarantine Check (blocked_clients table in SQLite)                        |
|   - Sliding-Window Rate Limiting (Token Bucket / Sliding Counter - Rule RATE-001)                  |
+----------------------------------------|----------------------------------------------------------+
                                         | Ingest / Telemetry
                                         v
+---------------------------------------------------------------------------------------------------+
|                                     AUTOHEAL CORE SOC BACKEND                                     |
|                                                                                                   |
|  +-------------------------------------+   +---------------------------------------------------+  |
|  | 1. SIEM Event Ingestion Pipeline    |   | 2. Multi-Vector Threat Correlation Engine         |  |
|  |    - Normalized JSON Telemetry      |   |    - Sliding-Window Telemetry Correlation (60s)    |  |
|  |    - SHA-256 Event & Correlation IDs|   |    - MITRE ATT&CK Enterprise Matrix Alignment     |  |
|  +-------------------------------------+   +---------------------------------------------------+  |
|                                  |                                   |                            |
|                                  v                                   v                            |
|  +-------------------------------------+   +---------------------------------------------------+  |
|  | 3. Autonomous LangGraph Swarm       |   | 4. SOAR Response Orchestrator & Remediation       |  |
|  |    - Detect -> Respond -> Verify    |   |    - Dynamic IP Perimeter Containment (403 drop)  |  |
|  |    - Bounded Retries (Max 3)        |   |    - Service Recovery & Invariant Healing         |  |
|  +-------------------------------------+   +---------------------------------------------------+  |
|                                  |                                   |                            |
|                                  v                                   v                            |
|  +-------------------------------------+   +---------------------------------------------------+  |
|  | 5. Closed-Loop Synthetic Verifier   |   | 6. AI Security Advisor & Forensic Reporting       |  |
|  |    - Perimeter 403 Quarantine Probe |   |    - Offline Deterministic Heuristics             |  |
|  |    - Availability 200 Shopper Probe |   |    - Markdown, PDF & JSON Dossier Exports         |  |
|  +-------------------------------------+   +---------------------------------------------------+  |
+----------------------------------------|----------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------------------------+
|                               PERSISTENCE & TELEMETRY STORAGE LAYER                               |
|                                                                                                   |
|  SQLite 3 Database (data/shopsphere.db) in Write-Ahead-Logging (WAL) Mode                         |
|   - 12 Tables with Strict Foreign Keys (`PRAGMA foreign_keys = ON`)                               |
|   - 7 Composite Enterprise Performance Indexes                                                    |
|   - Cryptographically Hashed RBAC (`PBKDF2-HMAC-SHA256` + 100,000 iterations)                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Component Decoupling & Interface Contracts

1. **Presentation Boundary:**
   - Frontend interfaces consume typed REST APIs with standardized JSON response envelopes.
   - All asynchronous state changes stream via Server-Sent Events (SSE) or REST polling with client-side reconciliation.
2. **Security Interception Boundary:**
   - In-flight HTTP requests pass through the Sentinel interceptor before touching e-commerce business services.
   - Malicious requests are rejected immediately with HTTP 403 Forbidden without database query execution.
3. **SOAR & Self-Healing Boundary:**
   - Response actions are policy-driven, idempotent, and bounded.
   - Remediation state is only set to `VERIFIED_CONTAINED` upon successful execution of synthetic loopback verification probes.
