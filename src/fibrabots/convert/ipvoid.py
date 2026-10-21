from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent

LOGGER = logging.getLogger(__name__)
IP_PATTERN = re.compile(r"^IP Address\s+(?!Information\b)(\S+)", re.MULTILINE)
DETECTION_PATTERN = re.compile(r"^Detections Count\s+(\d+)(?:/(\d+))?", re.MULTILINE)


def parse_file(path: Path) -> dict[str, object] | None:
    content = path.read_text(encoding="utf-8", errors="replace")
    ip_match = IP_PATTERN.search(content)
    detection_match = DETECTION_PATTERN.search(content)
    if not ip_match:
        return None
    detection = int(detection_match.group(1)) if detection_match else None
    total = int(detection_match.group(2)) if detection_match and detection_match.group(2) else None
    return {
        "ip": ip_match.group(1),
        "Detection Count": detection,
        "Total Detection Count": total,
    }


def convert(input_dir: Path, output_path: Path) -> int:
    rows: list[dict[str, object]] = []
    ignored: list[Path] = []
    for path in sorted(input_dir.glob("*.txt")):
        row = parse_file(path)
        if row is None or row["Detection Count"] is None:
            ignored.append(path)
            continue
        rows.append(row)

    frame = pd.DataFrame(rows, columns=["ip", "Detection Count", "Total Detection Count"])
    frame = frame.drop_duplicates(subset=["ip"]).sort_values("ip")
    ensure_parent(output_path)
    frame.to_excel(output_path, index=False, engine="openpyxl")
    if ignored:
        LOGGER.warning("IPVoid: %s arquivo(s) inválido(s) ignorado(s).", len(ignored))
    LOGGER.info("IPVoid: %s registro(s) -> %s", len(frame), output_path)
    return len(frame)
