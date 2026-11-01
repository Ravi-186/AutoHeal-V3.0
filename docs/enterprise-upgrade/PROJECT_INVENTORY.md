# AutoHeal & ShopSphere: Project Inventory

**Author:** Enterprise Engineering Architecture Organization  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC & ShopSphere Target Application  
**Workspace Root:** `c:\Users\bobba\Documents\AD`  
**Git Branch:** `enterprise-upgrade`  

---

## 1. Executive Summary

This inventory catalogs every directory, component, service, model, database artifact, frontend template, simulation script, and test suite within the AutoHeal and ShopSphere codebase.

The repository represents an integrated autonomous security ecosystem comprising:
1. **Application A (ShopSphere):** A full-featured Flipkart-inspired e-commerce storefront acting as a realistic target application with database persistence, transactional checkout, cart financial invariant logic, and role-based access.
2. **Application B (AutoHeal):** An autonomous Security Operations Center (SOC) platform powered by LangGraph multi-agent loops, scikit-learn anomaly detection, sliding-window log correlation, automated defense mitigation (WAF, 802.1X, Microsegmentation), synthetic verification, and transparent posture scoring.

---

## 2. Directory Hierarchy & Component Mapping

```
AD/
├── .gitignore                          # Workspace VCS ignore configuration
├── pyrightconfig.json                  # Python type checker settings
├── docs/                               # Enterprise architecture & upgrade documentation
│   └── enterprise-upgrade/             # Enterprise audit, tracking, and architectural specifications
└── autoheal/                           # Primary application root
    ├── .env.example                    # Environment configuration template
    ├── .gitignore                      # Python/OS ignore rules
    ├── Dockerfile                      # Container specification
    ├── docker-compose.yml              # Multi-service local composition
    ├── pyrightconfig.json              # Subproject type checking configuration
    ├── README.md                       # High-level architecture and startup instructions
    ├── requirements.txt                # Python package dependency specifications
    ├── server.py                       # Unified FastAPI application server (AutoHeal + ShopSphere)
    │
    ├── src/                            # AutoHeal Core Engineering Modules
    │   ├── config.py                   # Centralized runtime configuration & environment resolution
    │   ├── schemas.py                  # Pydantic data exchange models
    │   ├── agents/                     # LangGraph Autonomous Agent Definitions
    │   │   ├── detection_agent.py      # Telemetry feature analysis & ML inference agent
    │   │   ├── response_agent.py       # Policy mitigation selector (Isolate, Block, Escalate)
    │   │   └── verification_agent.py   # Closed-loop mitigation verification agent
    │   ├── appsec/                     # Enterprise Application Security (AppSec) Framework
    │   │   ├── ai_advisor.py           # Grounded AI forensic analysis & MITRE mapping
    │   │   ├── api.py                  # REST API for SOC telemetry, incidents, and test launcher
    │   │   ├── correlation_engine.py   # Multi-event sliding-window temporal correlation
    │   │   ├── detector.py             # Rule-based & regex inspection (SQLi, XSS, Brute-Force)
    │   │   ├── middleware.py           # ASGI interception, telemetry recording & dynamic WAF
    │   │   ├── models.py               # Data models & persistence helpers for AppSec entities
    │   │   ├── pdf_generator.py        # Pure-Python zero-dependency PDF 1.4 report compiler
    │   │   ├── posture_scorer.py       # Deterministic 0-100 posture scoring engine
    │   │   ├── reporter.py             # Markdown, JSON & PDF forensic dossier generator
    │   │   ├── responder.py            # Defensive playbook executor with dry-run & rollback
    │   │   ├── security_tester.py      # Authorized localhost-only security test harness
    │   │   ├── verifier.py             # Dual-probe verification (quarantine + availability)
    │   │   └── vulnerability_manager.py# Vulnerability ledger, patch proposal & regression runner
    │   ├── correlation/                # Legacy/Network-level correlation
    │   │   └── engine.py               # Multi-source log correlation & attack path extraction
    │   ├── detection/                  # Machine Learning Threat Detection Pipeline
    │   │   ├── feature_extractor.py    # Sliding window feature synthesis
    │   │   ├── generate_dataset.py     # Nominal vs attack telemetry dataset generator
    │   │   ├── model.py                # Scikit-learn RandomForestClassifier wrapper
    │   │   └── train_model.py          # Model training & joblib persistence pipeline
    │   ├── graph/                      # Agentic Orchestration State Graph
    │   │   └── workflow.py             # LangGraph stateful cyclic workflow (Detect->Respond->Verify)
    │   └── simulator/                  # Multi-Vector Network & Log Generator
    │       ├── log_generator.py        # Synthetic firewall, DNS, login, device event stream
    │       ├── network.py              # Zero-trust topology, VLANs, and stateful endpoints
    │       └── scenarios.py            # Adversary attack scenarios (A, B, C, D & Flipkart)
    │
    ├── shopsphere/                     # ShopSphere Production E-Commerce Application
    │   ├── api.py                      # Storefront, cart, checkout, admin & autoheal endpoints
    │   ├── autoheal_engine.py          # Controlled demo fault injector & AI patch demonstrator
    │   ├── database.py                 # SQLite schema initialization, connection pool, seed catalog
    │   └── services.py                 # Business logic (Products, Cart, Order, User, Admin)
    │
    ├── dashboard/                      # Enterprise Streamlit SOC Command Center
    │   ├── app.py                      # Primary SOC visualizer, 3D topology & triage workspace
    │   ├── attack_path3d.py            # Three.js 3D lateral movement attack path renderer
    │   ├── background3d.py             # WebGL 3D dynamic particle grid background
    │   └── assets/                     # HTML/JS templates for Three.js components
    │
    ├── web/                            # Fast-API Static & Server-Side Rendered Templates
    │   ├── templates/
    │   │   ├── index.html              # Standalone web dashboard portal
    │   │   └── shopsphere.html         # Flipkart-style modern e-commerce storefront UI
    │   └── static/
    │       ├── css/style.css           # Glassmorphism and dark mode theme styling
    │       ├── js/script.js            # Frontend interactivity and API polling
    │       └── img/bg.jpg              # Graphical background assets
    │
    ├── data/                           # Persistent Database & CSV Log Storage
    │   ├── shopsphere.db               # SQLite active relational database
    │   ├── firewall_logs.csv           # Streaming network telemetry
    │   ├── dns_logs.csv                # Streaming domain resolution telemetry
    │   ├── login_logs.csv              # Authentication telemetry
    │   └── device_logs.csv             # Host resource telemetry (CPU/Memory)
    │
    ├── models/                         # Serialized Machine Learning Artifacts
    │   └── rf_model.joblib             # Trained RandomForestClassifier binary
    │
    ├── tests/                          # Automated Unit, Integration & Regression Test Suites
    │   ├── test_agents.py              # Unit tests for Detection, Response, Verification agents
    │   ├── test_api.py                 # API integration tests for AutoHeal endpoints
    │   ├── test_appsec_pipeline.py     # E2E AppSec detection, mitigation, verification tests
    │   ├── test_engine.py              # Anomaly detection engine unit tests
    │   ├── test_five_security_components.py # Comprehensive 5-component AppSec suite
    │   ├── test_langgraph.py           # LangGraph cyclical state transition tests
    │   ├── test_live_security_testing.py# Live HTTP security testing against FastAPI
    │   ├── test_model.py               # ML model evaluation & threshold verification
    │   ├── test_shopsphere.py          # E-Commerce business logic & cart invariant tests
    │   └── test_simulator.py           # Adversary scenario simulation tests
    │
    ├── scripts/                        # Operational, Verification & Diagnostic Utilities
    │   ├── verify_full_system.py       # Full system diagnostic runner
    │   ├── verify_all_scenarios.py     # Scenario matrix verification
    │   ├── build_full_report.py        # Comprehensive report compilation script
    │   └── generate_diagrams.py        # Mermaid diagram renderer
    │
    └── run_*.py                        # Standalone Executable Demo Scripts
        ├── run_demo.py                 # CLI end-to-end adversary simulation & LangGraph loop
        ├── run_appsec_demo.py          # AppSec 6-scenario live demonstration
        ├── run_shopsphere_demo.py      # ShopSphere 11-step e-commerce self-healing demo
        ├── run_security_test.py        # Security testing harness CLI
        └── run_simulator.py            # Baseline traffic generator CLI
```

---

## 3. Technology Stack & Framework Inventory

| Layer | Technologies Used | Version / Constraints | Purpose |
|---|---|---|---|
| **Programming Language** | Python | 3.13.7 (64-bit Windows) | Core runtime environment |
| **Web API Framework** | FastAPI, Starlette, Uvicorn | FastAPI >=0.100.0, Starlette 1.7.0 | High-performance async ASGI REST API |
| **Interactive SOC UI** | Streamlit, Plotly, Three.js | Streamlit 1.64.0, Plotly 7.1.0 | 3D visual command center and telemetry |
| **Storefront Web UI** | HTML5, Vanilla CSS3, JavaScript | ES6+, Jinja2 templates | Flipkart replica storefront |
| **Relational Database** | SQLite3 (WAL Mode) | SQLite 3.45+ (Python built-in) | Persistent relational store |
| **AI / Agentic Graph** | LangGraph, LangChain Core | LangGraph 1.2.12, LangChain-Core 1.6.6 | Stateful cyclical agent workflows |
| **Machine Learning** | Scikit-Learn, NumPy, Pandas | Scikit-Learn 1.9.1, Pandas 3.0.6 | RandomForest threat detection |
| **Network & HTTP Client**| HTTPX | HTTPX 0.28.1 | Synthetic probing & test harness |
| **Testing Framework** | Unittest, Pytest | Pytest 9.2.0, Unittest | Test discovery & test execution |

---

## 4. Operational File & Asset Summary

- **Total Source Files (`.py`):** 46
- **Total Test Files:** 14 (10 inside `tests/`, 4 root runners)
- **Total Frontend Templates & Static Files:** 6 (`shopsphere.html`, `index.html`, `style.css`, `script.js`, `scene.html`, `attack_path_component`)
- **Active SQLite Tables:** 12 tables in `shopsphere.db`
- **Total Machine Learning Models:** 1 (`rf_model.joblib`)
- **Total Test Cases Currently Discovered:** 68 passing test cases across the entire test suite.
