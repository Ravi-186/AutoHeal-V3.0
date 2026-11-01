# AutoHeal & ShopSphere: Production Deployment Guide

**Author:** DevSecOps Lead & Cloud Infrastructure Engineer  
**Document Ref:** `DEP-GUIDE-001`  
**Date:** 2026-11-01  

---

## 1. System Requirements & Prerequisites

- **Python Runtime:** Python 3.10, 3.11, or 3.12
- **Operating Systems:** Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9), macOS 13+, Windows 10/11 Server
- **Memory:** Minimum 2 GB RAM (4 GB recommended for concurrent telemetry analysis)
- **Disk:** 500 MB for codebase and runtime virtual environment; 2 GB+ for persistent telemetry and logs
- **Ports:**
  - `8000`: AutoHeal Core Sentinel API & ShopSphere Storefront
  - `8501`: AutoHeal Enterprise 3D SOC Dashboard (Streamlit)

---

## 2. Step-by-Step Production Installation

```bash
# 1. Clone repository and navigate to root
cd /opt/autoheal

# 2. Initialize Virtual Environment
python -m venv .venv

# 3. Activate Virtual Environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\Activate.ps1

# 4. Install Dependencies
pip install --upgrade pip
pip install -r autoheal/requirements.txt
pip install fastapi plotly pytest coverage

# 5. Initialize Database Schema & Seed Baseline Catalog
python -c "import sys; sys.path.insert(0, 'autoheal'); from shopsphere.database import seed_data; seed_data()"
```

---

## 3. Starting the Production Services

### Option A: Local Process Daemon (Development / Staging)
```bash
# Terminal 1: Start AutoHeal API & ShopSphere Storefront
python autoheal/server.py

# Terminal 2: Start AutoHeal Enterprise SOC Dashboard
streamlit run autoheal/dashboard/app.py --server.port 8501
```

### Option B: Systemd Service Units (Production Linux)

Create `/etc/systemd/system/autoheal-backend.service`:
```ini
[Unit]
Description=AutoHeal Autonomous SOC Backend
After=network.target

[Service]
Type=simple
User=autoheal
WorkingDirectory=/opt/autoheal/autoheal
ExecStart=/opt/autoheal/.venv/bin/python server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/autoheal-dashboard.service`:
```ini
[Unit]
Description=AutoHeal Enterprise SOC Dashboard
After=autoheal-backend.service

[Service]
Type=simple
User=autoheal
WorkingDirectory=/opt/autoheal/autoheal
ExecStart=/opt/autoheal/.venv/bin/streamlit run dashboard/app.py --server.port 8501 --server.headless true
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Reload and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now autoheal-backend autoheal-dashboard
```

---

## 4. Reverse Proxy & SSL Termination (Nginx)

```nginx
server {
    listen 80;
    server_name soc.enterprise.internal;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name soc.enterprise.internal;

    ssl_certificate /etc/ssl/certs/autoheal.crt;
    ssl_certificate_key /etc/ssl/private/autoheal.key;

    # AutoHeal Backend & Storefront API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Streamlit SOC Dashboard
    location /dashboard/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
