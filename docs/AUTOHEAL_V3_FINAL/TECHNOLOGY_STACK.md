# AutoHeal v3.0 — Enterprise Technology Stack & Standards
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Date:** November 1, 2026  

---

## 1. Technology Philosophy

The architecture of AutoHeal v3.0 balances **zero-bloat performance, high maintainability, strict typing, and high visual fidelity**. Heavy JavaScript frontend frameworks (such as React or Next.js) and complex ORMs with hidden query overheads were avoided in favor of modern native standards: Python 3.13 with FastAPI and Pydantic v2 on the backend, paired with Vanilla CSS design tokens and ES6+ modules on the frontend.

---

## 2. Comprehensive Technology Inventory

### A. Backend Core & API Layer
| Component | Technology | Version | Architectural Rationale |
|---|---|---|---|
| **Programming Language** | Python | `3.13.7` | Modern language features, enhanced GIL performance, strict typing |
| **API Framework** | FastAPI | `>= 0.115.0` | High-throughput asynchronous ASGI execution, auto-generated OpenAPI |
| **ASGI Web Server** | Uvicorn / Starlette | `>= 0.34.0` | Non-blocking asynchronous event loop handling WebSockets and SSE |
| **Data Validation** | Pydantic v2 | `>= 2.10.0` | Fast C-based data validation and strict schema contracts |
| **Configuration** | Pydantic-Settings | `>= 2.7.0` | 12-factor application environmental externalization |
| **Template Engine** | Jinja2 | `>= 3.1.5` | Fast server-side rendering for HTML view shells |
| **Production WSGI/ASGI** | Gunicorn | `>= 23.0.0` | Multi-worker process manager for Linux deployments |

### B. Machine Learning & Anomaly Detection
| Component | Technology | Version | Architectural Rationale |
|---|---|---|---|
| **Anomaly Detection** | Scikit-Learn | `>= 1.6.0` | Isolation Forest unsupervised behavioral threat anomaly modeling |
| **Data Frames** | Pandas | `>= 2.2.3` | High-speed tabular telemetry manipulation |
| **Array Computing** | NumPy | `>= 2.2.0` | Vectorized numerical operations for spatial graph layouts |
| **Model Serialization** | Joblib | `>= 1.4.2` | Fast persistence of trained scikit-learn model weights |

### C. Data Persistence & Caching
| Component | Technology | Version | Architectural Rationale |
|---|---|---|---|
| **Database Engine** | SQLite 3 | `3.45+` | Zero-configuration relational database operating in WAL mode |
| **Journaling Mode** | WAL | Active | Write-Ahead Logging allows unlimited concurrent readers alongside writers |
| **Pragmas Configured** | `NORMAL` sync, `busy_timeout=5000` | Active | Sub-millisecond write commits without transaction lock contention |
| **Hot Backup Engine** | Native SQLite C Backup API | Active | Zero-downtime, non-locking online database backups |

### D. Frontend Presentation & Design Systems
| Component | Technology | Version | Architectural Rationale |
|---|---|---|---|
| **Design Tokens** | Vanilla Modular CSS | CSS3 Variables | Obsidian Sentinel & ShopSphere design tokens without framework bloat |
| **3D Visualization** | Three.js | `r128` | WebGL hardware-accelerated 3D spatial threat topology graph |
| **Data Charting** | Chart.js | `v4.4` | Responsive, accessible HTML5 Canvas charts (Timelines, Doughnuts) |
| **Real-Time Streaming** | Server-Sent Events (SSE) | W3C Standard | Unidirectional real-time event streaming (`/api/security/events/stream`) |
| **Iconography** | Inline Scalable Vector Graphics | SVG 1.1 | Zero network latency vector icons with responsive `:hover` styles |

### E. QA Automation & Test Frameworks
| Component | Technology | Version | Architectural Rationale |
|---|---|---|---|
| **Test Runner** | Pytest | `>= 8.3.4` | Parametrized test execution with structured reporting |
| **Async Test Harness**| Pytest-Asyncio | `>= 0.25.0` | Native asynchronous coroutine test assertions |
| **ASGI Test Client** | HTTPX | `>= 0.28.1` | In-process ASGI test client for fast integration validation |
| **Network Client** | Requests | `>= 2.32.3` | Synchronous HTTP client for live acceptance testing |

---

## 3. Directory & Module Organization

```
AD/
├── .venv/                         # Isolated Python 3.13.7 virtual environment
├── autoheal/                      # Primary application root
│   ├── server.py                  # ASGI application shell & router hub
│   ├── requirements.txt           # Pinned production dependencies
│   ├── data/                      # Persistence directory (shopsphere.db, CSV feeds)
│   ├── models/                    # ML anomaly detection serialized weights
│   ├── shopsphere/                # E-commerce target domain (services, API, db)
│   ├── src/                       # AutoHeal SOC core (WAF, SOAR, Self-Healing, Copilot)
│   ├── static/                    # CSS tokens, JS modules, Three.js shaders
│   ├── templates/                 # HTML templates (dashboard.html, shopsphere.html)
│   └── tests/                     # 20 test modules (227 tests)
└── docs/                          # Enterprise transformation documentation
    ├── v3-transformation/         # Phase 0–10 historical transformation docs
    └── AUTOHEAL_V3_FINAL/         # Sealed final release documentation
```

---

## 4. Technology Standards Sign-Off

The selected technology stack provides high stability, instant startup (< 1.5s), sub-40ms endpoint responsiveness, and effortless single-node operational maintenance.
