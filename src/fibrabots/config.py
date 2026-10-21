from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = (
    Path(os.getenv("FIBRABOTS_HOME", Path(__file__).resolve().parents[2])).expanduser().resolve()
)

load_dotenv(PROJECT_ROOT / ".env", override=False)


def _resolve_path(env_name: str, default: str) -> Path:
    raw = os.getenv(env_name)
    if not raw:
        return (PROJECT_ROOT / default).resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


DATA_DIR = _resolve_path("FIBRABOTS_DATA_DIR", "data")
INPUT_DIR = _resolve_path("FIBRABOTS_INPUT_DIR", "data/input")
RAW_DIR = _resolve_path("FIBRABOTS_RAW_DIR", "data/raw")
PROCESSED_DIR = _resolve_path("FIBRABOTS_PROCESSED_DIR", "data/processed")

ABUSEIPDB_DIR = RAW_DIR / "abuseipdb"
VIRUSTOTAL_DIR = RAW_DIR / "virustotal"
IPVOID_DIR = RAW_DIR / "ipvoid"
PULSEDIVE_DIR = RAW_DIR / "pulsedive"

DEFAULT_INPUT = INPUT_DIR / "ips.txt"
ABUSEIPDB_OUTPUT = ABUSEIPDB_DIR / "results.json"
VIRUSTOTAL_OUTPUT = VIRUSTOTAL_DIR / "results.json"


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DEBUG_URL = os.getenv("CHROME_DEBUG_URL")
REQUEST_TIMEOUT = float(os.getenv("FIBRABOTS_REQUEST_TIMEOUT", "30"))
REQUEST_DELAY = float(os.getenv("FIBRABOTS_REQUEST_DELAY", "0"))
BROWSER_TIMEOUT = float(os.getenv("FIBRABOTS_BROWSER_TIMEOUT", "120"))
BROWSER_PAUSE = float(os.getenv("FIBRABOTS_BROWSER_PAUSE", "5"))
BROWSER_HEADLESS = _flag("FIBRABOTS_HEADLESS")
PULSEDIVE_DELAY = float(os.getenv("FIBRABOTS_PULSEDIVE_DELAY", "1.2"))


def _list_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    values: list[str] = []
    for item in raw.replace("\n", ",").split(","):
        item = item.strip()
        if item:
            values.append(item)
    return values


def abuseipdb_keys() -> list[str]:
    return _list_env("ABUSEIPDB_API_KEYS")


def virustotal_key() -> str | None:
    return os.getenv("VIRUSTOTAL_API_KEY") or None


def pulsedive_key() -> str | None:
    return os.getenv("PULSEDIVE_API_KEY") or None


def cdp_url() -> str | None:
    return DEBUG_URL or None
