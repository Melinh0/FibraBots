from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)
REQUIRED_KEYWORDS = (
    "IP Blacklist Check",
    "IP Address Information",
    "IP Blocklist Report",
)


def is_valid(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="replace")
    return all(keyword in content for keyword in REQUIRED_KEYWORDS)


def validate(input_dir: Path, delete: bool = False) -> list[Path]:
    invalid: list[Path] = []
    for path in sorted(input_dir.glob("*.txt")):
        if not is_valid(path):
            invalid.append(path)
            if delete:
                path.unlink()
                LOGGER.warning("Removido: %s", path)
            else:
                LOGGER.warning("Inválido: %s", path)
    LOGGER.info(
        "%s arquivo(s) inválido(s)%s.",
        len(invalid),
        " removido(s)" if delete else " encontrado(s) (use --delete para remover)",
    )
    return invalid
