"""
Configurações do Meta Ads Automation
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretório base
BASE_DIR = Path(__file__).resolve().parent.parent

# === META ADS ===
META_CONFIG = {
    "app_id": os.getenv("META_APP_ID"),
    "app_secret": os.getenv("META_APP_SECRET"),
    "access_token": os.getenv("META_ACCESS_TOKEN"),
    "ad_account_id": os.getenv("META_AD_ACCOUNT_ID"),
    "page_id": os.getenv("FACEBOOK_PAGE_ID"),
    "instagram_id": os.getenv("INSTAGRAM_ACCOUNT_ID"),
}

# === OLLAMA ===
OLLAMA_CONFIG = {
    "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
    "timeout": 120,
}

# === CAMINHOS ===
PATHS = {
    "criativos": Path(os.getenv("CRIATIVOS_PATH", BASE_DIR / "criativos")),
    "logs": Path(os.getenv("LOGS_PATH", BASE_DIR / "logs")),
}

# === OTIMIZAÇÃO ===
OPTIMIZATION = {
    "max_cpa": int(os.getenv("MAX_CPA", 5000)),  # centavos
    "min_roas": float(os.getenv("MIN_ROAS", 1.5)),
    "default_daily_budget": int(os.getenv("DEFAULT_DAILY_BUDGET", 5000)),  # centavos
}

# === EXTENSÕES SUPORTADAS ===
SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".gif"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".avi"}

# === PÚBLICOS PADRÃO ===
DEFAULT_TARGETING = {
    "geo_locations": {
        "countries": ["BR"],
    },
    "age_min": 18,
    "age_max": 65,
    "publisher_platforms": ["facebook", "instagram"],
    "facebook_positions": ["feed", "story", "reels"],
    "instagram_positions": ["stream", "story", "reels"],
}


def validate_config():
    """Valida se todas as configurações obrigatórias estão presentes."""
    required = ["app_id", "app_secret", "access_token", "ad_account_id", "page_id"]
    missing = [key for key in required if not META_CONFIG.get(key)]

    if missing:
        raise ValueError(f"Configurações faltando no .env: {', '.join(missing)}")

    return True
