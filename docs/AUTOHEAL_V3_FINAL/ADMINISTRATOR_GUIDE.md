# AutoHeal v3.0 — Platform Administrator & Governance Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Audience:** Platform Administrators, DevSecOps Engineers, and Security Directors  
**Date:** November 1, 2026  

---

## 1. Administrative Overview

This guide outlines the governance controls, identity and access management (IAM), security policy configuration, inventory fulfillment, and compliance audit capabilities available to privileged administrators of AutoHeal v3.0.

---

## 2. Identity & Role-Based Access Control (RBAC)

AutoHeal implements three discrete security roles enforced at the API middleware level:

| Role Identifier | Description | Permitted Capabilities | Prohibited Capabilities |
|---|---|---|---|
| `ROLE_CUSTOMER` | Standard ShopSphere consumer | Browse catalog, add to cart, apply coupons, checkout, manage personal orders | Access `/dashboard`, view SOC telemetry, view admin APIs |
| `ROLE_ANALYST` | SOC Security Analyst | View Threat Center, inspect events, triage incidents, trigger SOAR dry-runs | Modify system WAF policies, replenish inventory, delete audit logs |
| `ROLE_ADMIN` | Enterprise Platform Admin | Full system access: manage users, approve high-impact SOAR gates, edit inventory, trigger hot backups | *Unrestricted* |

### Pre-Seeded Administrative Credentials
- **Email:** `admin@shopsphere.com`
- **Password:** `Admin@123`
- **Access Level:** `ROLE_ADMIN`

---

## 3. ShopSphere Store Administration

Administrators can manage store operations either via the ShopSphere Admin Modal (`/shop`) or via direct REST API endpoints:

### A. Inventory Management & Replenishment
- **View Inventory:** `GET /api/shop/admin/products`
- **Update Stock:** `PUT /api/shop/admin/products/{id}/stock` with payload `{"stock": 150}`.
- *Atomic Protection:* Stock updates use transactional locks to prevent race conditions during peak checkout traffic.

### B. Order Fulfillment Lifecycle
- **View Orders:** `GET /api/shop/admin/orders`
- **Update Status:** `POST /api/shop/admin/orders/{order_ref}/status` with valid target status:
  - `PLACED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` (or `CANCELLED`).
  - *Automated Stock Restoration:* Marking an order `CANCELLED` automatically restores product inventory in `products`.

### C. Promotional Coupon Governance
- **Create Coupon:** `POST /api/shop/admin/coupons` with payload:
  ```json
  {
    "code": "FESTIVE50",
    "discount_type": "PERCENTAGE",
    "discount_value": 50.0,
    "min_order_amount": 1000.0,
    "max_discount_amount": 500.0,
    "usage_limit": 500,
    "expires_at": "2026-12-31T23:59:59Z"
  }
  ```

---

## 4. AutoHeal Security Policy & Autonomous Governance

### A. Autonomous Self-Healing Policy Levels
Administrators can configure the system's operational autonomy via `PUT /api/self-healing/policies`:

| Autonomy Level | Name | Behavior |
|---|---|---|
| **Level 0** | *Manual Only* | Threat detection and diagnosis only; all remediation actions require manual analyst trigger. |
| **Level 1** | *Human-in-the-Loop* | System generates plans; actions require explicit operator approval via SOAR Approval Gates. |
| **Level 2** | *Bounded Autonomous* | Low-risk allowlisted actions (e.g. temporary IP rate limiting) execute autonomously; high-risk actions require approval. |

### B. IP Quarantine & Banishment Management
- **List Blocked IPs:** `SELECT * FROM blocked_clients;`
- **Manual Ban:** `INSERT INTO blocked_clients (client_ip, reason, blocked_until) VALUES ('198.51.100.42', 'Manual Admin Quarantine', '2026-11-02 12:00:00');`
- **Unblock IP:** `DELETE FROM blocked_clients WHERE client_ip = '198.51.100.42';`
- *Note: To clear active in-memory sliding window counters, restart the server or wait 8 seconds.*

---

## 5. Audit Trails & Compliance Verification

Every security-sensitive operation creates an immutable audit record:
- **SOC Activity Logs (`soc_activity_logs`):** Records analyst logins, incident status transitions, and note updates.
- **Self-Healing Audit Trail (`self_healing_audit_logs`):** Records hotpatch deployments, verification probe results, and snapshot rollbacks.
- **SOAR Execution Telemetry (`soar_execution_logs`):** Records node-by-node execution details, input/output JSON payloads, and approval signatures.

### Querying Audit Trail via Admin API
```bash
# Retrieve recent administrative actions
curl -s -H "Authorization: Bearer <ADMIN_TOKEN>" http://127.0.0.1:8000/api/security/audit-logs
```

---

## 6. System Health & Maintenance

Run detailed subsystem health inspection:
```bash
curl -s http://127.0.0.1:8000/api/security/health/detailed
```
Returns individual component status across API, Database, Ingestion, Queue, Detector, Verifier, and AI Provider.

---

## 7. Administrator Governance Sign-Off

The administrative control plane enforces strict role boundaries, comprehensive audit trails, and deterministic governance across both business and security operations.
