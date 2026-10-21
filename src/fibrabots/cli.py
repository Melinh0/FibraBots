from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fibrabots import config
from fibrabots.bots.abuseipdb import AbuseIPDBBot
from fibrabots.bots.ipvoid import IPVoidBot
from fibrabots.bots.pulsedive import PulsediveBot
from fibrabots.bots.virustotal import VirusTotalBot
from fibrabots.convert import abuseipdb as convert_abuseipdb
from fibrabots.convert import csv as convert_csv
from fibrabots.convert import ips as convert_ips
from fibrabots.convert import ipvoid as convert_ipvoid
from fibrabots.convert import pulsedive as convert_pulsedive
from fibrabots.convert import union as convert_union
from fibrabots.convert import validate as validate_ipvoid
from fibrabots.convert import virustotal as convert_virustotal
from fibrabots.logging_utils import setup_logging
from fibrabots.utils import dataset_paths

LOGGER = logging.getLogger(__name__)


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", type=Path, help="Arquivo de IPs de entrada.")
    parser.add_argument("--limit", type=int, help="Máximo de IPs a processar.")
    parser.add_argument("--force", action="store_true", help="Reprocessar IPs já existentes.")


def _add_http_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=float, default=config.REQUEST_TIMEOUT)
    parser.add_argument("--delay", type=float, default=config.REQUEST_DELAY)


def _add_browser_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--browser-timeout", type=float, default=config.BROWSER_TIMEOUT)
    parser.add_argument("--pause", type=float, default=config.BROWSER_PAUSE)
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=config.BROWSER_HEADLESS,
        help="Executar o navegador sem interface gráfica.",
    )
    parser.add_argument(
        "--cdp-url",
        default=config.cdp_url(),
        help="Conectar a um Chrome já em execução via CDP em vez de abrir o Chromium.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fibrabots",
        description="Coleta e consolida reputação de endereços IP.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Exibir logs detalhados.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    abuse = subparsers.add_parser("abuseipdb", help="Coleta dados do AbuseIPDB.")
    _add_common_options(abuse)
    _add_http_options(abuse)
    abuse.add_argument("--output", type=Path, default=config.ABUSEIPDB_OUTPUT)
    abuse.add_argument("--max-age-days", type=int, default=90)
    abuse.add_argument("--batch-size", type=int, default=100)

    virustotal = subparsers.add_parser("virustotal", help="Coleta dados do VirusTotal.")
    _add_common_options(virustotal)
    _add_http_options(virustotal)
    virustotal.add_argument("--output", type=Path, default=config.VIRUSTOTAL_OUTPUT)

    ipvoid = subparsers.add_parser("ipvoid", help="Coleta relatórios do IPVoid via navegador.")
    _add_common_options(ipvoid)
    _add_browser_options(ipvoid)
    ipvoid.add_argument("--output-dir", type=Path, default=config.IPVOID_DIR)
    ipvoid.add_argument("--manual-captcha", action="store_true")
    ipvoid.add_argument("--captcha-wait", type=float, default=60)

    pulsedive = subparsers.add_parser("pulsedive", help="Coleta indicadores do Pulsedive via API.")
    _add_common_options(pulsedive)
    pulsedive.add_argument("--output-dir", type=Path, default=config.PULSEDIVE_DIR)
    pulsedive.add_argument("--timeout", type=float, default=config.REQUEST_TIMEOUT)
    pulsedive.add_argument("--delay", type=float, default=config.PULSEDIVE_DELAY)

    convert = subparsers.add_parser("convert", help="Converte dados brutos em planilhas.")
    convert.add_argument(
        "source",
        choices=["abuseipdb", "virustotal", "ipvoid", "pulsedive", "union", "csv", "all"],
    )
    convert.add_argument("--input", type=Path, help="Arquivo ou diretório de entrada.")
    convert.add_argument("--output", type=Path, help="Arquivo de saída.")
    convert.add_argument("--processed-dir", type=Path, default=config.PROCESSED_DIR)

    validate = subparsers.add_parser(
        "validate-ipvoid", help="Valida (e opcionalmente remove) relatórios do IPVoid."
    )
    validate.add_argument("--input-dir", type=Path, default=config.IPVOID_DIR)
    validate.add_argument("--delete", action="store_true")

    make_ips = subparsers.add_parser("make-ips", help="Gera uma lista de IPs de uma faixa /24.")
    make_ips.add_argument("--prefix", required=True, help="Prefixo, exemplo: 8.8.8")
    make_ips.add_argument("--start", type=int, default=0)
    make_ips.add_argument("--end", type=int, default=255)
    make_ips.add_argument("--output", type=Path, default=config.DEFAULT_INPUT)

    extract = subparsers.add_parser("extract-ips", help="Extrai IPs de JSON ou CSV.")
    extract.add_argument("--format", choices=["json", "csv"], required=True)
    extract.add_argument("--input", type=Path, required=True)
    extract.add_argument("--output", type=Path, default=config.DEFAULT_INPUT)
    extract.add_argument("--column", default="IP", help="Coluna do CSV (padrão: IP).")

    return parser


def _input_path(args: argparse.Namespace) -> Path:
    return args.input or config.DEFAULT_INPUT


def _run_abuseipdb(args: argparse.Namespace) -> int:
    bot = AbuseIPDBBot(
        api_keys=config.abuseipdb_keys(),
        output=args.output,
        max_age_days=args.max_age_days,
        timeout=args.timeout,
        delay=args.delay,
        batch_size=args.batch_size,
        force=args.force,
    )
    return bot.run(_input_path(args), limit=args.limit)


def _run_virustotal(args: argparse.Namespace) -> int:
    bot = VirusTotalBot(
        api_key=config.virustotal_key(),
        output=args.output,
        timeout=args.timeout,
        delay=args.delay,
        force=args.force,
    )
    return bot.run(_input_path(args), limit=args.limit)


def _run_ipvoid(args: argparse.Namespace) -> int:
    bot = IPVoidBot(
        output_dir=args.output_dir,
        timeout=args.browser_timeout,
        pause=args.pause,
        manual_captcha=args.manual_captcha,
        captcha_wait=args.captcha_wait,
        force=args.force,
        headless=args.headless,
        cdp_url=args.cdp_url,
    )
    return bot.run(_input_path(args), limit=args.limit)


def _run_pulsedive(args: argparse.Namespace) -> int:
    bot = PulsediveBot(
        output_dir=args.output_dir,
        api_key=config.pulsedive_key(),
        timeout=args.timeout,
        delay=args.delay,
        force=args.force,
    )
    return bot.run(_input_path(args), limit=args.limit)


def _convert_all(processed_dir: Path) -> int:
    paths = dataset_paths(processed_dir)
    steps = [
        (
            "AbuseIPDB",
            lambda: convert_abuseipdb.convert(config.ABUSEIPDB_OUTPUT, paths["abuseipdb"]),
        ),
        (
            "VirusTotal",
            lambda: convert_virustotal.convert(config.VIRUSTOTAL_OUTPUT, paths["virustotal"]),
        ),
        ("IPVoid", lambda: convert_ipvoid.convert(config.IPVOID_DIR, paths["ipvoid"])),
        (
            "Pulsedive",
            lambda: convert_pulsedive.convert(config.PULSEDIVE_DIR, paths["pulsedive"]),
        ),
        ("União", lambda: convert_union.convert(processed_dir, paths["total_xlsx"])),
        ("CSV", lambda: convert_csv.convert(paths["total_xlsx"], paths["total_csv"])),
    ]
    failures = 0
    for name, step in steps:
        try:
            step()
        except (FileNotFoundError, ValueError) as exc:
            LOGGER.warning("%s ignorado: %s", name, exc)
        except Exception as exc:
            failures += 1
            LOGGER.error("%s falhou: %s", name, exc)
    return failures


def _run_convert(args: argparse.Namespace) -> int:
    paths = dataset_paths(args.processed_dir)
    if args.source == "all":
        return _convert_all(args.processed_dir)
    if args.source == "abuseipdb":
        convert_abuseipdb.convert(
            args.input or config.ABUSEIPDB_OUTPUT, args.output or paths["abuseipdb"]
        )
    elif args.source == "virustotal":
        convert_virustotal.convert(
            args.input or config.VIRUSTOTAL_OUTPUT, args.output or paths["virustotal"]
        )
    elif args.source == "ipvoid":
        convert_ipvoid.convert(args.input or config.IPVOID_DIR, args.output or paths["ipvoid"])
    elif args.source == "pulsedive":
        convert_pulsedive.convert(
            args.input or config.PULSEDIVE_DIR, args.output or paths["pulsedive"]
        )
    elif args.source == "union":
        convert_union.convert(args.input or args.processed_dir, args.output or paths["total_xlsx"])
    elif args.source == "csv":
        convert_csv.convert(args.input or paths["total_xlsx"], args.output or paths["total_csv"])
    else:
        raise ValueError(f"Fonte desconhecida: {args.source}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    try:
        if args.command == "abuseipdb":
            _run_abuseipdb(args)
        elif args.command == "virustotal":
            _run_virustotal(args)
        elif args.command == "ipvoid":
            _run_ipvoid(args)
        elif args.command == "pulsedive":
            _run_pulsedive(args)
        elif args.command == "convert":
            failures = _run_convert(args)
            if failures:
                return 1
        elif args.command == "validate-ipvoid":
            validate_ipvoid.validate(args.input_dir, delete=args.delete)
        elif args.command == "make-ips":
            convert_ips.make_ips(args.prefix, args.output, args.start, args.end)
        elif args.command == "extract-ips":
            if args.format == "json":
                convert_ips.extract_from_json(args.input, args.output)
            else:
                convert_ips.extract_from_csv(args.input, args.output, args.column)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
