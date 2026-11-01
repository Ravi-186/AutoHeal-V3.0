# AutoHeal v3.0 — Environment Configuration Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Standard:** 12-Factor Application Configuration  
**Date:** November 1, 2026  

---

## 1. Environment Variable Catalog

AutoHeal loads configuration dynamically at startup using `pydantic-settings` and `python-dotenv`. Variables can be supplied via an `autoheal/.env` file or directly as operating system environment variables.

| Variable Name | Type | Default Value | Production Recommendation | Description |
|---|---|---|---|---|
| `ENVIRONMENT` | String | `development` | `production` | Controls stack trace masking and strict error redaction |
| `PORT` | Integer | `8000` | `8000` (Behind reverse proxy) | TCP port the Uvicorn/ASGI server listens on |
| `HOST` | String | `127.0.0.1` | `127.0.0.1` | IP interface to bind to (`127.0.0.1` ensures isolation) |
| `SECRET_KEY` | String | *Auto-generated* | `openssl rand -hex 32` | Cryptographic secret used for signing JWT tokens and session cookies |
| `DATABASE_PATH` | Path | `data/shopsphere.db`| `/var/lib/autoheal/shopsphere.db` | Absolute or relative filesystem path to primary SQLite database |
| `RATE_LIMIT_BURST` | Integer | `15` | `15` | Maximum allowed requests per IP in sliding window before throttle |
| `RATE_LIMIT_WINDOW`| Float | `8.0` | `8.0` | Duration of the sliding rate-limiting window in seconds |
| `GEMINI_API_KEY` | String | `None` | Enterprise Google Cloud API Key | Enables live Google Gemini LLM synthesis in AI SOC Copilot |
| `OPENAI_API_KEY` | String | `None` | Enterprise OpenAI API Key | Alternative live LLM backend provider for AI SOC Copilot |
| `ALLOWLISTED_TARGETS`| String | `http://localhost:8000,http://127.0.0.1:8000` | Same | Comma-delimited list of targets permitted for attack simulations and probes |
| `LOG_LEVEL` | String | `INFO` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 2. Production `.env.example` Reference Template

```ini
# ==============================================================================
# AutoHeal v3.0 Production Environment Configuration Template
# ==============================================================================

# Application Environment (development, staging, production)
ENVIRONMENT=production

# Network Binding
HOST=127.0.0.1
PORT=8000

# Cryptographic Token Signing Secret (GENERATE IN PRODUCTION!)
SECRET_KEY=b94a8d38102f4a7c8e9b1d5c2e8a7f9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f

# Relational Persistence
DATABASE_PATH=data/shopsphere.db

# Autonomous AppSec Rate Limiting Invariants
RATE_LIMIT_BURST=15
RATE_LIMIT_WINDOW=8.0

# AI SOC Copilot Provider Configuration (Optional)
# If omitted, Copilot operates in 100% Deterministic Grounded Offline Mode
GEMINI_API_KEY=
OPENAI_API_KEY=

# Attack Simulation Target Allowlist (Prevents SSRF and unauthorized testing)
ALLOWLISTED_TARGETS=http://localhost:8000,http://127.0.0.1:8000

# Logging Verbosity
LOG_LEVEL=INFO
```

---

## 3. Secret Management & Key Rotation

1. **Zero Secret Storage in Version Control:** The `.env` file is explicitly ignored in `.gitignore`. Only `.env.example` is tracked.
2. **Key Rotation Runbook:**
   - Generate a new 256-bit hexadecimal key: `openssl rand -hex 32`.
   - Update `SECRET_KEY` in `.env`.
   - Perform graceful restart: `sudo systemctl restart autoheal`.
   - *Note: Rotating `SECRET_KEY` invalidates existing customer session tokens, prompting shoppers to log in again.*

---

## 4. Configuration Sign-Off

The configuration architecture ensures full isolation of operational credentials, zero hardcoded secrets, and seamless portability across development, staging, and production.
