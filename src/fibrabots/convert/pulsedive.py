from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent

LOGGER = logging.getLogger(__name__)
RISK_TYPES = [
    "unknown_pulsedrive",
    "none_pulsedrive",
    "low_pulsedrive",
    "medium_pulsedrive",
    "high_pulsedrive",
    "critical_pulsedrive",
]
COLUMNS = ["ip", "risk_recommended_pulsedrive", "amount_risk_pulsedrive", *RISK_TYPES]


def parse_file(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    ip = payload.get("indicator")
    if not ip:
        return None
    factors = payload.get("riskfactors") or []
    counts = {risk: 0 for risk in RISK_TYPES}
    for factor in factors:
        risk = str(factor.get("risk", "unknown")).lower() + "_pulsedrive"
        if risk in counts:
            counts[risk] += 1
    row: dict[str, object] = {
        "ip": ip,
        "risk_recommended_pulsedrive": payload.get("risk_recommended", "N/A"),
        "amount_risk_pulsedrive": len(factors),
    }
    row.update(counts)
    return row


def convert(input_dir: Path, output_path: Path) -> int:
    rows: list[dict[str, object]] = []
    ignored = 0
    for path in sorted(input_dir.glob("*.json")):
        row = parse_file(path)
        if row is None:
            ignored += 1
            continue
        rows.append(row)

    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame = frame.drop_duplicates(subset=["ip"]).sort_values("ip")
    ensure_parent(output_path)
    frame.to_excel(output_path, index=False, engine="openpyxl")
    if ignored:
        LOGGER.warning("Pulsedive: %s arquivo(s) inválido(s) ignorado(s).", ignored)
    LOGGER.info("Pulsedive: %s registro(s) -> %s", len(frame), output_path)
    return len(frame)
