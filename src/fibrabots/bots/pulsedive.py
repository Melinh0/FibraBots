from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from fibrabots.utils import ip_to_filename, read_ips, save_json

LOGGER = logging.getLogger(__name__)
API_URL = "https://pulsedive.com/api/"


class PulsediveBot:
    def __init__(
        self,
        output_dir: Path,
        api_key: str | None = None,
        timeout: float = 30,
        delay: float = 1.2,
        force: bool = False,
        retries: int = 3,
    ) -> None:
        self.output_dir = output_dir
        self.api_key = api_key
        self.timeout = timeout
        self.delay = delay
        self.force = force
        self.retries = retries
        self.quota_exhausted = False
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _params(self, ip: str) -> dict[str, str]:
        params = {"pretty": "true", "indicator": ip}
        if self.api_key:
            params["key"] = self.api_key
        return params

    def _track_quota(self, response: requests.Response) -> bool:
        remaining = response.headers.get("X-Requests-Remaining-Day")
        if remaining is None:
            return True
        try:
            saldo = int(remaining)
        except ValueError:
            return True
        if saldo <= 0:
            self.quota_exhausted = True
            LOGGER.warning(
                "Cota diária do Pulsedive esgotada (%s requisição(ões) restante(s) no mês). "
                "Use uma chave de conta gratuita em PULSEDIVE_API_KEY ou aguarde a virada do dia.",
                response.headers.get("X-Requests-Remaining-Month", "?"),
            )
            return False
        return True

    def fetch(self, ip: str) -> dict[str, object] | None:
        for attempt in range(self.retries):
            try:
                response = self.session.get(API_URL, params=self._params(ip), timeout=self.timeout)
            except requests.RequestException as exc:
                LOGGER.warning("Falha ao consultar %s: %s", ip, exc)
                time.sleep(min(2**attempt, 10))
                continue

            if response.status_code == 404:
                LOGGER.warning("IP %s não encontrado no Pulsedive.", ip)
                return None
            if response.status_code == 429:
                self._track_quota(response)
                if self.quota_exhausted:
                    return None
                wait = min(2**attempt + 1, 15)
                LOGGER.warning("Limite do Pulsedive atingido; aguardando %ss", wait)
                time.sleep(wait)
                continue
            if not self._track_quota(response):
                return None
            try:
                response.raise_for_status()
                payload = response.json()
            except ValueError as exc:
                LOGGER.warning("Resposta inválida do Pulsedive para %s: %s", ip, exc)
                return None

            indicator = str(payload.get("indicator") or "")
            if indicator.lower() != ip.lower():
                LOGGER.error(
                    "Indicador retornado (%s) difere do IP solicitado (%s); ignorado.",
                    indicator,
                    ip,
                )
                return None
            return payload
        LOGGER.error("Não foi possível coletar dados do IP %s", ip)
        return None

    def run(self, input_path: Path, limit: int | None = None) -> int:
        ips = read_ips(input_path)
        pending = [
            ip
            for ip in ips
            if self.force or not (self.output_dir / ip_to_filename(ip, ".json")).exists()
        ]
        if limit is not None:
            pending = pending[:limit]
        if not pending:
            LOGGER.info("Nenhum IP novo para processar.")
            return 0

        LOGGER.info(
            "Processando %s IP(s)%s.",
            len(pending),
            " com chave da API" if self.api_key else " sem chave (cota limitada)",
        )
        processed = 0
        for index, ip in enumerate(pending, start=1):
            payload = self.fetch(ip)
            if payload:
                path = self.output_dir / ip_to_filename(ip, ".json")
                save_json(path, payload)
                processed += 1
            LOGGER.info("[%s/%s] %s", index, len(pending), ip)
            if self.quota_exhausted:
                LOGGER.warning("Execução interrompida após %s de %s IP(s).", index, len(pending))
                break
            if self.delay:
                time.sleep(self.delay)
        LOGGER.info("Concluído: %s indicador(es) em %s", processed, self.output_dir)
        return processed
