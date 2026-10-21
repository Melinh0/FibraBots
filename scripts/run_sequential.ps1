param(
    [switch]$Docker,
    [switch]$IncludeBrowser,
    [string[]]$Steps
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$selected = if ($Steps) { $Steps } else { @("abuseipdb", "virustotal", "pulsedive", "convert") }
if ($IncludeBrowser) { $selected = @("ipvoid") + $selected }

foreach ($step in $selected) {
    Write-Host "`n=== Executando: $step ===" -ForegroundColor Cyan
    switch ($step) {
        "abuseipdb" {
            if ($Docker) { docker compose run --rm abuseipdb }
            else { uv run fibrabots abuseipdb }
        }
        "virustotal" {
            if ($Docker) { docker compose run --rm virustotal }
            else { uv run fibrabots virustotal }
        }
        "ipvoid" {
            if ($Docker) { docker compose run --rm ipvoid }
            else { uv run fibrabots ipvoid }
        }
        "pulsedive" {
            if ($Docker) { docker compose run --rm pulsedive }
            else { uv run fibrabots pulsedive }
        }
        "convert" {
            if ($Docker) { docker compose run --rm convert }
            else { uv run fibrabots convert all }
        }
        default { throw "Etapa desconhecida: $step" }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "A etapa '$step' falhou com código $LASTEXITCODE."
    }
}

Write-Host "`nPipeline concluído (execução sequencial)." -ForegroundColor Green
