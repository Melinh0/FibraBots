from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_ARGS = ("--no-first-run", "--no-default-browser-check")


class BrowserError(RuntimeError):
    pass


class BrowserSession:
    def __init__(
        self,
        playwright: Playwright,
        browser: Browser,
        context: BrowserContext,
        page: Page,
        timeout: float,
        owns_browser: bool,
    ) -> None:
        self._playwright = playwright
        self.browser = browser
        self.context = context
        self.page = page
        self.timeout = timeout
        self._owns_browser = owns_browser

    def navigate(self, url: str) -> None:
        try:
            self.page.goto(url, wait_until="load", timeout=self.timeout * 1000)
        except PlaywrightTimeoutError as exc:
            raise BrowserError(f"Timeout ao carregar {url}") from exc
        except PlaywrightError as exc:
            raise BrowserError(f"Falha ao carregar {url}: {exc}") from exc

    def wait_ready(self, timeout: float | None = None) -> None:
        try:
            self.page.wait_for_load_state("load", timeout=(timeout or self.timeout) * 1000)
        except PlaywrightTimeoutError as exc:
            raise BrowserError("Timeout aguardando a página terminar de carregar.") from exc

    def wait_for(self, expression: str, timeout: float = 60, interval: float = 0.5) -> Any:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                result = self.evaluate(expression)
                if result:
                    return result
            except BrowserError as exc:
                last_error = exc
            time.sleep(interval)
        message = f"Timeout aguardando condição: {expression}"
        if last_error:
            message += f" ({last_error})"
        raise BrowserError(message)

    def evaluate(self, expression: str) -> Any:
        try:
            return self.page.evaluate(expression)
        except PlaywrightError as exc:
            raise BrowserError(f"Erro JavaScript: {exc}") from exc

    def body_text(self) -> str:
        try:
            return self.page.inner_text("body")
        except PlaywrightError as exc:
            raise BrowserError(f"Não foi possível ler o conteúdo da página: {exc}") from exc

    def current_url(self) -> str:
        return self.page.url

    def close(self) -> None:
        closers: list[Any] = [self.context.close]
        if self._owns_browser:
            closers.append(self.browser.close)
        closers.append(self._playwright.stop)
        for closer in closers:
            try:
                closer()
            except Exception:
                LOGGER.debug("Falha ao finalizar recurso do navegador.", exc_info=True)


def cdp_base_url(cdp_url: str) -> str:
    cleaned = cdp_url.strip().rstrip("/")
    return cleaned[: -len("/json")] if cleaned.endswith("/json") else cleaned


def launch_session(
    cdp_url: str | None = None,
    headless: bool = False,
    timeout: float = 30,
) -> BrowserSession:
    playwright = sync_playwright().start()
    owns_browser = False
    try:
        if cdp_url:
            LOGGER.info("Conectando ao Chrome existente em %s", cdp_url)
            browser = playwright.chromium.connect_over_cdp(cdp_base_url(cdp_url))
            context = browser.new_context()
        else:
            browser = playwright.chromium.launch(headless=headless, args=list(DEFAULT_ARGS))
            owns_browser = True
            context = browser.new_context(viewport=None, locale="pt-BR")
        page = context.new_page()
        page.set_default_timeout(timeout * 1000)
        page.set_default_navigation_timeout(timeout * 1000)
    except PlaywrightError as exc:
        try:
            playwright.stop()
        except Exception:
            LOGGER.debug("Falha ao finalizar o Playwright.", exc_info=True)
        alvo = cdp_url or "Chromium do Playwright"
        raise BrowserError(f"Não foi possível iniciar o navegador ({alvo}): {exc}") from exc
    return BrowserSession(playwright, browser, context, page, timeout, owns_browser)
