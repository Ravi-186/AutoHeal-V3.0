# AutoHeal & ShopSphere: Enterprise Upgrade Changelog

All notable changes to the AutoHeal Autonomous SOC Platform and ShopSphere E-Commerce Target during the Enterprise Transformation are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.0-PROD] - 2026-11-01

### Security
- **REMOVED:** Eradicated master backdoor token `token_admin_shopsphere_secret` from `shopsphere/api.py` and `database.py`.
- **ADDED:** Dynamic cryptographically secure admin and customer token generation using `secrets.token_hex(24)`.
- **ADDED:** Database migration revoking and upgrading any legacy static tokens.
- **ADDED:** `TestShopSphereAdminRBAC` regression test suite covering 401 unauthenticated, 403 customer access, and 200 admin authorization.
- **ADDED:** Dual-probe synthetic loopback verification (perimeter 403 probe + availability 200 probe) in `AppSecVerifier`.

### Fixed
- **FIXED:** Missing `fastapi`, `plotly`, `pytest`, `coverage` dependencies in active `.venv` (BUG-001).
- **FIXED:** `PostureScorer` import mismatch in `dashboard/app.py` by adding alias in `posture_scorer.py` and dual-importing (BUG-002).
- **FIXED:** Duplicate route definition for `@router.get("/incidents/{incident_id}/export")` in `src/appsec/api.py` (BUG-003).
- **FIXED:** Implemented complete execution logic for `POST /api/security/test/replay` (`replay_attack_comparison`) returning structured before/after comparison states (BUG-004).
- **FIXED:** Removed fabricated device count formula in `server.py:155` (`len(devices) * 1152 + 14`); replaced with exact count `str(len(devices))` (BUG-006).
- **FIXED:** Replaced hardcoded `"remediation_time_ms": 842` in `server.py` and artificial `+ 12` ms addition in `responder.py` with true monotonic clock measurement using `time.perf_counter()` (BUG-007).
- **FIXED:** Replaced hardcoded `"average_remediation_ms": 38.5` in `/api/security/metrics` with dynamic calculation derived from persisted incident verification probe telemetry (BUG-008).
- **FIXED:** Integrated `TestClient(server_app)` in `security_tester.py:_get_client` to allow in-process ASGI execution against `http://testserver` without socket DNS lookups (BUG-009).
- **FIXED:** Added 7 composite performance indexes to `shopsphere/database.py:init_db()` for sub-millisecond telemetry and order lookups (BUG-010).

### Added
- **ADDED:** Atomic database transaction context (`with conn:`) to `OrderService.checkout` ensuring automatic rollback on checkout errors.
- **ADDED:** `test_security_metrics_dynamic` and `test_flipkart_heal_measured_latency` regression tests in `test_api.py`.
- **ADDED:** `test_11_replay_attack_comparison` regression test in `test_live_security_testing.py`.
- **ADDED:** Full enterprise documentation suite (19 documents) in `docs/enterprise-upgrade/`.
- **ADDED:** Final Master Transformation Report `AUTOHEAL_ENTERPRISE_TRANSFORMATION_REPORT.md`.
