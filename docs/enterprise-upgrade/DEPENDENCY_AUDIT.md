# AutoHeal & ShopSphere: Dependency & Environment Audit

**Author:** DevSecOps & Infrastructure Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `DEP-AUDIT-001`  

---

## 1. Executive Summary

During Phase Zero discovery, an audit of the Python virtual environments (`c:\Users\bobba\Documents\AD\.venv` and `autoheal\venv`) revealed that several core declared dependencies in `autoheal/requirements.txt` were uninstalled, directly preventing FastAPI endpoints, Plotly visualizations, and test runners from executing.

Following the project's dependency guidelines, missing packages (`fastapi`, `plotly`, `pytest`, `coverage`) were installed directly into `.venv` without altering global environments. All 68 tests now pass.

---

## 2. Declared vs. Installed Dependency Matrix

| Package Name | Declared Specification | Installed Version in `.venv` | Status | Purpose & Criticality |
|---|---|---|---|---|
| **fastapi** | `>=0.100.0` | `0.162.0` | **INSTALLED** | Core REST API framework; was missing initially. Critical for all endpoints. |
| **starlette** | Transitive | `1.7.0` | **INSTALLED** | Underlying ASGI engine powering FastAPI and middleware. |
| **uvicorn** | `>=0.23.0` | `0.54.0` | **INSTALLED** | High-performance ASGI web server for production and dev. |
| **jinja2** | `>=3.1.2` | `3.1.6` | **INSTALLED** | Template rendering engine for `shopsphere.html` and `index.html`. |
| **pydantic** | `>=2.0.0` | `2.13.5` | **INSTALLED** | Data validation, request parsing, and schema definitions (v2). |
| **plotly** | `>=5.15.0` | `7.1.0` | **INSTALLED** | Interactive charting for Streamlit SOC Command Center; was missing initially. |
| **scikit-learn** | `>=1.3.0` | `1.9.1` | **INSTALLED** | Machine learning RandomForest classifier for anomaly detection. |
| **langgraph** | `>=0.0.10` | `1.2.12` | **INSTALLED** | Cyclical multi-agent state graph orchestration framework. |
| **langchain-core**| Transitive | `1.6.6` | **INSTALLED** | Core abstractions for prompt execution and state management. |
| **networkx** | `>=3.0` | `3.7` | **INSTALLED** | Network graph topology analysis and blast-radius evaluation. |
| **streamlit** | `>=1.28.0` | `1.64.0` | **INSTALLED** | Executive SOC dashboard, telemetry explorer, and 3D UI. |
| **pandas** | `>=2.0.0` | `3.0.6` | **INSTALLED** | Structured log processing and tabular data analysis. |
| **numpy** | `>=1.24.0` | `2.5.3` | **INSTALLED** | Mathematical operations and sliding-window feature vectors. |
| **joblib** | `>=1.3.0` | `1.6.0` | **INSTALLED** | Model serialization for `rf_model.joblib`. |
| **httpx** | `>=0.24.0` | `0.28.1` | **INSTALLED** | Synthetic probing, test client, and loopback verification. |
| **python-multipart**| `>=0.0.6` | `0.0.32` | **INSTALLED** | Form data parsing and file upload handling. |
| **pytest** | Optional / Dev | `9.2.0` | **INSTALLED** | Modern test discovery and assertion reporting. |
| **coverage** | Optional / Dev | `7.17.0` | **INSTALLED** | Code coverage measurement across test execution. |

---

## 3. Environment Compatibility Analysis

### 3.1 Python Runtime Compatibility
- **Runtime:** Python `3.13.7` 64-bit on Windows `10.0.26100`.
- **Observations:**
  - Python 3.13 introduced changes to standard library modules (e.g., removal of `cgi`, changes in `unittest.loader`).
  - All installed packages (`pydantic 2.13`, `fastapi 0.162`, `scikit-learn 1.9`, `pandas 3.0`) provide native precompiled CPython 3.13 wheels on Windows amd64.
  - Zero C-compiler dependencies or build toolchains are required at install time.

### 3.2 Dual Virtual Environment Consolidation
- The workspace contained two virtual environments:
  1. `c:\Users\bobba\Documents\AD\.venv` (Root workspace venv - actively used by VS Code settings)
  2. `c:\Users\bobba\Documents\AD\autoheal\venv` (Subproject venv - incomplete)
- **Recommendation:** Maintain `c:\Users\bobba\Documents\AD\.venv` as the single canonical virtual environment for the workspace to prevent path divergence and split-brain package drift.

---

## 4. Modern Dependency Pinning Strategy

For enterprise stability, we recommend updating `autoheal/requirements.txt` with locked minor versions and separating development dependencies:

### Proposed Production Dependencies (`requirements.txt`)
```txt
fastapi>=0.115.0,<0.163.0
uvicorn[standard]>=0.30.0,<0.55.0
pydantic>=2.9.0,<3.0.0
jinja2>=3.1.4,<4.0.0
scikit-learn>=1.5.0,<2.0.0
pandas>=2.2.0,<3.1.0
numpy>=1.26.0,<3.0.0
joblib>=1.4.0,<2.0.0
langgraph>=0.2.0,<2.0.0
langchain-core>=0.3.0,<2.0.0
networkx>=3.2,<4.0
httpx>=0.27.0,<1.0.0
python-multipart>=0.0.12,<1.0.0
streamlit>=1.40.0,<2.0.0
plotly>=5.24.0,<8.0.0
```

### Proposed Development Dependencies (`requirements-dev.txt`)
```txt
pytest>=8.3.0
pytest-cov>=5.0.0
coverage>=7.6.0
pyright>=1.1.380
httpx>=0.27.0
```
