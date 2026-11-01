# AutoHeal & ShopSphere: Production Operational Troubleshooting Runbook

**Author:** Site Reliability Engineer & SOC Operations Lead  
**Document Ref:** `OPS-TROUBLE-001`  
**Date:** 2026-11-01  

---

## 1. Common Operational Issues & Runbook Resolutions

### Issue 1: Legitimate Client IP Accidentally Quarantined
- **Symptom:** Client receives `HTTP 403 Forbidden` with body `"error": "Client IP Quarantined by AutoHeal Sentinel"`.
- **Diagnosis:** Check `/api/security/blocked-clients` to see if IP is in active blocklist and review the triggering `rule_id`.
- **Resolution:**
  ```bash
  curl -X POST http://localhost:8000/api/security/unblock \
       -H "Content-Type: application/json" \
       -d '{"client_ip": "198.51.100.22"}'
  ```

### Issue 2: Database Locked Error (`sqlite3.OperationalError: database is locked`)
- **Symptom:** Fast concurrent requests report database lock timeout.
- **Diagnosis:** WAL journal mode or busy timeout is misconfigured.
- **Resolution:**
  - Verify WAL mode: `PRAGMA journal_mode = WAL;`
  - Verify busy timeout is set to 30.0 seconds: `sqlite3.connect(DB_PATH, timeout=30.0)`
  - Ensure all database connections are closed using the `@contextmanager` pattern (`get_db_connection()`).

### Issue 3: Streamlit Dashboard Posture Score Shows "Offline"
- **Symptom:** Dashboard KPI card indicates Posture Score unavailable.
- **Diagnosis:** Missing import or database connection failure.
- **Resolution:** Ensure `PostureScorer` and `SecurityPostureScorer` are both imported and `data/shopsphere.db` exists with seed catalog populated.

### Issue 4: Admin Modal Returns 401 Unauthorized
- **Symptom:** Clicking "Admin Portal" on ShopSphere displays authentication prompt error.
- **Diagnosis:** Session token expired or legacy token was revoked.
- **Resolution:** Log in via `/api/shop/auth/login` using administrative credentials (`admin@shopsphere.com` / `Admin@123`). The API returns a cryptographically secure token that is stored in `localStorage` under `shopsphere_auth_token`.
