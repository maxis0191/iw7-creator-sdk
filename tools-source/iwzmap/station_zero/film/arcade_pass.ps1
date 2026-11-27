# arcade_pass.ps1 -Pass <folder> [-Doc <document>]: one live pass of the Arcade (shell + goods: arcade_doc.py), one session.
# Real power states: ON (`live power on`, which now leaves the dark vision: the darkness fix is in this worktree's SDK) and OFF.
# The SDK is this worktree's: STUDIO_CONFIG names it, IWZ_SDK is the worktree root (the build reads it).
param([string]$Pass, [string]$Doc = 'C:\studio-data\sz\film\arcade\shell\docall')
$ErrorActionPreference = 'Continue'
$film = $PSScriptRoot
$root = (Resolve-Path "$film\..\..\..\..").Path
$env:STUDIO_ROOT = 'C:/studio'
$env:STUDIO_CONFIG = 'C:\studio-data\sz\film\arcade\shell\studio_a2.json'
$env:IWZ_SDK = $root
$env:IWZ_ZONETOOL_EXE = 'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe'
New-Item -ItemType Directory -Force $Pass | Out-Null
Push-Location C:\studio
python -m studio live start $Doc --idle-min 30 > "$Pass\start.json" 2> "$Pass\start.err"
$ok = $LASTEXITCODE
Pop-Location
if ($ok -eq 0) {
    $env:A2_STATES = 'on,off'
    python "$film\arcade_frames.py" $Pass $Doc > "$Pass\frames.log" 2>&1
} else { "start failed: exit $ok" }
Push-Location C:\studio
python -m studio live stop $Doc > "$Pass\stop.json" 2>&1
Pop-Location
"pass done"
