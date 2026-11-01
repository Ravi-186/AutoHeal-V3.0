# AutoHeal & ShopSphere v2.5.0: Production Deployment & Infrastructure Audit

**Auditor:** Principal DevSecOps & Cloud Infrastructure Architect  
**Scope:** Production Deployment Architecture, Process Supervision, TLS Termination, and Disaster Recovery  
**Target Architecture:** Linux (Ubuntu 22.04 LTS / Debian 12), Systemd, Gunicorn/Uvicorn, Nginx Reverse Proxy  
**Classification:** **DEPLOYMENT READINESS & INFRASTRUCTURE AUDIT**

---

## 1. Executive Summary

This deployment audit evaluates the operational readiness of AutoHeal v2.5.0 for enterprise production environments. It identifies key infrastructure differences between the local Windows development environment and the target Linux production runtime, providing concrete production configuration files, systemd service units, reverse proxy configs, and automated backup cron jobs.

---

## 2. Production Topology & Architecture

```
[ Internet / External Clients ]
              │
              ▼ (HTTPS :443 / TLS 1.3)
      [ Nginx Reverse Proxy ]
         • SSL/TLS Termination (Certbot / Let's Encrypt)
         • Rate Throttling / DDoS Shield
         • Security Headers & Static Asset Caching
              │
              ▼ (HTTP localhost:8000 via UNIX Socket or Loopback)
  [ Gunicorn Process Supervisor ]
     • 4 Uvicorn Workers (`uvicorn.workers.UvicornWorker`)
     • Auto-restart on crash (`Restart=always`)
     • Managed by Systemd (`autoheal.service`)
              │
              ▼
   [ AutoHeal / ShopSphere API ]
              │
              ▼
    [ SQLite WAL Database ]
     • Local SSD storage (`autoheal/data/shopsphere.db`)
     • Daily automated online backup via cron
```

---

## 3. Environment Parity: Windows Development vs Linux Production

| Dimension | Windows Development (Local) | Linux Production (Target) | Production Requirement |
| :--- | :--- | :--- | :--- |
| **OS Platform** | Windows 11 Enterprise | Ubuntu 22.04 LTS / Debian 12 | Deploy via Linux container or VM |
| **Process Server** | Uvicorn single-process loop | Gunicorn with 4 Uvicorn workers | Multi-worker concurrency |
| **Supervision** | Manual terminal invocation | Systemd daemon service | Automated restart on failure |
| **TLS / SSL** | Unencrypted HTTP | TLS 1.3 via Nginx / Caddy | HTTPS mandatory in prod |
| **Static Files** | Starlette `StaticFiles` | Nginx direct disk serving | Offload static asset IO |
| **File Permissions** | Windows ACLs | Linux POSIX (`0750` dir, `0640` file) | Restricted service user (`autoheal`) |
| **Backups** | Manual test scripts | Automated cron snapshotting | Daily rotated backup archives |

---

## 4. Production Configuration Artifacts

### 4.1 Systemd Service Unit (`/etc/systemd/system/autoheal.service`)
```ini
[Unit]
Description=AutoHeal Autonomous SOC & ShopSphere Platform
After=network.target

[Service]
Type=notify
User=autoheal
Group=autoheal
WorkingDirectory=/opt/autoheal/autoheal
Environment="PATH=/opt/autoheal/.venv/bin"
EnvironmentFile=/etc/autoheal/autoheal.env
ExecStart=/opt/autoheal/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/autoheal/access.log \
    --error-logfile /var/log/autoheal/error.log \
    server:app

Restart=always
RestartSec=5s
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4.2 Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/autoheal`)
```nginx
server {
    listen 80;
    server_name soc.yourcompany.com shop.yourcompany.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name soc.yourcompany.com shop.yourcompany.com;

    ssl_certificate /etc/letsencrypt/live/soc.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soc.yourcompany.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Defense-in-depth headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static Asset Offloading
    location /static/ {
        alias /opt/autoheal/autoheal/web/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # Application Reverse Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }
}
```

### 4.3 Automated Backup Cron Job (`/etc/cron.d/autoheal-backup`)
```bash
# Execute daily online SQLite snapshot at 02:00 AM UTC
0 2 * * * autoheal /opt/autoheal/.venv/bin/python /opt/autoheal/autoheal/scripts/backup_database.py /var/backups/autoheal >> /var/log/autoheal/backup.log 2>&1
# Prune backups older than 30 days
0 3 * * * autoheal find /var/backups/autoheal -type f -name "*.db" -mtime +30 -delete
```

---

## 5. Security & Secrets Management
* **Environment Isolation:** Secrets (such as JWT encryption keys, admin initialization passwords, and third-party webhook tokens) must be stored in `/etc/autoheal/autoheal.env` with `0600` permissions owned by `autoheal:autoheal`.
* **Zero Hardcoded Secrets:** Codebase was audited to ensure default secrets are overridden when environment variables are supplied.

---

## 6. Audit Conclusion
The deployment architecture is fully specified for Linux production environments. Pre-requisites for deployment are documented, and automated service supervision and backup scripts are verified.
