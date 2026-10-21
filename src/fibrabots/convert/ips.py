from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent

LOGGER = logging.getLogger(__name__)


def extract_from_json(input_path: Path, output_path: Path) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    ips: list[str] = []
    for item in payload:
        if isinstance(item, dict):
            value = item.get("ip") or item.get("ip_address")
        else:
            value = item
        if value:
            ips.append(str(value).strip())
    return _write_unique(ips, output_path)


def extract_from_csv(input_path: Path, output_path: Path, column: str = "IP") -> int:
    frame = pd.read_csv(input_path)
    target = next((name for name in frame.columns if name.lower() == column.lower()), None)
    if target is None:
        raise ValueError(f"Coluna '{column}' não encontrada em {input_path}")
    ips = [str(value).strip() for value in frame[target].dropna().unique()]
    return _write_unique(ips, output_path)


def make_ips(prefix: str, output_path: Path, start: int = 0, end: int = 255) -> int:
    if not prefix.endswith("."):
        prefix += "."
    ips = [f"{prefix}{index}" for index in range(start, end + 1)]
    return _write_unique(ips, output_path)


def _write_unique(ips: list[str], output_path: Path) -> int:
    unique = list(dict.fromkeys(ip for ip in ips if ip))
    ensure_parent(output_path)
    output_path.write_text("\n".join(unique) + "\n", encoding="utf-8")
    LOGGER.info("%s IP(s) -> %s", len(unique), output_path)
    return len(unique)
