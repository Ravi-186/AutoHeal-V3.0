# AutoHeal v3.0 — Troubleshooting & Diagnostic Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Date:** November 1, 2026  

---

## 1. Quick Diagnostic Triage Table

| Symptom | Probable Cause | Immediate Remediation Command |
|---|---|---|
| **Port 8000 Already in Use** | Orphaned uvicorn or background process | `Get-NetTCPConnection -LocalPort 8000 \| Stop-Process` |
| **HTTP 429 Too Many Requests** | Rate limiter triggered (15 req in 8s) | Wait 8s or clear `blocked_clients` SQLite table |
| **Database Locked Error** | High concurrency lock contention | Verify `PRAGMA journal_mode = WAL;` and `busy_timeout=5000` |
| **SOAR Execution Failed** | Attempted to execute `DRAFT` playbook | Publish playbook version via `/api/soar/playbooks/{id}/publish` |
| **Verification Failed / Rollback**| Dual-probe invariant violated | Check if WAF rule over-blocks normal traffic |
| **SSE Disconnected Badge** | Client network drop or proxy timeout | Frontend automatically retries with 5s polling fallback |

---

## 2. Detailed Diagnostic Walkthroughs

### Issue 1: Port 8000 Address Conflict
**Error:** `OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`  
**Diagnosis:** A previous instance of Uvicorn or another local web service is currently listening on port 8000.  
**Resolution:**
```powershell
# On Windows PowerShell:
$procId = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess
if ($procId) {
    Write-Host "Killing process on port 8000: PID $procId"
    Stop-Process -Id $procId -Force
}

# On Linux:
sudo fuser -k 8000/tcp
```

---

### Issue 2: Client IP Quarantined / Rate Limited
**Error:** Legitimate testing requests from `127.0.0.1` receive `HTTP 403 Forbidden` or `HTTP 429 Too Many Requests`.  
**Diagnosis:** The client IP exceeded the sliding window rate limit (15 requests in 8.0 seconds) or was quarantined during an attack simulation test.  
**Resolution:**
1. Wait 8.0 seconds for the in-memory sliding window ring buffer to expire.
2. Remove the IP from the SQLite persistent quarantine table:
   ```powershell
   cd autoheal
   python -c "import sqlite3; conn = sqlite3.connect('data/shopsphere.db'); conn.execute('DELETE FROM blocked_clients WHERE client_ip = ''127.0.0.1'''); conn.commit(); print('Quarantine cleared.')"
   ```
3. Restart the server if in-memory rate tracker reset is required.

---

### Issue 3: SQLite Database Locked Contention
**Error:** `sqlite3.OperationalError: database is locked`  
**Diagnosis:** SQLite was opened in standard rollback journal mode or a long-running transaction blocked writers.  
**Resolution:**
Confirm WAL mode and busy timeout pragmas are active:
```powershell
python -c "import sqlite3; conn = sqlite3.connect('data/shopsphere.db'); print('Journal Mode:', conn.execute('PRAGMA journal_mode').fetchone()[0]); conn.execute('PRAGMA journal_mode = WAL'); conn.commit()"
```
Output must read: `Journal Mode: wal`.

---

### Issue 4: SOAR Playbook Fails to Execute in Live Mode
**Error:** `Execution status immediately transitions to FAILED`  
**Diagnosis:** The target playbook is in status `DRAFT`. Only playbooks in status `PUBLISHED` or `ACTIVE` are permitted to execute in LIVE mode against the application.  
**Resolution:**
Publish the playbook draft before execution:
```bash
curl -X POST http://127.0.0.1:8000/api/soar/playbooks/<PLAYBOOK_ID>/publish
```

---

### Issue 5: Dual-Probe Synthetic Verification Rejection
**Error:** Self-healing status transitions to `VERIFICATION_FAILED` and triggers automated rollback.  
**Diagnosis:** The dual-probe verifier requires BOTH:
- Probe 1 (Benign shopper flow) to return **HTTP 200 OK**.
- Probe 2 (Exploit replay) to return **HTTP 403 Forbidden**.
If the deployed hotpatch was too broad (e.g. blocking all queries with the word "product"), Probe 1 fails with 403. The system automatically rolls back the hotpatch within 50ms to protect business operations.  
**Resolution:** Refine the WAF regex pattern to target only malicious syntax fragments (e.g. `' OR 1=1--`), leaving legitimate shopping queries unaffected.

---

## 3. Log Inspection Commands

```powershell
# Inspect server stdout / stderr logs
Get-Content -Path "autoheal\server.log" -Tail 50 -Wait

# Query recent security events directly from database
python -c "import sqlite3; conn = sqlite3.connect('data/shopsphere.db'); conn.row_factory = sqlite3.Row; [print(r['timestamp'], r['action_taken'], r['path']) for r in conn.execute('SELECT * FROM security_events ORDER BY id DESC LIMIT 10')]"
```

---

## 4. Troubleshooting Sign-Off

All identified operational anomalies have clear diagnostic paths, deterministic error messages, and automated recovery procedures.
