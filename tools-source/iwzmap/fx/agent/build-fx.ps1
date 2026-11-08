param([Parameter(Mandatory)][string]$Tag,                 # output fx\src_<Tag>, fx\um_<Tag>
      [string]$Base='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\src_g24_lm',   # baked level source (copy of g24)
      [string]$FxTxt='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\layout\station_zero_fx.txt',
      [string]$NcsSkip='',                                  # experiment: imported effects left out of the level effect list
      [switch]$NoFx,
      [switch]$ReuseCompile)                                # keep ztwork\dump\cp_iwz from the previous build (same world)
# FX build of Station Zero: copy of the baked g24 source -> fx_place.py (level FX module + proof fixture) -> build-sz2.ps1
# with the g24 flags (kit, audio, kept sub-models, nav obstacles) in the FX agent's own zonetool work dir, plus
# fx_import.py for the foreign-zone effects fx.txt uses (their debris models go through kit_import.py).
$ErrorActionPreference='Stop'
$F='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx'
$S='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-fx\tools-source\iwzmap'
$Z='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-doors\build\bin\x64\Release\zonetool.exe'
$D='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump'
$KD='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\kitimport\ztwork\dump'
$LD='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level\ztwork\dump'
$W="$F\ztwork"
$src="$F\src_$Tag"; $um="$F\um_$Tag"
if(Test-Path $src){ Remove-Item $src -Recurse -Force }
Copy-Item $Base $src -Recurse
$km=@((Get-Content "$src\layout.json" -Raw | ConvertFrom-Json).kit_models)
$A=@{AudioSdk='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-audio\tools-source\iwzmap\audio'
     AudioBank='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src10'
     AudioModels='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\audio\build\src'
     KitDumps=@("cp_disco=$KD\cp_disco;$LD\techsets_cp_disco","cp_final=$KD\cp_final;$LD\techsets_cp_final"); KitReport="$um.kit_import.json"
     NavObstacles=$true}
if(-not $NoFx){
  $imp=(python -I "$S\fx\fx_place.py" $FxTxt $src --list-imports | Select-Object -Last 1).Trim()
  $ncs=@('--ncs',"$D\cp_zmb\netconststrings\ncs_efx_level.json")
  if($imp){
    # dry run against the level's last assembled zone: the merged effect list for fx_place and the debris models
    $da=@("$S\fx\fx_import.py","C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level\ztwork",'cp_iwz','--fx',$imp,'--dump',"cp_disco=$W\dump\cp_disco;$KD\cp_disco;$LD\techsets_cp_disco",'--ncs-out',"$F\ncs_$Tag.json",'--report',"$F\import_dry_$Tag.json",'--dry-run')
    if($NcsSkip){ $da+=@('--ncs-skip',$NcsSkip) }
    python -I @da | Select-Object -Last 1
    $dry=Get-Content "$F\import_dry_$Tag.json" -Raw | ConvertFrom-Json
    if(@($dry.missing).Count){ throw "fx_import dry run: missing $($dry.missing -join ', ')" }
    $km+=@($dry.kitModels)
    $ncs=@('--ncs',"$F\ncs_$Tag.json")
    $A['FxImport']=$imp; $A['FxDumps']=@("cp_disco=$W\dump\cp_disco;$KD\cp_disco;$LD\techsets_cp_disco"); $A['FxReport']="$um.fx_import.json"
    if($NcsSkip){ $A['FxNcsSkip']=$NcsSkip }
  }
  $pa=@("$S\fx\fx_place.py",$FxTxt,$src)+$ncs+@('--fixture-out',"$src\fxproof.gsc",'--manifest-out',"$src\fx_manifest.json")
  if($NcsSkip){ $pa+=@('--allow-unlisted',$NcsSkip) }
  python -I @pa
  if($LASTEXITCODE){ throw 'fx_place failed' }
}
$A['KitModels']=($km | Select-Object -Unique) -join ','
"kit models: $($A['KitModels'])"
if($ReuseCompile){ $A['ReuseCompile']=$true }
&"$S\build-sz2.ps1" -Src $src -UmOut $um -Work $W -ZoneToolExe $Z -KeepSubmodels @A
(Get-FileHash "$um\cp_iwz.ff" -Algorithm SHA256).Hash
