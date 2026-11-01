# AutoHeal v3.0 — Complete REST API Specification
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**API Protocols:** REST (JSON) / Server-Sent Events (SSE) / WebSockets  
**Total Registered Endpoints:** 168 Endpoints  
**Date:** November 1, 2026  

---

## 1. API Architecture & Standards

All AutoHeal and ShopSphere APIs follow strict RESTful conventions:
- **Base URL:** `http://localhost:8000`
- **Data Format:** `application/json` (UTF-8 encoded)
- **Error Envelopes:** Standard JSON envelopes with correlation tracking (`{"error": "...", "detail": "...", "correlation_id": "corr-..."}`).
- **Authentication Scheme:** `Authorization: Bearer <TOKEN>` or session header `X-Session-ID: <SID>`.
- **Interactive OpenAPI Specification:** `http://localhost:8000/docs`

---

## 2. API Endpoint Catalog by Subsystem

### 2.1 Core Diagnostics & Platform Health (4 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/` | None | Service index & redirect | `200` |
| `GET` | `/api/health` | None | Core liveness probe (Uptime, ML status) | `200` |
| `GET` | `/api/system/status` | None | Comprehensive system state & metrics | `200` |
| `GET` | `/api/version` | None | Build version (`3.0.0-enterprise`) | `200` |

---

### 2.2 Live Threat Center & Security Event Explorer (32 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/security/events` | None | Paginated security event query with filters | `200` |
| `GET` | `/api/security/events/{id}` | None | Detailed event record with raw telemetry | `200`, `404` |
| `GET` | `/api/security/events/stream` | None | Real-time SSE event stream (text/event-stream)| `200` |
| `GET` | `/api/security/events/{id}/related`| None | 3-tier event correlation query | `200`, `404` |
| `GET` | `/api/security/rules/catalog` | None | 7 detection rules with live counters | `200` |
| `GET` | `/api/security/threat-intel/enrich`| None | IP threat score & reputation lookup | `200` |
| `GET` | `/api/security/events/export` | None | CSV/JSON data streaming export | `200` |
| `POST`| `/api/security/events/{id}/investigate`| Analyst| Update analyst investigation status | `200`, `400` |
| `POST`| `/api/security/events/{id}/escalate`| Analyst | Manually escalate event to incident | `200`, `409` |

---

### 2.3 Incident Command Center (18 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/security/incidents` | None | List incidents with status & priority filters | `200` |
| `GET` | `/api/security/incidents/{id}` | None | Forensic incident dossier | `200`, `404` |
| `GET` | `/api/security/incidents/{id}/timeline`| None | Chronological attack sequence | `200` |
| `GET` | `/api/security/incidents/{id}/evidence`| None | Raw evidence payload & query parameters | `200` |
| `POST`| `/api/security/incidents/{id}/status` | Analyst | Transition lifecycle state (optimistic lock)| `200`, `400`, `409` |
| `POST`| `/api/security/incidents/{id}/assign` | Analyst | Assign incident to security operator | `200`, `400` |
| `POST`| `/api/security/incidents/{id}/verify` | None | Run synthetic dual-probe verification | `200`, `404` |
| `GET` | `/api/security/incidents/{id}/report` | None | Download formatted Markdown report | `200`, `404` |

---

### 2.4 Visual SOAR Automation Builder (21 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/soar/playbooks` | None | List all defined playbooks | `200` |
| `POST`| `/api/soar/playbooks` | Admin | Create a new playbook | `201`, `400` |
| `GET` | `/api/soar/playbooks/{id}` | None | Retrieve playbook DAG structure & nodes | `200`, `404` |
| `POST`| `/api/soar/playbooks/{id}/execute` | Analyst | Execute playbook in LIVE mode | `200`, `400` |
| `POST`| `/api/soar/playbooks/{id}/dry-run` | Analyst | Execute dry-run without state mutation | `200`, `400` |
| `GET` | `/api/soar/executions/{id}` | None | Retrieve execution log & node results | `200`, `404` |
| `GET` | `/api/soar/approvals/pending` | Admin | List executions suspended at Approval Gates| `200` |
| `POST`| `/api/soar/approvals/{id}/decide`| Admin | Approve or reject gate and resume DAG | `200`, `400` |
| `GET` | `/api/soar/node-types` | None | Extensible catalog of supported SOAR nodes| `200` |

---

### 2.5 Self-Healing & Remediation Center (16 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/self-healing/overview` | None | Self-healing KPI metrics & recovery rates | `200` |
| `GET` | `/api/self-healing/protection-status`| None | Health matrix across all monitored layers | `200` |
| `GET` | `/api/self-healing/diagnose/{id}`| None | Execute RCA and extract attack root cause | `200`, `404` |
| `POST`| `/api/self-healing/plans/generate`| None | Generate structured remediation options | `200`, `400` |
| `POST`| `/api/self-healing/execute` | Admin | Deploy remediation hotpatch | `200`, `400` |
| `POST`| `/api/self-healing/verify` | None | Trigger dual-probe synthetic verification | `200`, `400` |
| `POST`| `/api/self-healing/rollback` | Admin | Instant (< 50ms) snapshot rollback | `200`, `400` |
| `POST`| `/api/self-healing/emergency-stop`| Admin| Global circuit breaker halting healing | `200` |

---

### 2.6 AI SOC Copilot (7 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `POST`| `/api/copilot/chat` | None | Multi-turn conversational security assistant | `200`, `400` |
| `GET` | `/api/copilot/suggested-prompts` | None | Context-aware starter prompts | `200` |
| `GET` | `/api/copilot/provider-status` | None | LLM provider connectivity & mode status | `200` |
| `POST`| `/api/copilot/investigate/{id}` | None | Generate deep-dive forensic synthesis | `200`, `404` |
| `POST`| `/api/copilot/reports/generate` | None | Generate 12-section formal defense report | `200`, `400` |

---

### 2.7 3D Threat Topology (4 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/threat-topology/graph` | None | Full 3D node and edge spatial graph | `200` |
| `GET` | `/api/threat-topology/summary` | None | Blast radius and node risk summaries | `200` |
| `GET` | `/api/threat-topology/entity/{id}`| None | Detailed metadata for selected node | `200`, `404` |
| `GET` | `/api/threat-topology/attack-sequence/{id}`| None | Chronological attack hop sequence | `200` |

---

### 2.8 ShopSphere E-Commerce Application (39 Endpoints)
| Method | Endpoint | Auth | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/api/shop/products` | None | Query product catalog (search, filter, sort) | `200` |
| `GET` | `/api/shop/products/{id}` | None | Product detail with gallery and JSON specs | `200`, `404` |
| `GET` | `/api/shop/cart` | None | Retrieve cart totals calculated server-side | `200` |
| `POST`| `/api/shop/cart/add` | None | Add item to shopping cart | `200`, `400` |
| `POST`| `/api/shop/cart/apply-coupon` | None | Apply promo coupon (`WELCOME10`, `SAVE20`) | `200`, `400` |
| `POST`| `/api/shop/checkout` | None | Complete atomic order checkout | `200`, `400` |
| `POST`| `/api/shop/auth/login` | None | Customer login with JWT issuance | `200`, `401` |
| `POST`| `/api/shop/auth/register` | None | New customer account registration | `201`, `400` |
| `GET` | `/api/shop/products/{id}/reviews`| None | Verified customer reviews and ratings | `200` |
| `POST`| `/api/shop/products/{id}/reviews`| Customer | Submit a product review | `201`, `400` |
| `PUT` | `/api/shop/admin/products/{id}/stock`| Admin | Update inventory stock level | `200`, `400` |

---

## 3. Standard Request & Response Envelopes

### Sample WAF Block Envelope (HTTP 403 Forbidden)
```json
{
  "error": "Request Blocked by AutoHeal Application Security Sentinel",
  "threat_category": "Injection",
  "rule_id": "INJ-001",
  "summary": "SQL injection attempt detected on GET /api/shop/products",
  "incident_id": "INC-2026-D6DC8C55",
  "mitigation_action": "BLOCK_IP",
  "confidence": 0.98,
  "correlation_id": "corr-845549a4"
}
```

### Sample Cart Calculation Response (HTTP 200 OK)
```json
{
  "status": "success",
  "cart": {
    "items": [...],
    "total_items": 1,
    "subtotal": 21990.0,
    "discount": 2910.0,
    "coupon_code": "WELCOME10",
    "delivery_fee": 0.0,
    "final_total": 19080.0,
    "free_delivery_qualified": true
  }
}
```

---

## 4. API Specification Sign-Off

All 168 registered endpoints have been audited, reachability-verified, and documented in adherence to OpenAPI 3.1 standards.
