from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent

LOGGER = logging.getLogger(__name__)


def convert(input_path: Path, output_path: Path) -> int:
    frame = pd.read_excel(input_path, engine="openpyxl")
    ensure_parent(output_path)
    frame.to_csv(output_path, index=False, encoding="utf-8")
    LOGGER.info("%s linhas -> %s", len(frame), output_path)
    return len(frame)
