# arcade_pass.ps1 <pass folder>: one live pass of the Arcade shell, one session at a time.
# 1. the lit-vision variant (arcade_litview.py): frames labelled LIT; 2. the document itself in the dark vision: frames labelled OFF.
# (ON is not shot: with every light baked and no power bank the darkness script never releases the dark vision; ON equals OFF, pass 1.)
param([string]$Pass)
$ErrorActionPreference = 'Continue'
$film = $PSScriptRoot
$doc = 'C:\studio-data\sz\film\arcade\shell\doc'
$lit = 'C:\studio-data\sz\film\arcade\shell\litview'
$env:STUDIO_ROOT = 'C:/studio'
$env:IWZ_ZONETOOL_EXE = 'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe'
New-Item -ItemType Directory -Force $Pass | Out-Null
python "$film\arcade_litview.py" $doc $lit
foreach ($run in @(@{d = $lit; s = 'lit'; tag = 'litview'}, @{d = $doc; s = 'off'; tag = 'doc'})) {
    Push-Location C:\studio
    python -m studio live start $run.d --idle-min 30 > "$Pass\start_$($run.tag).json" 2> "$Pass\start_$($run.tag).err"
    $ok = $LASTEXITCODE
    Pop-Location
    if ($ok -eq 0) {
        $env:A2_STATES = $run.s
        python "$film\arcade_frames.py" $Pass $run.d > "$Pass\frames_$($run.tag).log" 2>&1
    } else { "start $($run.tag) failed: exit $ok" }
    Push-Location C:\studio
    python -m studio live stop $run.d > "$Pass\stop_$($run.tag).json" 2>&1
    Pop-Location
}
"pass done"
