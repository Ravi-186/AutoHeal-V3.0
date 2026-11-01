import os
from pathlib import Path

# Base Paths
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

DATA_DIR = Path(os.getenv("AUTOHEAL_DATA_DIR", PROJECT_ROOT / "data"))
MODELS_DIR = Path(os.getenv("AUTOHEAL_MODELS_DIR", PROJECT_ROOT / "models"))
WEB_DIR = PROJECT_ROOT / "web"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings
API_HOST = os.getenv("AUTOHEAL_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("AUTOHEAL_API_PORT", os.getenv("PORT", 8000)))
DASHBOARD_PORT = int(os.getenv("AUTOHEAL_DASHBOARD_PORT", 8501))

# AI & Detection Engine Configuration
DEFAULT_THRESHOLD = float(os.getenv("AUTOHEAL_DETECTION_THRESHOLD", 0.45))
MAX_ESCALATION_RETRIES = int(os.getenv("AUTOHEAL_MAX_RETRIES", 2))
DEFAULT_TRAFFIC_DURATION_MINS = int(os.getenv("AUTOHEAL_TRAFFIC_DURATION", 5))

# Security & CORS
ALLOWED_ORIGINS = os.getenv("AUTOHEAL_ALLOWED_ORIGINS", "*").split(",")
LOG_LEVEL = os.getenv("AUTOHEAL_LOG_LEVEL", "INFO")
