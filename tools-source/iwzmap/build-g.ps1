param([Parameter(Mandatory)][string]$Tag, [switch]$SkipPick, [switch]$Bake, [string]$LightArgs='', [int]$Rays=256, [switch]$Audio, [switch]$NavObstacles, [switch]$ReuseBake, [string]$BakeFrom='', [switch]$Kit, [switch]$Lights, [switch]$Smodels, [switch]$KitBaseline, [switch]$Fx, [string]$FxTxt='', [switch]$NeutralProbes, [string]$ProbeScale='', [switch]$Train, [ValidateSet('g27','stock')][string]$StairStyle='g27', [switch]$GateOnly, [ValidateSet('g27','g27d','g27e')][string]$TrainSet='g27', [switch]$BakeLoose, [string]$ZoneToolExe='', [switch]$WithP1)
# Station Zero v2 level build <Tag>: generator -> (compile-only pass: sub-model log -> pick door blocker sub-model ->
# regenerate) -> optional light bake (layout_lights + lmbake, Build lease) -> full build with kept sub-models and own
# lightmap, using the merged door-brushmodel + lightmap zonetool. Output: level\src_<Tag>[_lm], level\um_<Tag>.
$ErrorActionPreference='Stop'
if($ReuseBake -and $BakeFrom -and $BakeFrom -eq $Tag){ throw "-BakeFrom $BakeFrom names the tag being built: the bake source would be deleted before it is copied. Name another tag, or leave -BakeFrom out to reuse src_$Tag`_lm in place." }
$L=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level')
$RT=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2')
$S=$PSScriptRoot                       # the checkout this script is in (no other SDK worktree)
$B="$S\bake"
$PY=(& "$PSScriptRoot\machine.ps1" BakePython)+'\Scripts\python.exe'
# the compiler: the x64-zt main binary (door brush models, named scriptable lights, static models, tome culling, zone-step
# fix: compiler-landing\zonetool-playeranim-1dcd449.exe = main 342b870) unless -ZoneToolExe or IWZ_ZONETOOL_EXE names one
$Z=if($ZoneToolExe){ $ZoneToolExe } elseif($env:IWZ_ZONETOOL_EXE){ $env:IWZ_ZONETOOL_EXE } else { (& "$PSScriptRoot\machine.ps1" Runtime 'compiler-landing\zonetool-playeranim-1dcd449.exe') }
$D=(& "$PSScriptRoot\machine.ps1" TemplateDump)
$src="$L\src_$Tag"; $um="$L\um_$Tag"
# -Kit: foreign-zone kit models (cp_disco / cp_final) placed by the generator (IWZ_KIT=1) and imported by kit_import.py
# (x64-zt codex/iwzmap-door-brushmodels bd5e7fb now carries kit-import dd5c7e8 and static-models a99270f)
if($Lights){ $env:IWZ_LIGHTS='1' } else { Remove-Item Env:IWZ_LIGHTS -ErrorAction SilentlyContinue }
if($Smodels){ $env:IWZ_SMODELS='1' } else { Remove-Item Env:IWZ_SMODELS -ErrorAction SilentlyContinue }
if($KitBaseline){ $env:IWZ_KIT='1'; $env:IWZ_KIT_BASELINE='1' } else { Remove-Item Env:IWZ_KIT_BASELINE -ErrorAction SilentlyContinue }
if($Kit){
  $env:IWZ_KIT='1'
  # g25: the hero train's opaque window glass becomes the grimy translucent clk glass of the same cp_disco dump
  $env:IWZ_KIT_MATERIAL_MAP='mopw/glass_opaque_02=m/clk_glass_grunge_mild'
} elseif(-not $KitBaseline){ Remove-Item Env:IWZ_KIT -ErrorAction SilentlyContinue }
$env:IWZ_DOUBLE_SIDED='1'
# stock-stair study: -StairStyle stock = cp_zmb-style clip sheet over 8-unit steps (A/B against g27c)
$env:IWZ_STAIR_STYLE=$StairStyle
# -Train: the train agent's track kit + hero car (SDK codex/iwzmap-hero-train 902d744, merged), BO3 ports in train\port
# (g27) train agent v4: track kit v4, G-2 genset + period wall fittings, lighter BO3 props (placed by IWZ_TRAIN_PROPS)
$TPR="$RT\train\port"
# -TrainSet g27 (g27..g27c): banzai_v3, kit_v4, genset, props_v4. g27d (train agent g27 round, coordinator 2026-11-09):
# banzai_v4 (bogies, livery, closed gangway), kit_v5 (ballast faces + dark wheels, proven in the train agent's e9),
# genset_v5 (+ iwz_g2_radiator), props_v4; kit_v5 also has iwz_track_256_disused_end / iwz_buffer_sleepers (Platform B)
if($TrainSet -eq 'g27'){ $TP=@("$TPR\banzai_v3","$TPR\kit_v4","$TPR\genset","$TPR\props_v4") }
elseif($TrainSet -eq 'g27e'){ $TP=@("$TPR\banzai_v5","$TPR\kit_v6","$TPR\genset_v6","$TPR\props_v4") }     # train agent round of 9 Nov (radiator v2, plate, buffers, skirt, crease, matte silt)
else { $TP=@("$TPR\banzai_v4","$TPR\kit_v5","$TPR\genset_v5","$TPR\props_v4") }     # (coordinator 2026-11-09) kit_v5 proven in train e9
if($Train){ $env:IWZ_TRAIN='1'; $env:IWZ_TRAIN_CARS='3'; $env:IWZ_TRAIN_CONSIST_END_X='2540'; $env:IWZ_TRAIN_TRACK_EAST_X='2848'; $env:IWZ_TRAIN_CAR_BOXES="$($TP[0])\collision\iwz_t7e_subway_car_a.json"; $env:IWZ_TRAIN_PROPS=$(if($TrainSet -eq 'g27'){"$L\props_g27.json"}else{"$L\props_g27d.json"}) } else { Remove-Item Env:IWZ_TRAIN -ErrorAction SilentlyContinue; Remove-Item Env:IWZ_TRAIN_CAR_BOXES -ErrorAction SilentlyContinue; Remove-Item Env:IWZ_TRAIN_PROPS -ErrorAction SilentlyContinue }
# -NeutralProbes: the compiler replaces the template reflection probes by one constant-colour probe per lighting room
if($NeutralProbes){ $env:IWZ_PROBES='neutral'; if($ProbeScale){ $env:IWZ_PROBES_SCALE=$ProbeScale } else { Remove-Item Env:IWZ_PROBES_SCALE -ErrorAction SilentlyContinue } } else { Remove-Item Env:IWZ_PROBES -ErrorAction SilentlyContinue; Remove-Item Env:IWZ_PROBES_SCALE -ErrorAction SilentlyContinue }
$A=@{}
if($Audio){
  $env:IWZ_AUDIO='1'
  $A=@{AudioSdk="$S\audio"
       AudioBank="$RT\audio\build\src15"
       AudioModels="$RT\audio\build\src"}
}
# (g27) the generator reads the FX placement file too (fx-fixture / fx-source lint, leaks under drip FX)
if($Fx -and $FxTxt){ $env:IWZ_FX_TXT=$FxTxt } else { Remove-Item Env:IWZ_FX_TXT -ErrorAction SilentlyContinue }
python -I "$S\station_zero2.py" "$D\cp_zmb" $src | Select-Object -Last 1
if(-not $SkipPick){
  & "$S\build-sz2.ps1" -Src $src -UmOut $um -ZoneToolExe $Z -KeepSubmodels -CompileOnly
  python -I "$S\sz2_submodels.py" "$um.compile.log" "$S\sz2_submodels.json" "$D\cp_zmb\maps\cp\cp_zmb.d3dbsp.ents"
  python -I "$S\station_zero2.py" "$D\cp_zmb" $src | Select-Object -Last 1
}
python -I "$S\sz2_plan.py" $src | Select-Object -Last 1
# g25 gate: static art lint (fake objects, voids, trim aspect, anchors, intersections, tone, colour casts)
$AS="$RT\assets"
python -I "$S\sz2_artlint.py" $src --json "$L\artlint_$Tag.json" --catalog "$AS\catalog.json" --kit "$AS\kit\kit_final.json" | Select-Object -Last 1
if($LASTEXITCODE -ne 0){ throw "artlint failed: $L\artlint_$Tag.json" }
python -I "$S\sz2_seams.py" $src --json "$L\seams_$Tag.json" | Select-Object -Last 1
if($LASTEXITCODE -ne 0){ throw "seam check failed: $L\seams_$Tag.json" }
python -I "$S\sz2_navconn.py" $src --json "$L\navconn_$Tag.json" | Select-Object -Last 6
if($LASTEXITCODE -ne 0){ throw "nav connectivity failed: $L\navconn_$Tag.json" }
python -I "$S\sz2_flatness.py" $src | Select-Object -Last 1
if($LASTEXITCODE -ne 0){ throw "flatness failed" }
if($Audio){   # (g27) audio anchors (decor / light / interaction names) checked before the bake, not after it
  python -I "$S\audio\audio_layout.py" --layout "$src\layout.json" --spec "$S\audio\station_zero_audio_layout.json" --bank "$S\audio\station_zero_audio.json" --out "$L\audio_check_$Tag.gsc" --report "$L\audio_check_$Tag.json" | Select-Object -Last 1
  if($LASTEXITCODE -ne 0){ throw "audio layout anchors failed: $L\audio_check_$Tag.json" }
}
if($GateOnly){ Write-Output "gate-only: $src"; return }
$build=$src
if($ReuseBake){
  # the bake only depends on the render world: -BakeFrom <tag> reuses that tag's bake when the generated world.bin is
  # identical, overlaying every other generated file (entities, collision, nav, scripts) on the baked copy
  $build="$src`_lm"
  if($BakeFrom){
    $from="$L\src_$BakeFrom"
    # -BakeLoose (A/B builds only: a material swap, same geometry): the bake source's world.bin with renamed materials
    if(-not $BakeLoose -and (Get-FileHash "$from\world.bin").Hash -ne (Get-FileHash "$src\world.bin").Hash){ throw "render world differs from ${BakeFrom}: bake again" }
    if(Test-Path $build){ Remove-Item $build -Recurse -Force }
    Copy-Item "$from`_lm" $build -Recurse
    Get-ChildItem $src -File | Where-Object { $_.Name -notin @('world.bin','lighting.txt') } | ForEach-Object { Copy-Item $_.FullName (Join-Path $build $_.Name) -Force }
    # the baked world.bin carries the lightmap coordinates: an A/B material swap renames entries of its material table
    # (env IWZ_AB_MATSWAP 'w/old=w/new;...'), geometry and lightmap unchanged
    if($BakeLoose){ python -I "$L\tools\world_matswap.py" "$build\world.bin" $env:IWZ_AB_MATSWAP; if($LASTEXITCODE){ throw 'world_matswap failed' } }
    "bake reused from $BakeFrom"
  }
  if(!(Test-Path "$build\lightmap\secondary.dds")){ throw 'no bake to reuse' }
}
elseif($Bake){
  . (& "$S\scheduler.ps1")
  $lj="$L\lights_$Tag.json"
  & $PY -I "$B\layout_lights.py" $src $lj @($LightArgs -split ' ' | Where-Object { $_ })
  for($k=0;$k -lt 900;$k++){ try { $lease=Enter-IW7ResourceLease -Scope "$L\bake" -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner 'IWZ Station Zero level: light bake'; break } catch { if($_.Exception.Message -match 'busy|reserved|wait'){ Start-Sleep 15; continue }; throw } }
  try {
    $build="$src`_lm"
    if(Test-Path $build){ Remove-Item $build -Recurse -Force }
    & $PY -I "$B\lmbake.py" $src $lj $build --rays $Rays --bounces 3 --denoise 1 2>&1 | Select-Object -Last 8
  } finally { Exit-IW7ResourceLease -Token $lease.Token | Out-Null }
  if(!(Test-Path "$build\lightmap\secondary.dds")){ throw 'bake produced no lightmap' }
}
if($NavObstacles){ $A['NavObstacles']=$true }
# the P1 perk machines (build-sz2 default) need scenegen's relocated perk scriptables; the g27 generator output has none: not part of g27e
if(-not $WithP1){ $A['PerkMachines']=''; $A['DeadeyeKitDump']=''; $A['DeadeyeScriptable']='' }
if($Kit){
  $km=@((Get-Content "$src\layout.json" -Raw | ConvertFrom-Json).kit_models | Where-Object { -not $_.StartsWith('iwz_') })
  $KD="$RT\kitimport\ztwork\dump"
  $A['KitDumps']=@("cp_disco=$KD\cp_disco;$KD\techsets_cp_disco","cp_final=$KD\cp_final;$KD\techsets_cp_final")
  if($Train){
    # (g27) only the port models the generator places (layout decor): the unplaced v4 props stay out of the FF
    $placed=@((Get-Content "$src\layout.json" -Raw | ConvertFrom-Json).decor | ForEach-Object { $_.model } | Select-Object -Unique)
    foreach($p in $TP){ foreach($f in Get-ChildItem "$p\xmodel\*.xmb"){ if($placed -contains $f.BaseName){ $km+=('train:'+$f.BaseName) } } }
    $A['KitDumps']+=("train=$($TP -join ';')")
  }
  $km=$km -join ','
  $A['KitModels']=$km
  $A['KitReport']="$um.kit_import.json"
  "kit models: $km"
}
# -Fx: ambient FX (FX agent route, SDK fx\, merged 9db8e34): fx_place.py patches the level script of the build source
# with the FX module, foreign-zone effects go through build-sz2 -FxImport (dry run first: merged effect list + debris
# kit models). Placement file: fx\station_zero_fx_g25.txt (g25 coordinates).
if($Fx){
  if(-not $FxTxt){ $FxTxt="$S\fx\station_zero_fx_g25.txt" }
  $FD="$RT\fx\ztwork\dump\cp_disco"
  $KD2="$RT\kitimport\ztwork\dump"
  $LD2="$L\ztwork\dump"
  $imp=(python -I "$S\fx\fx_place.py" $FxTxt $build --list-imports | Select-Object -Last 1).Trim()
  $ncs=@('--ncs',"$D\cp_zmb\netconststrings\ncs_efx_level.json")
  # (g27d, FX agent codex/iwzmap-fx 05c57a7) self-lit "dark" variants named by the catalog: fx_variant.py writes them to
  # level\fxvariants\<Tag>, imported as zone iwzv (fx_place --list-imports lists the placed iwzv:... effects)
  $VR="$L\fxvariants\$Tag"; if(Test-Path $VR){ Remove-Item $VR -Recurse -Force }
  $vroots="$FD;$KD2\cp_disco;$LD2\techsets_cp_disco;$D\cp_zmb;$D\techsets_cp_zmb;$D\techsets_global_cp;$D\techsets_common_cp;$D\techsets_global;$D\techsets_common_mp;$D\techsets_global_mp"
  $fxcat=(Get-Content "$S\fx\fx_catalog.json" -Raw | ConvertFrom-Json).fx
  foreach($pv in $fxcat.PSObject.Properties){ if($pv.Value.variant -and ($imp -match [regex]::Escape(($pv.Value.variant.of -split '/')[-1] + $pv.Value.variant.suffix))){
    python -I "$S\fx\fx_variant.py" --dump $vroots --fx $pv.Value.variant.of --out $VR --tint $pv.Value.variant.tint --suffix $pv.Value.variant.suffix --techsets "$RT\fx\techsets_all.txt" --report "$VR.$($pv.Name).json" | Select-Object -Last 1
    if($LASTEXITCODE){ throw "fx_variant failed for $($pv.Name)" }
  } }
  $fxv="iwzv=$VR;$vroots"
  if($imp){
    $fxd="cp_disco=$FD;$KD2\cp_disco;$LD2\techsets_cp_disco"
    python -I "$S\fx\fx_import.py" "$L\ztwork" 'cp_iwz' --fx $imp --dump $fxd --dump $fxv --ncs-out "$L\ncs_$Tag.json" --report "$L\fx_import_dry_$Tag.json" --dry-run | Select-Object -Last 1
    $dry=Get-Content "$L\fx_import_dry_$Tag.json" -Raw | ConvertFrom-Json
    if(@($dry.missing).Count){ throw "fx_import dry run: missing $($dry.missing -join ', ')" }
    if(@($dry.kitModels).Count){ $A['KitModels']=((@($A['KitModels'] -split ',') + @($dry.kitModels)) | Where-Object { $_ } | Select-Object -Unique) -join ',' }
    $ncs=@('--ncs',"$L\ncs_$Tag.json")
    $A['FxImport']=$imp; $A['FxDumps']=@($fxd,$fxv); $A['FxReport']="$um.fx_import.json"
  }
  python -I "$S\fx\fx_place.py" $FxTxt $build @ncs --fixture-out "$build\fxproof.gsc" --manifest-out "$build\fx_manifest.json" | Select-Object -Last 3
  if($LASTEXITCODE){ throw 'fx_place failed' }
}
& "$S\build-sz2.ps1" -Src $build -UmOut $um -ZoneToolExe $Z -KeepSubmodels @A
(Get-FileHash "$um\cp_iwz.ff" -Algorithm SHA256).Hash
