# AutoHeal & ShopSphere: Automated Testing & Verification Guide

**Author:** QA Automation Lead & Site Reliability Engineer  
**Document Ref:** `TEST-GUIDE-001`  
**Date:** 2026-11-01  

---

## 1. Test Architecture & Directory Structure

AutoHeal maintains 10 dedicated test suites inside `autoheal/tests/`:

```
autoheal/tests/
├── test_agents.py                   # Unit tests for DetectionAgent, ResponseAgent, VerificationAgent
├── test_api.py                      # FastAPI endpoint tests, metric dynamics, measured latency
├── test_appsec_pipeline.py          # AppSec end-to-end telemetry and mitigation pipeline tests
├── test_engine.py                   # Core detection engine heuristic tests
├── test_five_security_components.py # Architectural tests for 5 SOC sentinel components
├── test_langgraph.py                # LangGraph state machine workflow and retry loop tests
├── test_live_security_testing.py    # Live attack injection, export, and replay comparison tests
├── test_model.py                    # Isolation Forest anomaly detection model tests
├── test_shopsphere.py               # E-commerce customer journeys & Admin RBAC verification
└── test_simulator.py                # Synthetic enterprise network and log generator tests
```

---

## 2. Running Automated Tests

### 2.1 Complete Test Suite Discovery
```bash
cd autoheal
python -m unittest discover tests
```
- **Expected Execution Time:** ~110 seconds
- **Expected Result:** `Ran 72 tests in 110s -> OK` (0 failures, 0 errors, 0 skipped)

### 2.2 Running Specific Test Suites
```bash
# E-commerce and RBAC security tests
python -m unittest tests/test_shopsphere.py

# Live security testing and replay attack comparison
python -m unittest tests/test_live_security_testing.py

# FastAPI endpoints and dynamic metric tests
python -m unittest tests/test_api.py
```

### 2.3 Running Standalone Demonstration & Verification Scripts
```bash
# Full AppSec automated detection & mitigation demonstration (6 scenarios)
python run_appsec_demo.py

# Full ShopSphere storefront & invariant self-healing demonstration (11 steps)
python run_shopsphere_demo.py
```
