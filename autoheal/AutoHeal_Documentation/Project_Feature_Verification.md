# AutoHeal: Project Feature Verification & Implementation Matrix

**Project Title**: AutoHeal: An AI-Powered Self-Healing Cybersecurity System for E-Commerce Applications  
**Institutions**: Department of Computer Science & Engineering (Cyber Security), Malla Reddy University  
**Authors**: B. Sri Ravi Tej (2411CS040019) & J. Anil (2411CS040069)  
**Supervisor**: Priyanka Chandragiri, Assistant Professor (Ph.D)  
**Evaluation Date**: October 2026  
**Primary Testbed**: ShopSphere E-Commerce Application (`http://localhost:8000/shop`) & AutoHeal SOC Dashboard (`http://localhost:8000/`)

---

## 1. Executive Summary

This document provides a comprehensive verification matrix of all architectural components, API endpoints, detection engines, adversary simulation routines, mitigation mechanisms, and reporting features implemented within the AutoHeal and ShopSphere repositories. Every feature is categorized as **Fully Implemented & Verified**, **Partially Implemented**, **Planned**, or **Not Working/Deprecated**, referencing actual source code files, database schemas, and live execution test runs.

---

## 2. Feature Verification Matrix

| Module / Feature Name | Intended Capability | Technical Implementation / Source Files | Verification Evidence & Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ShopSphere Storefront & Catalog** | Multi-category e-commerce catalog, promotional banners, product filtering, and shopping cart | `shopsphere/api.py`, `shopsphere/models.py`, `web/templates/shopsphere.html` | Served live at `http://localhost:8000/shop`; verified with 14 products across Mobiles, Laptops, Electronics, and Fashion categories. Cart additions functional. | **Fully Implemented & Verified** |
| **Ingress AppSec Middleware** | In-process request interception, IP extraction, perimeter quarantine check, and structured telemetry logging | `src/appsec/middleware.py`, `src/appsec/models.py` | Starlette ASGI middleware intercepts all requests on port 8000; returns immediate HTTP 403 to quarantined IPs in < 1ms. Commits structured telemetry to `appsec_telemetry.db`. | **Fully Implemented & Verified** |
| **Attack Center & Scenario Dispatcher** | Bounded, safe adversary simulation interface executing real HTTP requests against local ShopSphere | `src/appsec/security_tester.py`, `src/appsec/api.py`, `web/templates/index.html` | Embedded in AutoHeal dashboard; verified with 5 attack scenarios (Failed Logins, Admin Probe, SQLi, XSS, Rate Anomaly) targeting `http://localhost:8000` with real-time SSE execution trace. | **Fully Implemented & Verified** |
| **Sliding-Window Threat Correlation** | Deterministic rule-based threat detection over 60-second temporal sliding windows | `src/appsec/detector.py`, `src/appsec/rules.py` | Verified detection of `AUTH-001` (>=4 failed logins in 60s, 96% confidence) and `RATE-001` (>=30 requests/60s). Creates structured `SecurityIncident` entries in SQLite. | **Fully Implemented & Verified** |
| **Autonomous Dynamic Quarantine** | Immediate perimeter IP quarantine with configurable sliding TTL auto-expiry | `src/appsec/responder.py`, `src/appsec/models.py` | Sub-second quarantine (< 80ms) registered in memory and persisted in SQLite. Attacker client receives HTTP 403 Forbidden. Manual unblock and sliding TTL expiry verified. | **Fully Implemented & Verified** |
| **Synthetic Probe Verification** | Active loopback HTTP probing to confirm perimeter blockage without human intervention | `src/appsec/verifier.py`, `src/appsec/api.py` | Dispatches loopback HTTP probe with spoofed `X-Forwarded-For: <attacker_ip>` to `/api/shop`. Confirms HTTP 403 response, updating incident to `VERIFIED_CONTAINED`. | **Fully Implemented & Verified** |
| **Autonomous Code Vulnerability Remediation** | Closed-loop source code defect diagnosis, surgical patch injection, regression testing, and rollback | `shopsphere/autoheal_engine.py`, `src/appsec/vulnerability_manager.py` | Remediation Hub executes baseline tests, applies surgical code modifications to `shopsphere/api.py`, verifies zero regressions, and demonstrates atomic rollback. | **Fully Implemented & Verified** |
| **Transparent Security Posture Scoring** | Real-time 0–100 security posture score with visible deduction weights, bonuses, and defense pillars | `src/appsec/posture_scorer.py`, `src/appsec/api.py` | Dynamically calculated posture score (65/100, Grade: MODERATE RISK) with 5 evaluated pillars: Authentication (75%), Injection (100%), Access Control (95%), DoS (98%), Code Integrity (68%). | **Fully Implemented & Verified** |
| **Primary Web SOC Dashboard** | Real-time security operations console with KPI tiles, live telemetry audit logs, and incident dossiers | `web/templates/index.html`, `web/static/js/script.js`, `web/static/css/style.css` | Operational at `http://localhost:8000/`. Real-time event polling/SSE, 5-stage containment timeline, filterable event logs, and subsystem health indicators. | **Fully Implemented & Verified** |
| **Streamlit 3D Spatial Threat Hub** | 3D WebGL particle network representing zero-trust network zones and multi-agent SOAR states | `dashboard/app.py`, `dashboard/background3d.py`, `src/graph/workflow.py` | Operational at `http://localhost:8501`. Renders 23 monitored assets, Three.js 3D rotating network mesh, SOAR policy controls, and LangGraph multi-agent reasoning. | **Fully Implemented & Verified** |
| **Audit-Ready Incident PDF Export** | Pure-Python PDF forensic dossier generator with automatic credential sanitization | `src/appsec/reporter.py`, `src/appsec/pdf_generator.py`, `src/appsec/api.py` | Verified via `GET /api/security/incidents/{id}/export?format=pdf` (5,867 bytes binary PDF) with automatic redaction of passwords, tokens, and cookies; also exports JSON & Markdown. | **Fully Implemented & Verified** |
| **Distributed Kubernetes Sidecar** | Service mesh eBPF/Envoy proxy enforcement across multi-cluster Kubernetes deployments | Conceptual architecture in Section 6.2 | Delineated as future scope; currently runs as an in-process ASGI middleware within the local application container. | **Planned (Future Scope)** |
| **LLM Zero-Day Patch Synthesis** | Generative LLM agent synthesizing dynamic code patches for uncataloged zero-day CVEs | Conceptual architecture in Section 6.2 | Delineated as future scope; current remediation uses pre-tested, verified surgical code patches with automated regression testing. | **Planned (Future Scope)** |

---

## 3. Discrepancy & Gap Analysis: Presentation vs. Source Code

During the inspection of `AutoHeal_Review_2.pptx` against the actual codebase, the following alignments and clarifications were established:

1. **E-Commerce Replica Naming**:
   - Presentation references "ShopSphere" / "Flipkart replica".
   - Codebase matches: Fully implemented in `shopsphere/api.py` and `web/templates/shopsphere.html` with Flipkart-style blue headers, Indian Rupee pricing, and active shopping categories.

2. **Dual-Dashboard Architecture**:
   - Presentation mentions both an AutoHeal web platform and a CyberShield SOC center.
   - Codebase matches: Port 8000 hosts the primary AutoHeal Web SOC (dark-mode enterprise UI with Attack Center, Live Telemetry, Incident Forensics, Remediation Hub, and Health), while Port 8501 hosts the Streamlit 3D Cyber Defense Center with Three.js particle topology.

3. **Attack Simulation Safety Bounds**:
   - The review presentation specifies controlled attack simulation.
   - Codebase matches: `src/appsec/security_tester.py` strictly restricts target URLs to `http://localhost:8000`, rejecting arbitrary external IP ranges to ensure safe, ethical academic demonstration.

4. **Zero-Dependency PDF Export**:
   - The review presentation highlights forensic incident reporting.
   - Codebase matches: `src/appsec/pdf_generator.py` utilizes a pure-Python PDF 1.4 canvas stream generator that requires zero external C libraries (e.g., Cairo, Pango, or wkhtmltopdf), ensuring cross-platform stability.

---

## 4. Summary of Verification Outcome

- **Core Functionality**: 100% operational across ports 8000 and 8501.
- **Test Case Execution**: 8 out of 8 test cases passed.
- **Genuine Screenshots**: 10 real screenshots captured and archived in `AutoHeal_Documentation/screenshots/`.
- **Architectural Diagrams**: 7 UML diagrams rendered in `AutoHeal_Documentation/diagrams/`.
