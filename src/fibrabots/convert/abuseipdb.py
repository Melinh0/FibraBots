from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent, load_json

LOGGER = logging.getLogger(__name__)
COLUMNS = [
    "ip",
    "abuseipdb_confidence_score",
    "abuseipdb_total_reports",
    "abuseipdb_num_distinct_users",
]


def convert(input_path: Path, output_path: Path) -> int:
    records = load_json(input_path, [])
    frame = pd.DataFrame(records)
    for column in COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame = frame[COLUMNS].drop_duplicates(subset=["ip"]).sort_values("ip")
    ensure_parent(output_path)
    frame.to_excel(output_path, index=False, engine="openpyxl")
    LOGGER.info("AbuseIPDB: %s registro(s) -> %s", len(frame), output_path)
    return len(frame)
