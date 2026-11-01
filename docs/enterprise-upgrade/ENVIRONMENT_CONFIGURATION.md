# AutoHeal & ShopSphere: Environment Configuration Specification

**Author:** DevSecOps Lead  
**Document Ref:** `ENV-CONF-001`  
**Date:** 2026-11-01  

---

## 1. Environment Variables Reference

| Variable Name | Default Value | Description | Production Guidance |
|---|---|---|---|
| `API_HOST` | `0.0.0.0` | Bind IP for FastAPI core server | Use `0.0.0.0` inside containers, `127.0.0.1` behind reverse proxy |
| `API_PORT` | `8000` | Port for REST API and ShopSphere storefront | Standard internal HTTP port |
| `LOG_LEVEL` | `INFO` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | Set to `INFO` for production; `DEBUG` during auditing |
| `ALLOWED_ORIGINS` | `*` | CORS origins allowlist | In production, restrict to specific corporate domain origins |
| `ENVIRONMENT` | `production` | Deployment environment (`development`, `staging`, `production`) | Enforces strict authentication policies |
| `SHOPSPHERE_SECRET_KEY` | *(Generated)* | HMAC secret for session verification | Set via secrets manager; min 32 characters |
| `DB_PATH` | `autoheal/data/shopsphere.db` | Path to persistent SQLite database | Ensure path is on persistent, backed-up SSD volume |

---

## 2. Sample `.env.production` Configuration

```ini
# AutoHeal Core Environment Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
ALLOWED_ORIGINS=https://soc.enterprise.internal,https://shop.enterprise.internal

# Data Directories
DB_PATH=/var/lib/autoheal/shopsphere.db
DATA_DIR=/var/lib/autoheal/data

# Security & Secrets
SHOPSPHERE_SECRET_KEY=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
TARGET_SAFETY_ALLOWLIST=http://localhost:8000,http://127.0.0.1:8000,http://testserver
```
