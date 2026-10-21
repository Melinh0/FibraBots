# Configuração do navegador

Somente o bot `ipvoid` usa navegador. Ele é gerenciado pelo Playwright: na primeira
execução o Chromium é baixado automaticamente, sem Selenium, chromedriver ou Chrome
instalado.

```bash
uv run playwright install chromium   # opcional; o bot instala sozinho se faltar
uv run fibrabots ipvoid --limit 5
```

## Janela visível e headless

Por padrão a janela do navegador fica visível, o que permite observar a coleta e
resolver captcha manualmente. Em servidor ou CI use `--headless` (ou `FIBRABOTS_HEADLESS=1`):

```bash
uv run fibrabots ipvoid --headless
uv run fibrabots ipvoid --no-headless   # força a janela visível
```

O Pulsedive detecta navegador automatizado em modo headless e exige conta; por isso
o bot `pulsedive` usa a API pública e não o navegador.

## Captcha

O IPVoid pode exibir reCAPTCHA. Execute com `--manual-captcha` e resolva o desafio na
janela do navegador; o bot aguarda `--captcha-wait` segundos (padrão 60) antes de
tentar novamente.

```bash
uv run fibrabots ipvoid --manual-captcha --captcha-wait 90
```

## Chrome próprio (opcional)

Para usar um Chrome já em execução — com suas extensões de captcha e sua sessão —
inicie-o com depuração remota e aponte o bot:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

```bash
uv run fibrabots ipvoid --cdp-url http://127.0.0.1:9222/json
```

Também é possível fixar a URL em `.env` com `CHROME_DEBUG_URL`. O Playwright abre uma
aba própria nesse Chrome e não fecha o navegador ao final.

## Docker

O container usa o Chromium do Playwright em modo headless (`FIBRABOTS_HEADLESS=1`
no `docker-compose.yml`); não é necessário Chrome no host nem `host.docker.internal`.
