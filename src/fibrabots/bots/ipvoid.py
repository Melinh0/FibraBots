from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from fibrabots.bots.browser import BrowserError, BrowserSession, launch_session
from fibrabots.utils import ip_to_filename, read_ips

LOGGER = logging.getLogger(__name__)
IPVOID_URL = "https://www.ipvoid.com/ip-blacklist-check/"


def _set_ip_expression(ip: str) -> str:
    return f"""
        (() => {{
            const input = document.querySelector("#ipAddr");
            if (!input) return false;
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, "value"
            ).set;
            setter.call(input, {json.dumps(ip)});
            input.dispatchEvent(new Event("input", {{ bubbles: true }}));
            input.dispatchEvent(new Event("change", {{ bubbles: true }}));
            return true;
        }})();
    """


def _submit_expression() -> str:
    return """
        (() => {
            const form = document.querySelector("form");
            if (!form) return false;
            form.submit();
            return true;
        })();
    """


class IPVoidBot:
    def __init__(
        self,
        output_dir: Path,
        timeout: float = 120,
        pause: float = 5,
        manual_captcha: bool = False,
        captcha_wait: float = 60,
        force: bool = False,
        headless: bool = False,
        cdp_url: str | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.timeout = timeout
        self.pause = pause
        self.manual_captcha = manual_captcha
        self.captcha_wait = captcha_wait
        self.force = force
        self.headless = headless
        self.cdp_url = cdp_url
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_one(self, session: BrowserSession, ip: str) -> bool:
        session.navigate(IPVOID_URL)
        session.wait_ready(timeout=self.timeout)
        session.wait_for("!!document.querySelector('#ipAddr')", timeout=self.timeout)

        if not session.evaluate(_set_ip_expression(ip)):
            raise BrowserError("Campo #ipAddr não encontrado.")
        if not session.evaluate(_submit_expression()):
            raise BrowserError("Formulário do IPVoid não encontrado.")

        condition = "document.body && document.body.innerText.includes('Detections Count')"
        try:
            session.wait_for(condition, timeout=self.timeout)
        except BrowserError:
            if not self.manual_captcha:
                raise
            LOGGER.warning(
                "Resultado não carregou. Resolva o captcha no Chrome e aguarde %ss.",
                self.captcha_wait,
            )
            time.sleep(self.captcha_wait)
            session.wait_for(condition, timeout=self.timeout)

        content = session.body_text()
        if "Detections Count" not in content or "IP Address" not in content:
            LOGGER.error("Conteúdo inválido recebido para %s; arquivo não salvo.", ip)
            return False

        path = self.output_dir / ip_to_filename(ip, ".txt")
        path.write_text(content, encoding="utf-8")
        LOGGER.info("Relatório salvo em %s", path)
        return True

    def run(self, input_path: Path, limit: int | None = None) -> int:
        ips = read_ips(input_path)
        pending = [
            ip
            for ip in ips
            if self.force or not (self.output_dir / ip_to_filename(ip, ".txt")).exists()
        ]
        if limit is not None:
            pending = pending[:limit]
        if not pending:
            LOGGER.info("Nenhum IP novo para processar.")
            return 0

        session = launch_session(cdp_url=self.cdp_url, headless=self.headless, timeout=self.timeout)
        processed = 0
        try:
            for index, ip in enumerate(pending, start=1):
                LOGGER.info("[%s/%s] Processando %s", index, len(pending), ip)
                try:
                    if self.run_one(session, ip):
                        processed += 1
                except BrowserError as exc:
                    LOGGER.error("Falha ao processar %s: %s", ip, exc)
                time.sleep(self.pause)
        finally:
            session.close()
        LOGGER.info("Concluído: %s relatório(s) em %s", processed, self.output_dir)
        return processed
