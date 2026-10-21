from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from fibrabots.utils import ensure_parent

LOGGER = logging.getLogger(__name__)


def convert(input_dir: Path, output_path: Path) -> int:
    excluded = {output_path.name, "Total.xlsx"}
    files = sorted(
        path
        for path in input_dir.glob("*.xlsx")
        if path.name not in excluded and not path.name.startswith("~$")
    )
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo Excel encontrado em {input_dir}")

    merged = pd.DataFrame()
    used: list[str] = []
    for path in files:
        frame = pd.read_excel(path, engine="openpyxl")
        if "ip" not in frame.columns:
            LOGGER.warning("Ignorando %s: coluna 'ip' não encontrada.", path.name)
            continue
        frame = frame.drop_duplicates(subset=["ip"])
        merged = frame if merged.empty else merged.merge(frame, on="ip", how="outer")
        used.append(path.name)

    if merged.empty:
        raise ValueError("Nenhuma planilha válida para consolidar.")
    merged = merged.dropna(how="any").sort_values("ip")
    ensure_parent(output_path)
    merged.to_excel(output_path, index=False, engine="openpyxl")
    LOGGER.info(
        "Dataset consolidado (%s fontes): %s linhas -> %s",
        len(used),
        len(merged),
        output_path,
    )
    return len(merged)
