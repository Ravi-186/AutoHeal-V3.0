# AutoHeal v3.0 — Known Architectural Limitations & Boundaries
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Classification:** Transparent Architecture Disclosure  
**Date:** November 1, 2026  

---

## 1. Purpose of this Document

In adherence to the enterprise engineering principles of AutoHeal v3.0, this document provides an honest, transparent accounting of all known technical boundaries, design trade-offs, and scaling limits present in the current release.

---

## 2. Identified Technical Limitations & Mitigation Roadmaps

### Limitation 1: In-Memory Sliding-Window Rate Limiter
- **Description:** `AppSecProtectionMiddleware._rate_tracker` maintains client request timestamps in an in-memory dictionary.
- **Operational Impact:** On single-node servers (the certified deployment target), rate limiting functions reliably (15 requests in 8 seconds). However, in a multi-instance horizontally scaled cloud deployment behind a round-robin load balancer, each node maintains its own independent rate counter unless sticky sessions are configured.
- **Mitigation / Roadmap:** For multi-node Kubernetes clusters, replace the in-memory ring buffer with a centralized Redis backend using atomic Redis sliding-window scripts (`ZADD` / `ZREMRANGEBYSCORE`).

---

### Limitation 2: SQLite Relational Concurrency Ceiling
- **Description:** The system utilizes SQLite with Write-Ahead Logging (`shopsphere.db`).
- **Operational Impact:** Benchmarked at up to 800 writes per second and thousands of reads per second with sub-40ms latencies. However, SQLite permits only one writer transaction at any given microsecond. Highly distributed write loads (> 1,000 writes/sec across multiple distinct processes) may encounter `SQLITE_BUSY` contention.
- **Mitigation / Roadmap:** For multi-region enterprise deployments, migrate the SQLite data access layer to PostgreSQL 16+ with PgBouncer connection pooling.

---

### Limitation 3: AI Copilot Offline Fallback Mode
- **Description:** When an external LLM API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`) is not configured in `.env`, the Copilot defaults to the **Deterministic Grounded Analyst Engine**.
- **Operational Impact:** The offline mode is 100% grounded in SQLite telemetry, executes in sub-40ms, and cites concrete records. However, it cannot generate creative rephrasing or synthesize arbitrary open-ended questions unrelated to the database schema.
- **Mitigation:** Configure an enterprise Google Gemini API key to enable live LLM synthesis.

---

### Limitation 4: Simulated Payment Gateway in ShopSphere
- **Description:** ShopSphere e-commerce checkout offers "Cash on Delivery" and "Simulated Sandbox Card" options.
- **Operational Impact:** Real financial credit card processing is not hooked up to a live merchant bank (Stripe, Razorpay, or Adyen). Simulated payment transactions are explicitly tagged with `payment_status: "SIMULATED_SUCCESS"`.
- **Mitigation / Roadmap:** For live retail production, integrate the Stripe PaymentIntents API with webhooks.

---

### Limitation 5: 3D Threat Topology WebGL Hardware Requirement
- **Description:** The 3D Threat Topology canvas requires a graphics card and browser supporting WebGL 2.0.
- **Operational Impact:** Legacy headless browsers, text-mode browsers, or virtual machines without 3D GPU acceleration will not render the Three.js orbit graph.
- **Mitigation:** AutoHeal provides a built-in accessible **2D Table Fallback** view that renders all nodes, IPs, and blast radius scores in standard HTML.

---

## 3. Deployment Feasibility Matrix

| Environment | Supported? | Conditions & Recommendations |
|---|---|---|
| **Local Development** | **YES** | Native support on Windows, macOS, Linux |
| **Controlled Staging / UAT** | **YES** | Single-node VM, 4 vCPU, 8GB RAM, Uvicorn/Gunicorn |
| **Dedicated Single-Node Production** | **YES** | Certified ready behind Nginx reverse proxy with TLS |
| **Distributed Multi-Node Cloud Cluster** | **REQUIRES MIGRATION** | Requires Redis for rate limiting & PostgreSQL for database |

---

## 4. Limitations Sign-Off

All identified boundaries are well-understood, documented, and do not compromise the stability, security, or reliability of the certified single-node staging and production target.
