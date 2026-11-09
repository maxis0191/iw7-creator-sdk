param([Parameter(Mandatory)][string]$Tag, [switch]$ReuseBake, [string]$BakeFrom='', [switch]$ReuseCompile, [int]$Rays=256,
# Reference copy (darkness agent): the exact build used for d12 (run dk15-d12). Paths are this machine's; the level
# builder takes the darkness steps into its own build-g.ps1 (README "Integration").
      [string]$Ambient='0.025', [string]$Scale='1400', [string]$RadiusScale='1.8', [string]$CueScale='0.35', [string]$FlBright='1.0',
      [switch]$TestVfx)
# Darkness build on the level builder's current source (g27 flags of level\tools\chain-g27.sh: -SkipPick -Bake
# --texel 6 --ambient 0.012 -Train -NeutralProbes -Fx -Audio -NavObstacles -Lights -Smodels -Kit), with:
#   generator IWZ_DARK=1 (SDK codex/iwzmap-darkness = sz2 + darkness), dark split of the layout lights (dark_build.py:
#   emergency bake, named power lights, amber cues x CueScale), dark bake, darkness zonetool (named scriptable lights),
#   flashlight effects, add_darkness (modules, dark visions: default + exposure variants under stock names, lit vision).
# Dark vision args: env IWZ_DARK_ARGS (pwsh -File cannot take a value that starts with --).
# Output darkness\src_<Tag>[_lm], darkness\um_<Tag>. Reads level\ files (props_g27.json, train ports), never writes them.
$ErrorActionPreference='Stop'
$DK='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\darkness'
$L='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level'
$S='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-darkness\tools-source\iwzmap'
$B='C:\Users\ezvalo\Documents\IW7-Products\worktrees\iw7-creator-sdk-lightbake\tools-source\iwzmap\bake'
$PY='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\lightmaps\venv\Scripts\python.exe'
$Z='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-darkness\build\bin\x64\Release\zonetool.exe'
$D='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump'
$W="$DK\ztwork"
$src="$DK\src_$Tag"; $um="$DK\um_$Tag"
# (d12) run dk13 sweep (fast adaptation): the manual exposure keys are tonemapExposure / tonemapExposureAdjust
# (tonemapMaxExposure does nothing, auto or manual). tonemapExposureAdjust -3: hall 2.8 %, platform 0.85 % outside the
# cone (run dk14). Default -3; ride = -2, main = -2.5 for the final sweep. Lit: veilStrength 0 (veiling glare = the white haze
# around the hot power spots, dk10 / dk13); alien = lit + veil 0 (= default lit), ghost_path = lit + veil 0 + auto
# exposure bias -1 (lit sweep).
$DarkArgs='--dark tonemapAuto=0;tonemapAdaptSpeed=1;tonemapExposureAdjust=-3 --variants ea2:tonemapAuto=0;tonemapAdaptSpeed=1;tonemapExposureAdjust=-2|ea25:tonemapAuto=0;tonemapAdaptSpeed=1;tonemapExposureAdjust=-2.5|lita:fogMaxOpacity=0.03;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0;tonemapAdaptSpeed=1|litb:fogMaxOpacity=0.03;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0;tonemapAdaptSpeed=1;tonemapAutoExposureAdjust=-1 --alias cp_zmb_int_triton_ride=ea2,cp_zmb_int_triton_main=ea25,cp_zmb_alien=lita,cp_zmb_ghost_path=litb --lit fogMaxOpacity=0.03;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0'
if($env:IWZ_DARK_ARGS){ $DarkArgs=$env:IWZ_DARK_ARGS }
foreach($v in 'IWZ_LIGHTS','IWZ_SMODELS','IWZ_KIT','IWZ_KIT_MATERIAL_MAP','IWZ_KIT_BASELINE','IWZ_AUDIO','IWZ_DARK','IWZ_TRAIN','IWZ_TRAIN_CAR_BOXES','IWZ_TRAIN_PROPS','IWZ_PROBES','IWZ_PROBES_SCALE','IWZ_FX_TXT'){ Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
$env:IWZ_DARK='1'; $env:IWZ_LIGHTS='1'; $env:IWZ_SMODELS='1'; $env:IWZ_DOUBLE_SIDED='1'
$env:IWZ_KIT='1'; $env:IWZ_KIT_MATERIAL_MAP='mopw/glass_opaque_02=m/clk_glass_grunge_mild'
$TP=@("$DK\..\train\port\banzai_v3","$DK\..\train\port\kit_v4","$DK\..\train\port\genset","$DK\..\train\port\props_v4") | ForEach-Object { [IO.Path]::GetFullPath($_) }
$env:IWZ_TRAIN='1'; $env:IWZ_TRAIN_CARS='3'; $env:IWZ_TRAIN_CONSIST_END_X='2540'; $env:IWZ_TRAIN_TRACK_EAST_X='2848'
$env:IWZ_TRAIN_CAR_BOXES="$($TP[0])\collision\iwz_t7e_subway_car_a.json"; $env:IWZ_TRAIN_PROPS="$L\props_g27.json"
$env:IWZ_PROBES='neutral'
$env:IWZ_AUDIO='1'
$FxTxt="$S\fx\station_zero_fx_g25.txt"; $env:IWZ_FX_TXT=$FxTxt
python -I "$S\station_zero2.py" "$D\cp_zmb" $src | Select-Object -Last 1
python -I "$S\sz2_plan.py" $src | Select-Object -Last 1
$AS='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\assets'
python -I "$S\sz2_artlint.py" $src --json "$DK\artlint_$Tag.json" --catalog "$AS\catalog.json" --kit "$AS\kit\kit_final.json" | Select-Object -Last 1
if($LASTEXITCODE -ne 0){ "WARNING artlint failed: $DK\artlint_$Tag.json" }
python -I "$S\sz2_navconn.py" $src --json "$DK\navconn_$Tag.json" | Select-Object -Last 2
if($LASTEXITCODE -ne 0){ throw 'nav connectivity failed' }
& $PY -I "$B\layout_lights.py" $src "$DK\lights_full_$Tag.json" --texel 6 --ambient 0.012
& $PY -I "$S\darkness\dark_build.py" $src "$DK\lights_full_$Tag.json" "$DK\lights_$Tag.json" --ambient $Ambient --scale $Scale --radius-scale $RadiusScale --cue-scale $CueScale
if($LASTEXITCODE){ throw 'dark_build failed' }
$build="$src`_lm"
if($ReuseBake){
  $from="$DK\src_$BakeFrom"
  if((Get-FileHash "$from\world.bin").Hash -ne (Get-FileHash "$src\world.bin").Hash){ throw "render world differs from ${BakeFrom}: bake again" }
  if((Get-FileHash "$DK\lights_$BakeFrom.json").Hash -ne (Get-FileHash "$DK\lights_$Tag.json").Hash){ throw "dark light list differs from ${BakeFrom}: bake again" }
  if(Test-Path $build){ Remove-Item $build -Recurse -Force }
  Copy-Item "$from`_lm" $build -Recurse
  Get-ChildItem $src -File | Where-Object { $_.Name -notin @('world.bin','lighting.txt') } | ForEach-Object { Copy-Item $_.FullName (Join-Path $build $_.Name) -Force }
  "bake reused from $BakeFrom"
} else {
  . 'C:\Users\ezvalo\Documents\IW7-Products\iw7-mod-components\ops\Resource-Scheduler.Core.ps1'
  for($i=0;$i -lt 900;$i++){ try { $lease=Enter-IW7ResourceLease -Scope "$DK\bake" -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner 'IWZ darkness agent: dark light bake'; break } catch { if($_.Exception.Message -match 'busy|reserved|wait'){ Start-Sleep 60; continue }; throw } }
  try {
    if(Test-Path $build){ Remove-Item $build -Recurse -Force }
    & $PY -I "$B\lmbake.py" $src "$DK\lights_$Tag.json" $build --rays $Rays --bounces 3 --denoise 1 2>&1 | Select-Object -Last 4
  } finally { for($r=0;$r -lt 60;$r++){ try { Exit-IW7ResourceLease -Token $lease.Token | Out-Null; break } catch { Start-Sleep 3 } } }
  if(!(Test-Path "$build\lightmap\secondary.dds")){ throw 'bake produced no lightmap' }
}
# flashlight effects: six copies of the patched cp_disco train front light (one LIGHT_SPOT emitter, no sprite)
$V="$DK\vfxsrc"; $FD="$DK\..\fx\ztwork\dump"
$TL="$FD\cp_disco\particlesystem\vfx\iw7\levels\cp_disco\subway_train\vfx_train_front_light_ch.iw7VFX"
$fxMine=@()
foreach($sfx in '','_b','_c','_d','_e','_f'){
  & $PY -I "$S\darkness\make_vfx_light.py" $TL $V "vfx/iwz/vfx_iwz_flashlight_world$sfx" --fov 32 --inner 12 --radius 900 --color 1,0.92,0.80 --brightness $FlBright --shadow 1 --near 8 --life 100000 | Out-Null
  $fxMine+="iwz:vfx/iwz/vfx_iwz_flashlight_world$sfx"
}
if($TestVfx){
  foreach($b in '1.0','3.0'){ $n="vfx/iwz/vfx_iwz_fl_b$($b -replace '\.','')"; & $PY -I "$S\darkness\make_vfx_light.py" $TL $V $n --fov 32 --inner 12 --radius 900 --color 1,0.92,0.80 --brightness $b --shadow 1 --near 8 --life 100000 | Out-Null; $fxMine+="iwz:$n" }
}
$A=@{KeepSubmodels=$true; NavObstacles=$true; Darkness=$true; DarkArgs=$DarkArgs; FxReport="$um.fx_import.json"
     AudioSdk="$S\audio"; AudioBank='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src15'; AudioModels='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src'}
if($ReuseCompile){ $A['ReuseCompile']=$true }
# kit + train models
$km=@((Get-Content "$src\layout.json" -Raw | ConvertFrom-Json).kit_models | Where-Object { -not $_.StartsWith('iwz_') })
$KD='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\kitimport\ztwork\dump'
$A['KitDumps']=@("cp_disco=$KD\cp_disco;$KD\techsets_cp_disco","cp_final=$KD\cp_final;$KD\techsets_cp_final")
foreach($p in $TP){ foreach($f in Get-ChildItem "$p\xmodel\*.xmb"){ $km+=('train:'+$f.BaseName) } }
$A['KitDumps']+=("train=$($TP -join ';')")
$A['KitReport']="$um.kit_import.json"
# ambient FX (level builder's g25 placement: emergency glow sprites already disabled there)
$LD2="$L\ztwork\dump"
$imp=(python -I "$S\fx\fx_place.py" $FxTxt $build --list-imports | Select-Object -Last 1).Trim()
$ncs=@('--ncs',"$D\cp_zmb\netconststrings\ncs_efx_level.json")
$fxd="cp_disco=$FD\cp_disco;$KD\cp_disco;$LD2\techsets_cp_disco"
if($imp){
  python -I "$S\fx\fx_import.py" $W 'cp_iwz' --fx $imp --dump $fxd --ncs-out "$DK\ncs_$Tag.json" --report "$DK\fx_import_dry_$Tag.json" --dry-run | Select-Object -Last 1
  $dry=Get-Content "$DK\fx_import_dry_$Tag.json" -Raw | ConvertFrom-Json
  if(@($dry.kitModels).Count){ $km+=@($dry.kitModels) }
  $ncs=@('--ncs',"$DK\ncs_$Tag.json")
}
python -I "$S\fx\fx_place.py" $FxTxt $build @ncs --fixture-out "$build\fxproof.gsc" --manifest-out "$build\fx_manifest.json" | Select-Object -Last 2
if($LASTEXITCODE){ throw 'fx_place failed' }
$A['FxImport']=((@($imp) + $fxMine) | Where-Object { $_ }) -join ','
$A['FxDumps']=@($fxd,"iwz=$V")
$A['KitModels']=($km | Select-Object -Unique) -join ','
# the darkness zonetool must carry the merged door-brushmodels compiler (neutral probes 1a8323f): wait for its build
for($i=0;$i -lt 720 -and -not (Select-String -Path "$DK\build-zt2.log" -Pattern '^exit 0' -Quiet -ErrorAction SilentlyContinue);$i++){ Start-Sleep 30 }
if(-not (Select-String -Path "$DK\build-zt2.log" -Pattern '^exit 0' -Quiet)){ throw 'darkness zonetool rebuild did not finish' }
& "$S\build-sz2.ps1" -Src $build -UmOut $um -Work $W -ZoneToolExe $Z @A
(Get-FileHash "$um\cp_iwz.ff" -Algorithm SHA256).Hash
