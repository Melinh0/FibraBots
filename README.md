# FibraBots

Coleta e consolidação de reputação de endereços IP a partir de AbuseIPDB, VirusTotal,
IPVoid e Pulsedive. O projeto usa caminhos relativos, configuração por variáveis de
ambiente e o mesmo código em Windows, Linux e macOS.

## Estrutura

```text
.
├── data/
│   ├── input/                  # listas de IPs de entrada
│   ├── raw/                    # dados brutos coletados
│   │   ├── abuseipdb/results.json
│   │   ├── virustotal/results.json
│   │   ├── ipvoid/<ip>.txt
│   │   └── pulsedive/<ip>.json
│   └── processed/              # planilhas consolidadas (xlsx/csv)
├── docs/
│   ├── browser-setup.md        # configuração do Chrome e captcha
│   └── features.txt            # descrição das features do dataset
├── scripts/
│   └── run_sequential.ps1|.sh  # executa as etapas uma de cada vez
├── src/fibrabots/
│   ├── bots/                   # AbuseIPDB, VirusTotal, IPVoid e Pulsedive
│   ├── convert/                # conversores e consolidação
│   └── cli.py                  # interface fibrabots
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml              # dependências para uv
├── requirements.txt            # dependências para pip
└── uv.lock
```

## Requisitos

- Python 3.10 ou superior.
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip.
- Docker e Docker Compose são opcionais.
- Navegador: o Playwright baixa o Chromium automaticamente na primeira execução do
  bot `ipvoid`. Nada de Selenium, chromedriver ou Chrome instalado.

## Configuração

Crie o arquivo local de variáveis (ele é ignorado pelo Git):

```bash
cp .env.example .env
```

Preencha:

```dotenv
ABUSEIPDB_API_KEYS=chave1,chave2
VIRUSTOTAL_API_KEY=sua_chave
# Pulsedive: sem chave a API aceita poucas requisições por dia; crie uma conta
# gratuita em pulsedive.com para elevar a cota.
PULSEDIVE_API_KEY=
FIBRABOTS_HEADLESS=0
```

As chaves antigas que estavam no código devem ser rotacionadas nos provedores, pois
ficaram expostas no histórico do Git. O código atual lê apenas variáveis de ambiente.

## Instalação

Com uv:

```bash
uv sync
uv run fibrabots --help
```

Com pip:

```bash
python -m pip install -r requirements.txt
python -m fibrabots --help
```

Para o bot `ipvoid` com pip, baixe o Chromium do Playwright uma vez:

```bash
python -m playwright install chromium
```

## Uso

Os bots são idempotentes: por padrão, IPs já presentes na saída são ignorados. Use
`--force` para reprocessar.

```bash
# APIs
uv run fibrabots abuseipdb --input data/input/ips.txt
uv run fibrabots virustotal --input data/input/ips.txt
uv run fibrabots pulsedive --input data/input/ips.txt

# Navegador (Playwright abre o Chromium sozinho)
uv run fibrabots ipvoid --input data/input/ips.txt --manual-captcha

# Conversão e consolidação
uv run fibrabots convert all

# Manutenção
uv run fibrabots validate-ipvoid
uv run fibrabots validate-ipvoid --delete
uv run fibrabots make-ips --prefix 8.8.8 --output data/input/whitelist_ips.txt
uv run fibrabots extract-ips --format json --input data/raw/abuseipdb/results.json
```

Opções úteis:

- `--limit 100`: processa somente os primeiros 100 IPs pendentes.
- `--force`: ignora a checagem de saídas existentes.
- `--input`/`--output`: sobrescreve os caminhos padrão.
- `--delay`: pausa entre requisições HTTP.

### Como cada bot coleta dados

| Bot        | Método                    | Observação                                    |
| ---------- | ------------------------- | --------------------------------------------- |
| abuseipdb  | API REST                  | várias chaves rotacionadas em `ABUSEIPDB_API_KEYS` |
| virustotal | API REST v3               | chave única em `VIRUSTOTAL_API_KEY`           |
| pulsedive  | API pública               | cota diária baixa sem chave; use `PULSEDIVE_API_KEY` |
| ipvoid     | Navegador (Playwright)    | preenche o formulário e lê a tabela de resultados |

### Navegador

O `ipvoid` abre um Chromium gerenciado pelo Playwright. Por padrão a janela fica
visível; use `--headless` (ou `FIBRABOTS_HEADLESS=1`) em servidor. Se o IPVoid
exibir captcha, use `--manual-captcha` e resolva o desafio na janela. Para usar um
Chrome já aberto com suas extensões:

```bash
uv run fibrabots ipvoid --cdp-url http://127.0.0.1:9222/json
```

Detalhes em [docs/browser-setup.md](docs/browser-setup.md).

## Docker

O Compose usa o mesmo `.env` e monta `./data` no container. Execute um serviço por vez:

```bash
docker compose build

docker compose run --rm abuseipdb
docker compose run --rm virustotal
docker compose run --rm convert
docker compose run --rm ipvoid
docker compose run --rm pulsedive
```

O container instala o Chromium do Playwright na imagem e roda o `ipvoid` em modo
headless; não é preciso Chrome no host.

Perfis disponíveis:

- `api`: `abuseipdb`, `virustotal`, `pulsedive`.
- `browser`: `ipvoid`.
- `pipeline`: `convert`.

## Execução sequencial

Os scripts executam uma etapa por vez e param em caso de erro. Por padrão, rodam os
bots de API e a consolidação; inclua os bots de navegador apenas quando o Chrome
estiver pronto.

```powershell
pwsh scripts/run_sequential.ps1
pwsh scripts/run_sequential.ps1 -IncludeBrowser
pwsh scripts/run_sequential.ps1 -Docker
```

```bash
bash scripts/run_sequential.sh
bash scripts/run_sequential.sh --include-browser
bash scripts/run_sequential.sh --docker
```

## Desenvolvimento

```bash
uv sync            # instala o pacote e o grupo dev (pytest, ruff)
uv run playwright install chromium
uv run ruff check .
uv run pytest
```

## Segurança

- `.env` não é versionado; mantenha as chaves apenas nele ou no gerenciador de segredos.
- Nunca commite chaves de API.
- Se as chaves antigas forem reutilizadas, gere novas nos painéis do AbuseIPDB e VirusTotal.
