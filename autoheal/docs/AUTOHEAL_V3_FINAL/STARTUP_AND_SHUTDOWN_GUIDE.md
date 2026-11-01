# AutoHeal v3.0 — Service Startup & Shutdown Operations Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Date:** November 1, 2026  

---

## 1. Startup Workflows by Environment

### A. Local Development Startup (Windows PowerShell)
```powershell
# 1. Open PowerShell and navigate to repository root
cd C:\Users\bobba\Documents\AD

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Enter autoheal directory
cd autoheal

# 4. Start Uvicorn development server with live reload
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### B. Windows Background Daemon Startup
To run the server as a persistent background process without tying up a console window:
```powershell
Start-Process -FilePath "C:\Users\bobba\Documents\AD\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn server:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory "C:\Users\bobba\Documents\AD\autoheal" `
    -WindowStyle Hidden
```

### C. Linux Production Startup (Systemd Service)
Create `/etc/systemd/system/autoheal.service`:
```ini
[Unit]
Description=AutoHeal Autonomous SOC & ShopSphere E-Commerce Application
After=network.target

[Service]
Type=simple
User=autoheal
Group=autoheal
WorkingDirectory=/opt/autoheal/autoheal
Environment="PATH=/opt/autoheal/.venv/bin"
EnvironmentFile=/opt/autoheal/autoheal/.env
ExecStart=/opt/autoheal/.venv/bin/gunicorn server:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/autoheal/access.log \
    --error-logfile /var/log/autoheal/error.log \
    --graceful-timeout 10
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autoheal
sudo systemctl start autoheal
sudo systemctl status autoheal
```

---

## 2. Post-Startup Health Verification

Verify service responsiveness immediately after startup:
```bash
# Verify core platform health (Expect HTTP 200)
curl -f http://127.0.0.1:8000/api/health

# Verify ShopSphere storefront health (Expect HTTP 200)
curl -f http://127.0.0.1:8000/api/shop/health

# Verify SOC detailed health panel (Expect overall_status: "healthy")
curl -f http://127.0.0.1:8000/api/security/health/detailed
```

---

## 3. Orderly Shutdown Procedures

FastAPI and Uvicorn handle `SIGTERM` and `SIGINT` signals with deterministic graceful shutdown:

### What Happens During Graceful Shutdown:
1. **Connection Draining:** Ingress stops accepting new TCP connections. In-flight HTTP requests have a 10-second budget to complete.
2. **SOAR Worker Drainage:** Active non-approval DAG executions complete their current node.
3. **Database WAL Checkpointing:** In-memory SQLite write-ahead transactions are committed and checkpointed to disk (`shopsphere.db-wal` flushes to `shopsphere.db`).
4. **Log Flush:** Audit logs and security event buffers flush cleanly to disk.

### Windows Shutdown
- In active interactive terminal: Press `CTRL + C`.
- In background daemon mode:
  ```powershell
  # Find PID listening on port 8000
  $procId = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess
  if ($procId) { Stop-Process -Id $procId -Force }
  ```

### Linux Shutdown
```bash
# Graceful stop
sudo systemctl stop autoheal

# Graceful restart (e.g. after update)
sudo systemctl restart autoheal
```

---

## 4. Emergency Recovery & Disaster Protocol

If the process becomes unresponsive due to system-level deadlocks or resource starvation:
1. **Force Terminate:** `sudo systemctl kill -s SIGKILL autoheal` (or `taskkill /F /IM python.exe`).
2. **Verify SQLite Integrity:** Run SQLite integrity check on the database file before restart:
   ```bash
   sqlite3 autoheal/data/shopsphere.db "PRAGMA integrity_check;"
   ```
3. **Restart Cleanly:** `sudo systemctl start autoheal`.

---

## 5. Operations Sign-Off

The startup and shutdown procedures have been tested and verified across both Windows and Linux environments.
