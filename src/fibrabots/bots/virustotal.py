from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from fibrabots.utils import load_json, merge_records, read_ips, save_json

LOGGER = logging.getLogger(__name__)
API_URL = "https://www.virustotal.com/api/v3/ip_addresses/"


class VirusTotalBot:
    def __init__(
        self,
        api_key: str | None,
        output: Path,
        timeout: float = 30,
        delay: float = 0,
        force: bool = False,
    ) -> None:
        if not api_key:
            raise ValueError("Defina VIRUSTOTAL_API_KEY no .env ou no ambiente.")
        self.api_key = api_key
        self.output = output
        self.timeout = timeout
        self.delay = delay
        self.force = force
        self.session = requests.Session()
        self.session.headers.update({"x-apikey": api_key})

    def fetch(self, ip: str, retries: int = 3) -> dict[str, object] | None:
        for attempt in range(retries):
            try:
                response = self.session.get(f"{API_URL}{ip}", timeout=self.timeout)
                if response.status_code == 429:
                    wait = min(60 * (attempt + 1), 300)
                    LOGGER.warning("Limite do VirusTotal atingido; aguardando %ss", wait)
                    time.sleep(wait)
                    continue
                if response.status_code == 404:
                    LOGGER.warning("IP %s não encontrado no VirusTotal.", ip)
                    return None
                response.raise_for_status()
                attributes = response.json()["data"]["attributes"]
                return {
                    "ip": ip,
                    "virustotal_reputation": attributes["reputation"],
                    "virustotal_last_analysis_stats": attributes["last_analysis_stats"],
                }
            except requests.RequestException as exc:
                LOGGER.warning("Falha ao consultar %s: %s", ip, exc)
                time.sleep(min(2**attempt, 30))
        LOGGER.error("Não foi possível coletar dados do IP %s", ip)
        return None

    def run(self, input_path: Path, limit: int | None = None) -> int:
        ips = read_ips(input_path)
        existing = load_json(self.output, [])
        existing_ips = {str(item.get("ip")) for item in existing if item.get("ip")}
        pending = [ip for ip in ips if self.force or ip not in existing_ips]
        if limit is not None:
            pending = pending[:limit]

        if not pending:
            LOGGER.info("Nenhum IP novo para processar.")
            return 0

        LOGGER.info("Processando %s IP(s).", len(pending))
        processed = 0
        for index, ip in enumerate(pending, start=1):
            record = self.fetch(ip)
            if record:
                existing = merge_records(existing, [record])
                save_json(self.output, existing)
                processed += 1
            LOGGER.info("[%s/%s] %s", index, len(pending), ip)
            if self.delay:
                time.sleep(self.delay)
        LOGGER.info("Concluído: %s registro(s) em %s", processed, self.output)
        return processed
