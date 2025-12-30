<# 
    Wrapper for local CI-equivalent checks.
    Runs `python scripts/run_ci_checks.py` from the repo root and, on failure,
    prints a concise git status to help developers see what changed.
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassthroughArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

Push-Location -LiteralPath $repoRoot
try {
    $pythonArgs = @('scripts/run_ci_checks.py')
    if ($PassthroughArgs) {
        $pythonArgs += $PassthroughArgs
    }

    & python @pythonArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host "`n[FAIL] python $($pythonArgs -join ' ') exited with $exitCode" -ForegroundColor Red
        $git = Get-Command git -ErrorAction SilentlyContinue
        if ($git) {
            Write-Host "`n=== git status --short ==="
            git status --short
        }
        else {
            Write-Host "`nGit executable not found; skipping status dump."
        }
    }
    else {
        Write-Host "`n[OK] CI checks completed successfully."
    }

    exit $exitCode
}
finally {
    Pop-Location
}

