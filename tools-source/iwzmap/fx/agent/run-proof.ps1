param([Parameter(Mandatory)][string]$Tag,            # build tag: fx\src_<Tag> (fxproof.gsc, fx_manifest.json), fx\um_<Tag>
      [string]$Suffix='a', [string]$Sel='', [int]$Seconds=600)
# FX proof run: private leased session of um_<Tag> with the generated proof fixture and the fxperf frame-time DLL,
# then fx_proof.py (pixel-change mask in the FX region, temporal change, frame time per FX).
$ErrorActionPreference='Stop'
$F=(& "$PSScriptRoot\..\..\machine.ps1" Runtime 'iwz-stage2\fx')
$S=(Resolve-Path "$PSScriptRoot\..\..").Path
$run="proof-$Tag-$Suffix"
$extra='+set cg_fov 65 +set com_maxfps 0 +set r_vsync 0 +set paris_iwz_mode fxproof +set paris_iwz_fxproof 1 +set paris_iwz_fxonly -2 +set paris_iwz_fxphase 0 +set paris_iwz_flickertest 1'
if($Sel){ $extra+=" +set paris_iwz_fxsel $Sel" }
& "$F\tools\run-fx.ps1" -Tag $run -UsermapDir "$F\um_$Tag" -Fixture "$F\src_$Tag\fxproof.gsc" -Extra $extra -Seconds $Seconds -DllEnv "IW7_FXPERF=$F\runs\$run.fxperf.txt"
if($LASTEXITCODE -eq 3){ exit 3 }
$ff=(Get-FileHash "$F\um_$Tag\cp_iwz.ff" -Algorithm SHA256).Hash
$j=Get-Content "$F\runs\$run\result.local.json" -Raw | ConvertFrom-Json
"FF build $ff run $($j.FFSHA256) match=$($ff -eq $j.FFSHA256)"
& (& "$PSScriptRoot\..\..\machine.ps1" Runtime 'iwz-stage2\level\venv\Scripts\python.exe') -I "$S\fx\fx_proof.py" "$F\runs\$run" "$F\src_$Tag\fx_manifest.json" "$F\analysis\$run" --perf "$F\runs\$run.fxperf.txt"
