# The key of an incremental assembly (assemble_key.py): prints it. Arguments are passed through:
#   Get-AssembleKey.ps1 --file <f> ... --tree <d> ... --manifest <d> ... --text <t> ...
# Throws when an input path is missing (never an empty input). The timing goes to the host.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$KeyArgs)
$ErrorActionPreference='Stop'
$timing=[IO.Path]::GetTempFileName()
try {
  $key=(& python -I "$PSScriptRoot\assemble_key.py" @KeyArgs 2>$timing)
  if($LASTEXITCODE){ throw "assemble_key failed: $((Get-Content $timing -Raw).Trim())" }
  Write-Host ((Get-Content $timing -Raw).Trim())
  ($key | Select-Object -Last 1).Trim()
} finally { Remove-Item $timing -Force -ErrorAction SilentlyContinue }
