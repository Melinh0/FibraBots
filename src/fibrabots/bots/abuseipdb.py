from __future__ import annotations

import itertools
import logging
import time
from pathlib import Path

import requests

from fibrabots.utils import load_json, merge_records, read_ips, save_json

LOGGER = logging.getLogger(__name__)
API_URL = "https://api.abuseipdb.com/api/v2/check"


class AbuseIPDBBot:
    def __init__(
        self,
        api_keys: list[str],
        output: Path,
        max_age_days: int = 90,
        timeout: float = 30,
        delay: float = 0,
        batch_size: int = 100,
        force: bool = False,
    ) -> None:
        if not api_keys:
            raise ValueError("Defina ABUSEIPDB_API_KEYS no .env ou no ambiente.")
        self.api_keys = api_keys
        self.output = output
        self.max_age_days = max_age_days
        self.timeout = timeout
        self.delay = delay
        self.batch_size = batch_size
        self.force = force
        self.session = requests.Session()
        self._keys = itertools.cycle(api_keys)

    def fetch(self, ip: str) -> dict[str, object] | None:
        for attempt in range(len(self.api_keys)):
            key = next(self._keys)
            headers = {"Key": key, "Accept": "application/json"}
            params = {"ipAddress": ip, "maxAgeInDays": self.max_age_days}
            try:
                response = self.session.get(
                    API_URL, headers=headers, params=params, timeout=self.timeout
                )
                if response.status_code == 429:
                    wait = min(2**attempt, 30)
                    LOGGER.warning("Limite da chave atingido para %s; aguardando %ss", ip, wait)
                    time.sleep(wait)
                    continue
                if response.status_code == 404:
                    LOGGER.warning("IP %s não encontrado no AbuseIPDB.", ip)
                    return None
                response.raise_for_status()
                payload = response.json()["data"]
                return {
                    "ip": ip,
                    "abuseipdb_confidence_score": payload["abuseConfidenceScore"],
                    "abuseipdb_total_reports": payload["totalReports"],
                    "abuseipdb_num_distinct_users": payload["numDistinctUsers"],
                }
            except requests.RequestException as exc:
                LOGGER.warning("Falha ao consultar %s: %s", ip, exc)
        LOGGER.error("Todas as chaves falharam para o IP %s", ip)
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

        LOGGER.info("Processando %s IP(s) com %s chave(s).", len(pending), len(self.api_keys))
        batch: list[dict[str, object]] = []
        processed = 0
        for index, ip in enumerate(pending, start=1):
            record = self.fetch(ip)
            if record:
                batch.append(record)
                processed += 1
            if index % self.batch_size == 0:
                existing = merge_records(existing, batch)
                save_json(self.output, existing)
                batch.clear()
                LOGGER.info("Progresso: %s/%s", index, len(pending))
            if self.delay:
                time.sleep(self.delay)

        if batch:
            existing = merge_records(existing, batch)
            save_json(self.output, existing)
        LOGGER.info("Concluído: %s registro(s) em %s", processed, self.output)
        return processed
