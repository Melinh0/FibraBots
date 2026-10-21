#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

use_docker=false
include_browser=false
steps=()

for argument in "$@"; do
  case "$argument" in
    --docker) use_docker=true ;;
    --include-browser) include_browser=true ;;
    *) steps+=("$argument") ;;
  esac
done

if ((${#steps[@]} == 0)); then
  steps=(abuseipdb virustotal pulsedive convert)
fi

if $include_browser; then
  steps=(ipvoid "${steps[@]}")
fi

run_step() {
  local step="$1"
  echo
  echo "=== Executando: $step ==="
  if $use_docker; then
    docker compose run --rm "$step"
  else
    case "$step" in
      convert) uv run fibrabots convert all ;;
      *) uv run fibrabots "$step" ;;
    esac
  fi
}

for step in "${steps[@]}"; do
  case "$step" in
    abuseipdb|virustotal|ipvoid|pulsedive|convert) run_step "$step" ;;
    *) echo "Etapa desconhecida: $step" >&2; exit 1 ;;
  esac
done

echo
echo "Pipeline concluído (execução sequencial)."
