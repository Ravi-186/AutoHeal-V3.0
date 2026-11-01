# Phase 10 — Enterprise Release Manifest
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center  
**Target Application:** ShopSphere E-Commerce Security Testing Target  
**Release Tag:** `v3.0.0-enterprise`  
**Git Branch:** `v3-transformation`  
**Commit Baseline:** `897880b`  
**Release Lead:** Principal Enterprise Release Manager  
**Release Date:** November 1, 2026  
**Status:** SEALED — CERTIFIED RELEASE MANIFEST  

---

## 1. Release Identification

| Attribute | Manifest Value |
|---|---|
| **Product Name** | AutoHeal Autonomous SOC & ShopSphere E-Commerce |
| **Release Version** | `3.0.0-enterprise` |
| **Release Codename** | *Obsidian Sentinel* |
| **Git Repository** | `AD` |
| **Git Branch** | `v3-transformation` |
| **Release Status** | Certified Staging Ready / Single-Node Production Ready |
| **Python Runtime** | Python 3.13.7 (Standard 64-bit AMD64) |
| **ASGI Engine** | Uvicorn 0.34.0+ / Starlette 0.45.3+ / FastAPI 0.115.8+ |

---

## 2. Source Code & Component Inventory

```
autoheal/
├── server.py                        # Core ASGI application router & shell
├── requirements.txt                 # Pinned enterprise dependencies
├── .env.example                     # Reference environment configuration
├── data/
│   ├── shopsphere.db                # SQLite 3 WAL database (30 tables)
│   ├── firewall_logs.csv            # Telemetry feed
│   ├── device_logs.csv              # Telemetry feed
│   ├── dns_logs.csv                 # Telemetry feed
│   └── login_logs.csv               # Telemetry feed
├── models/
│   ├── isolation_forest.joblib      # Pre-trained ML anomaly detector
│   └── threat_features.joblib       # Feature engineering transformer
├── shopsphere/
│   ├── __init__.py
│   ├── api.py                       # 39 ShopSphere REST endpoints
│   ├── database.py                  # Schema definitions & connection pool
│   ├── services.py                  # Domain logic (Catalog, Orders, Auth)
│   └── autoheal_engine.py           # Sandbox vulnerability simulator
├── src/
│   ├── appsec/
│   │   ├── api.py                   # Threat Center & Incident Command
│   │   ├── copilot_api.py           # AI Security Copilot
│   │   ├── executive_api.py         # Executive Defense Deck & KPIs
│   │   ├── middleware.py            # WAF & sliding window rate limiting
│   │   ├── models.py                # Pydantic schemas & state machines
│   │   ├── self_healing_api.py      # Self-Healing endpoints
│   │   ├── self_healing_engine.py   # RCA, plan generator & rollback
│   │   ├── soar_api.py              # Visual SOAR Builder REST API
│   │   ├── soar_engine.py           # SOAR DAG execution & node runner
│   │   ├── soar_models.py           # Playbook schema & execution logs
│   │   ├── topology_api.py          # Threat Topology REST API
│   │   ├── topology_engine.py       # Graph centrality & blast radius
│   │   └── verifier.py              # Dual-probe synthetic verification
│   └── engine/
│       ├── pipeline.py              # Telemetry ingestion pipeline
│       └── detector.py              # Threat pattern matching engine
├── static/
│   ├── css/
│   │   ├── obsidian-sentinel.css    # SOC design identity system
│   │   ├── dashboard.css            # SOC layout & widgets
│   │   ├── shopsphere.css           # Consumer storefront styling
│   │   └── soar.css                 # Node canvas & DAG styles
│   └── js/
│       ├── dashboard.js             # Threat Center reactive state
│       ├── shopsphere.js            # Storefront shopping cart & auth
│       ├── soar.js                  # SOAR canvas drag-and-drop builder
│       └── topology.js              # Interactive D3/SVG threat graph
└── templates/
    ├── dashboard.html               # Obsidian Sentinel SOC portal
    └── shopsphere.html              # ShopSphere consumer storefront
```

---

## 3. Dependency Manifest & Locking

Key production dependencies verified in [requirements.txt](file:///C:/Users/bobba/Documents/AD/autoheal/requirements.txt):

```text
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
jinja2>=3.1.5
python-multipart>=0.0.20
scikit-learn>=1.6.0
joblib>=1.4.2
numpy>=2.2.0
pandas>=2.2.3
requests>=2.32.3
httpx>=0.28.1
pytest>=8.3.4
pytest-asyncio>=0.25.0
python-dotenv>=1.0.1
```

---

## 4. Database Schema & Migration Baseline

- **Database File:** `autoheal/data/shopsphere.db`
- **Schema Version:** `3.0-final`
- **Table Count:** 30 normalized tables
- **Journal Mode:** `WAL` (Write-Ahead Logging)
- **Synchronous Pragma:** `NORMAL`
- **Referential Integrity:** Enforced (`PRAGMA foreign_keys = ON`)
- **Seeded Identity Accounts:**
  - Standard Customer: `rahul.shopper@example.com`
  - SOC Administrator: `admin@shopsphere.com`
- **Default SOAR Playbooks Seeded:** 5 pre-configured enterprise playbooks (Credential Stuffing Containment, SQLi Hotpatching, API Flood Throttling, Malicious Session Revocation, Phishing Triage).

---

## 5. Automated Verification & Artifact Integrity

- **Automated Tests Executed:** 227 tests across 20 test files.
- **Pass Rate:** 100% (227 passed, 0 failed, 0 skipped).
- **Execution Elapsed Time:** 292.99s.
- **Phase 10 Certification Suite:** 13 passed in 85.93s.
- **Defects Identified & Repaired:** 3 (DEF-001, DEF-002, DEF-003).

---

## 6. Release Sign-Off

The release manifest is sealed. The codebase at commit `897880b` + Phase 10 patches represents the certified, immutable baseline for the AutoHeal v3.0.0-enterprise distribution.
