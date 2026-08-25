# Bootstrap (Windows PowerShell) - thin wrapper around the cross-platform CLI.
# Canonical logic lives in src/ommw. This script only installs uv + the package
# if they are missing, then defers to `ommw doctor`.

<#
.SYNOPSIS
  Provision OMMW on a fresh Windows machine.
.DESCRIPTION
  Installs uv if missing, syncs dependencies, installs the ommw console script,
  then runs `ommw doctor`. Does NOT modify the system PATH permanently.
#>
[CmdletBinding()]
param(
  [switch]$SkipPython,
  [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Test-Command($n) { [bool](Get-Command $n -ErrorAction SilentlyContinue) }

if (-not $SkipPython) {
  if (-not (Test-Command python)) {
    Write-Error "Python 3.12+ not found on PATH. Install Python first (https://www.python.org/)."
  }
  $pyVer = (python --version 2>&1) -replace "Python ", ""
  $pyMajor, $pyMinor = $pyVer.Split(".")[0..1] | ForEach-Object { [int]$_ }
  if (($pyMajor -lt 3) -or ($pyMajor -eq 3 -and $pyMinor -lt 12)) {
    Write-Error "Python $pyVer is too old; OMMW requires 3.12+."
  }
}

# uv: install per-user if missing (no admin, no global PATH mutation).
if (-not (Test-Command uv)) {
  Write-Host "Installing uv (user-scoped)..." -ForegroundColor Cyan
  powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host "Syncing dependencies (uv sync --frozen)..." -ForegroundColor Cyan
uv sync --frozen

Write-Host "Installing ommw console script (editable)..." -ForegroundColor Cyan
uv pip install -e .

Write-Host "Running ommw doctor..." -ForegroundColor Cyan
uv run ommw doctor
