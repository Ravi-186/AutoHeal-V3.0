# AutoHeal v3.0 — Enterprise Installation & Setup Guide
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Target OS:** Windows 10/11, Ubuntu 22.04 LTS, Debian 12, macOS 14+  
**Date:** November 1, 2026  

---

## 1. System Requirements

### Hardware Prerequisites
- **Processor:** 64-bit AMD64 / ARM64 dual-core processor (4 vCPUs recommended for high-volume stress).
- **RAM:** Minimum 4 GB available memory (8 GB recommended for concurrent 3D WebGL and ML inference).
- **Storage:** 1.5 GB free disk space (includes SQLite database, telemetry CSVs, and ML models).
- **Network:** Port 8000 available for TCP ingress.

### Software Prerequisites
- **Python:** Python 3.13.0 or higher (AMD64 standard distribution).
- **Git:** Git 2.40+ (for source code retrieval and branch tracking).
- **Web Browser:** Modern browser with WebGL 2.0 and CSS Grid support (Chrome 120+, Edge 120+, Firefox 120+, Safari 17+).

---

## 2. Installation Procedure (Windows PowerShell)

### Step 1: Navigate to Workspace Root
```powershell
cd C:\Users\bobba\Documents\AD
```

### Step 2: Establish Isolated Virtual Environment
Create a clean Python 3.13 virtual environment if not already present:
```powershell
python -m venv .venv
```

### Step 3: Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*Note: If PowerShell execution policy restricts scripts, execute: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` prior to activation.*

### Step 4: Install Pinned Dependencies
Install the certified production dependencies from `autoheal/requirements.txt`:
```powershell
pip install --upgrade pip
pip install -r autoheal\requirements.txt
```

---

## 3. Installation Procedure (Linux / Ubuntu 22.04 LTS)

### Step 1: Install System Prerequisites
```bash
sudo apt update && sudo apt install -y python3.13 python3.13-venv python3.13-dev sqlite3 git build-essential
```

### Step 2: Navigate and Create Virtual Environment
```bash
cd /opt/autoheal  # Or your chosen deployment path
python3.13 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r autoheal/requirements.txt
```

---

## 4. Environment Configuration

Copy the reference environment template and configure secrets:
```bash
# On Windows
copy autoheal\.env.example autoheal\.env

# On Linux
cp autoheal/.env.example autoheal/.env
```

Ensure `.env` contains:
```ini
ENVIRONMENT=production
PORT=8000
HOST=127.0.0.1
SECRET_KEY=generate-a-secure-random-32-char-key-here
DATABASE_PATH=data/shopsphere.db
RATE_LIMIT_BURST=15
RATE_LIMIT_WINDOW=8.0
```

---

## 5. Automated Database Initialization

The database engine in `shopsphere/database.py` automatically initializes and seeds required tables upon initial server launch:
- 30 relational tables created with strict foreign key constraints.
- Default product catalog (29 items across 8 categories) seeded.
- Default customer and admin accounts seeded (`rahul.shopper@example.com`, `admin@shopsphere.com`).
- 5 enterprise SOAR playbooks seeded.
- SQLite WAL mode activated (`PRAGMA journal_mode = WAL;`).

---

## 6. Post-Installation Verification Check

Run the Phase 10 certification test suite to confirm installation integrity:
```powershell
cd autoheal
pytest tests/test_phase10_release_certification.py -v
```

**Expected Result:**
```
======================= 13 passed, 1 warning in ~86s =======================
```

---

## 7. Installation Sign-Off

The environment is now fully installed, validated, and ready for service execution.
