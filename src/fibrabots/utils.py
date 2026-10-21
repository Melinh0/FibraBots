from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_ips(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def ip_to_filename(ip: str, suffix: str) -> str:
    normalized = ip.strip().replace(":", "_").replace(".", "_")
    return f"{normalized}{suffix}"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    fd, temporary = tempfile.mkstemp(
        prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent), text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise


def merge_records(
    existing: Iterable[dict[str, Any]], new: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in existing:
        ip = record.get("ip")
        if ip:
            merged[str(ip)] = record
    for record in new:
        ip = record.get("ip")
        if ip:
            merged[str(ip)] = record
    return list(merged.values())


def dataset_paths(processed_dir: Path) -> dict[str, Path]:
    return {
        "abuseipdb": processed_dir / "ABUSEIPDB.xlsx",
        "virustotal": processed_dir / "VIRUSTOTAL.xlsx",
        "ipvoid": processed_dir / "IPVOID.xlsx",
        "pulsedive": processed_dir / "PULSEDIVE.xlsx",
        "total_xlsx": processed_dir / "Total.xlsx",
        "total_csv": processed_dir / "Total.csv",
    }
