param([string]$Venv=(& "$PSScriptRoot\..\machine.ps1" BakePython),[string]$Python='python')
# The light baker's Python environment (lmbake.py, layout_lights.py, lm_measure.py): numba, numpy, scipy, pillow at the
# versions of requirements.txt, in a folder of the runtime area (never in a checkout). Prints the environment's python.exe.
# Block compression uses DirectXTex texconv: $env:IWZ_TEXCONV, else <Documents>\IW7-Tools\texconv-may2026\texconv.exe.
$ErrorActionPreference='Stop'
$py=Join-Path $Venv 'Scripts\python.exe'
if(!(Test-Path -LiteralPath $py)){
  & $Python -m venv $Venv
  if($LASTEXITCODE){ throw "python -m venv failed: $Venv" }
}
& $py -m pip install --disable-pip-version-check -q -r (Join-Path $PSScriptRoot 'requirements.txt')
if($LASTEXITCODE){ throw 'pip install failed' }
& $py -I -c "import numba, numpy, scipy, PIL; print('bake env: numba', numba.__version__, 'numpy', numpy.__version__)"
if($LASTEXITCODE){ throw 'the environment does not import its packages' }
$tc=if($env:IWZ_TEXCONV){$env:IWZ_TEXCONV}else{Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'IW7-Tools\texconv-may2026\texconv.exe'}
if(!(Test-Path -LiteralPath $tc)){ Write-Warning "texconv not found at $tc (DirectXTex release; set IWZ_TEXCONV)" }
$py
