param([Parameter(Mandatory)][string]$Tag,                  # output fx\src_<Tag>, fx\um_<Tag>
      [string]$Base='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\darkness\src_d12_lm',   # darkness d12 baked source (read only)
      [string]$FxTxt='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\layout\station_zero_fx_dark.txt',
      [string]$FlBright='2.0', [switch]$ReuseCompile,
      [string]$Ladder='0.5,4')                              # extra tints of every variant (imported for probes, not placed)
# FX agent build on the darkness agent's d12 source: same world, bake, darkness modules (SDK 3d7ed90 detached worktree
# sdk-fx-d12, darkness zonetool), flashlight effects regenerated with the d12 parameters into fx\vfxsrc-d, and the FX
# agent's dark-state fx.txt with self-lit variants (fx_variant.py -> fx\variants\<Tag>, imported as zone iwzv).
# Never writes darkness\ or level\ (reads src_d12_lm, kit/train dumps, the darkness zonetool exe).
$ErrorActionPreference='Stop'
$F='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx'
$DK='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\darkness'
$L='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level'
$S='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-fx-d12\tools-source\iwzmap'          # d12 SDK (build-sz2, darkness)
$FXS='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-fx\tools-source\iwzmap\fx'  # FX agent tools (fx_place, fx_variant, module)
$PY='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\lightmaps\venv\Scripts\python.exe'
$Z='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-darkness\build\bin\x64\Release\zonetool.exe'
$D='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump'
$KD='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\kitimport\ztwork\dump'
$LD2="$L\ztwork\dump"
$FD="$F\ztwork\dump"
$W="$F\ztwork-d"
if(!(Test-Path "$W\zonetool.exe")){
  & "$S\new-work.ps1" -Work $W -ZoneTool $Z | Out-Null
  New-Item -ItemType Directory -Force "$W\zonetool" | Out-Null
  New-Item -ItemType Junction -Path "$W\zonetool\cp_zmb_tpl" -Target "$D\cp_zmb" | Out-Null
}
$src="$F\src_$Tag"; $um="$F\um_$Tag"
if(Test-Path $src){ Remove-Item $src -Recurse -Force }
Copy-Item $Base $src -Recurse
# the d12 FX module is replaced by the FX agent's current one (bank sync, stages)
Copy-Item "$FXS\iwz_fx.gsc" "$W\iwz_fx_module_used.gsc" -Force
# flashlight effects with the d12 parameters (darkness build-g-dark.ps1: fov 32, inner 12, radius 900, life 100000)
$V="$F\vfxsrc-d"; if(Test-Path $V){ Remove-Item $V -Recurse -Force }
$TL="$FD\cp_disco\particlesystem\vfx\iw7\levels\cp_disco\subway_train\vfx_train_front_light_ch.iw7VFX"
$fxMine=@()
foreach($sfx in '','_b','_c','_d','_e','_f'){
  & $PY -I "$S\darkness\make_vfx_light.py" $TL $V "vfx/iwz/vfx_iwz_flashlight_world$sfx" --fov 32 --inner 12 --radius 900 --color 1,0.92,0.80 --brightness $FlBright --shadow 1 --near 8 --life 100000 | Out-Null
  $fxMine+="iwz:vfx/iwz/vfx_iwz_flashlight_world$sfx"
}
$litB=[string]([math]::Round([double]$FlBright*0.3,2))
& $PY -I "$S\darkness\make_vfx_light.py" $TL $V "vfx/iwz/vfx_iwz_flashlight_lit" --fov 32 --inner 12 --radius 900 --color 1,0.92,0.80 --brightness $litB --shadow 1 --near 8 --life 100000 | Out-Null
$fxMine+="iwz:vfx/iwz/vfx_iwz_flashlight_lit"
# self-lit variants named by the catalog (entries with "variant")
$cat=(Get-Content "$FXS\fx_catalog.json" -Raw | ConvertFrom-Json).fx
$VR="$F\variants\$Tag"; if(Test-Path $VR){ Remove-Item $VR -Recurse -Force }
$roots="$FD\cp_disco;$KD\cp_disco;$LD2\techsets_cp_disco;$D\cp_zmb;$D\techsets_cp_zmb;$D\techsets_global_cp;$D\techsets_common_cp;$D\techsets_global;$D\techsets_common_mp;$D\techsets_global_mp"
# the placed tint (catalog) plus a ladder of other tints (imported for the probes, not placed): the dark vision is
# manual exposure -3 (x1/8), so a self-lit sprite needs a tint near or above 1 to read
$ladderFx=@()
foreach($p in $cat.PSObject.Properties){ if($p.Value.variant){
  $tints=@([string]$p.Value.variant.tint) + ($Ladder -split ',' | Where-Object { $_ })
  foreach($t in ($tints | Select-Object -Unique)){
    $sfx='_d'+[string][int][math]::Round([double]$t*10)
    python -I "$FXS\fx_variant.py" --dump $roots --fx $p.Value.variant.of --out $VR --tint $t --suffix $sfx --techsets "$F\techsets_all.txt" --report "$VR.$($p.Name)$sfx.json" | Select-Object -First 1
    if($LASTEXITCODE){ throw "fx_variant failed for $($p.Name)" }
    $ladderFx+=('iwzv:vfx/iwz/amb/'+($p.Value.variant.of -split '/')[-1]+$sfx)
  }
} }
$A=@{KeepSubmodels=$true; NavObstacles=$true; Darkness=$true; FxReport="$um.fx_import.json"
     AudioSdk="$S\audio"; AudioBank='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src15'; AudioModels='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src'}
$A['DarkArgs']="--dark tonemapAuto=0;tonemapAdaptSpeed=1;tonemapExposureAdjust=-3 --lit fogMaxOpacity=0.03;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0"
if($ReuseCompile){ $A['ReuseCompile']=$true }
$TP=@("$DK\..\train\port\banzai_v3","$DK\..\train\port\kit_v4","$DK\..\train\port\genset","$DK\..\train\port\props_v4") | ForEach-Object { [IO.Path]::GetFullPath($_) }
$km=@((Get-Content "$src\layout.json" -Raw | ConvertFrom-Json).kit_models | Where-Object { -not $_.StartsWith('iwz_') })
$A['KitDumps']=@("cp_disco=$KD\cp_disco;$KD\techsets_cp_disco","cp_final=$KD\cp_final;$KD\techsets_cp_final")
foreach($p in $TP){ foreach($xf in Get-ChildItem "$p\xmodel\*.xmb"){ $km+=('train:'+$xf.BaseName) } }   # not $f: PowerShell names are case-insensitive ($F)
$A['KitDumps']+=("train=$($TP -join ';')")
$A['KitModels']=''
$A['KitReport']="$um.kit_import.json"
$fxd="cp_disco=$FD\cp_disco;$KD\cp_disco;$LD2\techsets_cp_disco"
$fxv="iwzv=$VR;$roots"
$imp=(python -I "$FXS\fx_place.py" $FxTxt $src --list-imports | Select-Object -Last 1).Trim()
python -I "$S\fx\fx_import.py" "$L\ztwork" 'cp_iwz' --fx $imp --dump $fxd --dump $fxv --ncs-out "$F\ncs_$Tag.json" --report "$F\fx_import_dry_$Tag.json" --dry-run | Select-Object -Last 1
$dry=Get-Content "$F\fx_import_dry_$Tag.json" -Raw | ConvertFrom-Json
if(@($dry.missing).Count){ throw "fx_import dry run: $($dry.missing -join ', ')" }
if(@($dry.kitModels).Count){ $km+=@($dry.kitModels) }
python -I "$FXS\fx_place.py" $FxTxt $src --ncs "$F\ncs_$Tag.json" --fixture-out "$src\fxproof.gsc" --manifest-out "$src\fx_manifest.json"
if($LASTEXITCODE){ throw 'fx_place failed' }
$A['FxImport']=((@($imp) + $fxMine + $ladderFx) | Where-Object { $_ } | Select-Object -Unique) -join ','
$A['FxDumps']=@($fxd,"iwz=$V",$fxv)
$A['KitModels']=($km | Select-Object -Unique) -join ','
& "$S\build-sz2.ps1" -Src $src -UmOut $um -Work $W -ZoneToolExe $Z @A
(Get-FileHash "$um\cp_iwz.ff" -Algorithm SHA256).Hash
