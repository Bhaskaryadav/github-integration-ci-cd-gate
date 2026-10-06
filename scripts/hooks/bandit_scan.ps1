# PostToolUse hook — Windows PowerShell alternative for bandit scanning.
param()

$Severity = if ($env:BANDIT_SEVERITY_LEVEL) { $env:BANDIT_SEVERITY_LEVEL } else { "medium" }
$Files = @()

if ($env:CLAUDE_FILE_PATHS) {
    $Files = $env:CLAUDE_FILE_PATHS -split '\s+' | Where-Object { $_ -match '\.py$' -and (Test-Path $_) }
}

if ($Files.Count -eq 0) {
    Write-Host "[bandit-hook] No Python files to scan."
    exit 0
}

New-Item -ItemType Directory -Force -Path audit_log | Out-Null
Write-Host "[bandit-hook] Scanning: $($Files -join ', ')"

$out = Join-Path $env:TEMP "bandit_out.json"
& bandit --format json --severity-level $Severity --output $out @Files 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[bandit-hook] Clean scan."
    Remove-Item $out -ErrorAction SilentlyContinue
    exit 0
}

Write-Host "[bandit-hook] FINDINGS detected. Review bandit output."
Remove-Item $out -ErrorAction SilentlyContinue
exit 1
