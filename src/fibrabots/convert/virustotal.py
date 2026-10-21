from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent, load_json

LOGGER = logging.getLogger(__name__)
STATS = ["malicious", "suspicious", "undetected", "harmless"]
COLUMNS = ["ip", "virustotal_reputation", *STATS]


def convert(input_path: Path, output_path: Path) -> int:
    records = load_json(input_path, [])
    rows: list[dict[str, object]] = []
    for record in records:
        stats = dict(record.get("virustotal_last_analysis_stats") or {})
        stats.pop("timeout", None)
        row = {
            "ip": record.get("ip"),
            "virustotal_reputation": record.get("virustotal_reputation"),
        }
        row.update({key: stats.get(key) for key in STATS})
        rows.append(row)

    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame = frame.drop_duplicates(subset=["ip"]).sort_values("ip")
    ensure_parent(output_path)
    frame.to_excel(output_path, index=False, engine="openpyxl")
    LOGGER.info("VirusTotal: %s registro(s) -> %s", len(frame), output_path)
    return len(frame)
