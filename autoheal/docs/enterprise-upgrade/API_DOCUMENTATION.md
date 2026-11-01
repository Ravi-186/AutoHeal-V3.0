# AutoHeal & ShopSphere: Enterprise API Documentation

**Author:** Principal Software Architect & API Engineering Group  
**Document Ref:** `API-DOC-001`  
**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/api/docs` (Swagger UI), `/api/redoc` (ReDoc)  
**Date:** 2026-11-01  

---

## 1. Application Security Sentinel API (`/api/security/*`)

### 1.1 `GET /api/security/metrics`
- **Summary:** Retrieve Live Application Security KPIs
- **Response Model:**
  ```json
  {
    "status": "OPERATIONAL",
    "total_events_recorded": 5872,
    "total_incidents": 292,
    "active_blocked_ips": 1,
    "incidents_by_severity": { "CRITICAL": 52, "HIGH": 80, "MEDIUM": 140, "LOW": 20 },
    "active_threats": 0,
    "average_remediation_ms": 145.96
  }
  ```
- **Integrity Rule:** `average_remediation_ms` is computed dynamically from persisted verification probe and mitigation execution records.

### 1.2 `GET /api/security/events`
- **Summary:** List Telemetry Security Events
- **Query Parameters:** `event_type`, `severity`, `client_ip`, `limit` (max 200)

### 1.3 `GET /api/security/incidents`
- **Summary:** List Security Incidents with Evidence Dossiers
- **Query Parameters:** `status`, `severity`, `limit` (max 200)

### 1.4 `GET /api/security/incidents/{incident_id}/export`
- **Summary:** Export Incident Forensic Dossier
- **Query Parameter:** `format` (`json`, `md`, `markdown`, `pdf`)

### 1.5 `POST /api/security/test/run`
- **Summary:** Execute Live Controlled Security Test
- **Payload:** `{"scenario": "sqli|xss|failed_logins|admin|rate|health", "target_url": "http://localhost:8000", "client_ip": "..."}`

### 1.6 `POST /api/security/test/replay`
- **Summary:** Replay Attack Scenario with Before/After Quarantine State Comparison
- **Payload:** `{"scenario": "sqli", "target_url": "http://localhost:8000", "client_ip": "203.0.113.111"}`
- **Response:** Contains `before_state`, `after_state`, `protection_verified`, and `incident_id`.

### 1.7 `POST /api/security/unblock`
- **Summary:** Unblock Quarantined Client IP
- **Payload:** `{"client_ip": "198.51.100.22"}`

---

## 2. ShopSphere E-Commerce API (`/api/shop/*`)

### 2.1 `GET /api/shop/products`
- **Summary:** Product Catalog Search & Category Filter
- **Security Interception:** Inspected by INJ-001 (SQLi) and XSS-001 filters before query execution.

### 2.2 `POST /api/shop/cart/add`
- **Summary:** Add Product to Cart with Stock Limits
- **Payload:** `{"user_or_session_id": "...", "product_id": 1, "quantity": 2}`

### 2.3 `POST /api/shop/checkout`
- **Summary:** Atomic Transactional Checkout
- **Payload:** `{"user_or_session_id": "...", "customer_name": "...", "customer_email": "...", "shipping_address": "...", "city": "...", "pincode": "..."}`
- **Response:** Contains full `order` object with order reference and item breakdown.

### 2.4 `GET /api/shop/admin/stats`
- **Summary:** Protected Admin Analytics
- **Security Requirement:** Requires `Authorization: Bearer <valid_admin_token>`. Returns HTTP 401 on missing/invalid token and HTTP 403 on non-admin user role.
