<# 
    Prints the most recent GitHub Actions run id + conclusion.
    Usage: ./scripts/gh_ci_latest.ps1 [additional gh run list args...]
    Requires the GitHub CLI (`gh`) to be installed and authenticated.
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AdditionalArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI ('gh') is required but was not found in PATH."
    exit 1
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$jqFilter = '.[0] | {id: .databaseId, conclusion: (.conclusion // "in_progress")}'

$argsList = @(
    'run', 'list',
    '--limit', '1',
    '--json', 'databaseId,conclusion'
)

if ($AdditionalArgs) {
    $argsList += $AdditionalArgs
}

$argsList += @('--jq', $jqFilter)

Push-Location -LiteralPath $repoRoot
try {
    $raw = & gh @argsList
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        exit $exitCode
    }

    if (-not $raw -or $raw -eq 'null') {
        Write-Host 'No CI runs found.'
        exit 1
    }

    $data = $raw | ConvertFrom-Json
    if ($null -eq $data) {
        Write-Host 'Unable to parse GH CLI output.'
        exit 1
    }

    $conclusion = if ([string]::IsNullOrEmpty($data.conclusion)) { 'in_progress' } else { $data.conclusion }
    Write-Host ("Latest run {0}: {1}" -f $data.id, $conclusion.ToUpperInvariant())
}
finally {
    Pop-Location
}

