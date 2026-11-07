param(
  [Parameter(Mandatory)][string]$Src,                                                                 # station_zero2.py output
  [Parameter(Mandatory)][string]$UmOut,                                                               # usermap dir to fill (cp_iwz.ff, .arena)
  [string]$Map='cp_iwz',
  [string]$Work='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level\ztwork',                     # own zonetool work dir (new-work.ps1 + zonetool\cp_zmb_tpl junction)
  [string]$ZoneToolExe='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-map\build\bin\x64\Release\zonetool.exe',
  [string]$TemplateDump='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump',
  [string]$Arena='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-release\cp_iwz-rc1\usermaps\cp_iwz\cp_iwz.arena',
  [int]$Tries=600,
  [switch]$KeepSubmodels,                                                                             # door blockers: zonetool codex/iwzmap-door-brushmodels
  [switch]$CompileOnly,
  [switch]$NavObstacles,                                                                              # IWZ_SUBMODEL_NAVOBST=keep (closed doors cut the navmesh)
  [string]$AudioSdk='',                                                                               # sdk codex/iwzmap-audio tools-source\iwzmap\audio: adds the audio module
  [string]$AudioBank='', [string]$AudioModels='')
# Station Zero v2 build: iwzcompile (generated tome) -> assemble (+ custom materials) -> buildzone, every zonetool run under
# the machine-wide resource lease (zt.ps1); waits and retries while another owner holds the heavy slot.
$ErrorActionPreference='Stop'
$S=$PSScriptRoot; $W=$Work; $D=$TemplateDump
function Invoke-Zt([string[]]$a,[int]$t){
  for($k=0;$k -lt $Tries;$k++){
    try { return (& "$S\zt.ps1" -Work $W -ZtArgs $a -TimeoutSec $t -Owner 'IWZ Station Zero v2 level build') }
    catch { if($_.Exception.Message -match 'Resource busy|Heavy job already reserved|busy|wait before heavy admission|wait for its owner'){ Start-Sleep 15; continue }; throw }
  }
  throw 'resource lease not obtained'
}
Copy-Item $ZoneToolExe "$W\zonetool.exe" -Force
if(Test-Path "$W\iwz_src"){ Remove-Item "$W\iwz_src" -Recurse -Force }
Copy-Item -Recurse $Src "$W\iwz_src"
if(Test-Path "$W\dump\$Map"){ Remove-Item -LiteralPath "$W\dump\$Map" -Recurse -Force }
$env:IWZ_GEN_TOME='1'; $env:IWZ_KEEP_ENTSHAPES='1'
if($KeepSubmodels){ $env:IWZ_KEEP_SUBMODELS='1'; $env:IWZ_TRIGGER_SHAPES='1' }
if($NavObstacles){ $env:IWZ_SUBMODEL_NAVOBST='keep' }
try { $c = Invoke-Zt @('-iwzcompile','cp_zmb_tpl','cp_zmb',$Map,"$W\iwz_src") 900 } finally { Remove-Item Env:IWZ_GEN_TOME,Env:IWZ_KEEP_ENTSHAPES,Env:IWZ_KEEP_SUBMODELS,Env:IWZ_TRIGGER_SHAPES,Env:IWZ_SUBMODEL_NAVOBST -ErrorAction SilentlyContinue }
$full = Get-ChildItem "$W\zt-*.out.log" | Sort-Object LastWriteTime | Select-Object -Last 1
if($full){ Copy-Item $full.FullName "$UmOut.compile.log" -Force -ErrorAction SilentlyContinue }
if(($c -join "`n") -notmatch 'iwzmap: wrote'){ $c | Select-Object -Last 25; throw 'iwzcompile failed' }
($c | Select-String 'iwzmap: wrote|relit|brush models|generated trigger|lightmap').Line | Select-Object -First 30
if($KeepSubmodels -and (Test-Path "$Src\plan.json")){
  # gate: compiled trigger volumes must be point-testable and hold their spawners / zone cells (volume_check.py,
  # volumes agent, SDK codex/iwzmap-volumes 12f2f8f)
  python -I "$S\volume_check.py" "$W\dump\$Map\maps\cp" $Map --plan "$Src\plan.json" --require-spawners --gap-regions 'portal:a_tunnel_platform_b,portal:d_hall_stair_a,portal:d_platform_tunnel,portal:d_platform_corridor' --json "$UmOut.volume_check.json" | Select-Object -Last 4
  if($LASTEXITCODE){ throw 'volume_check failed' }
}
if($CompileOnly){ return }
if(Test-Path "$W\zonetool\$Map"){ Remove-Item -LiteralPath "$W\zonetool\$Map" -Recurse -Force }
python -I "$S\assemble.py" $W $Map "$Src\cp_iwz.gsc" "$D\patch_cp_zmb" "$D\techsets_cp_zmb" "$D\techsets_global_cp" "$D\techsets_global" "$D\cp_zmb" | Select-Object -Last 3
if($LASTEXITCODE){ throw 'assemble failed' }
python -I "$S\sz2_assemble.py" $W $Map $Src
if($LASTEXITCODE){ throw 'sz2_assemble failed' }
if($AudioSdk){
  # audio module (audio agent): placement script from this layout, bank + teddy model + scripts into the zone
  python -I "$AudioSdk\audio_layout.py" --layout "$Src\layout.json" --spec "$AudioSdk\station_zero_audio_layout.json" --bank "$AudioSdk\station_zero_audio.json" --out "$W\cp_iwz_audio_layout.gsc" --report "$UmOut.audio_positions.json"
  if($LASTEXITCODE){ throw 'audio_layout failed' }
  $aa=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--layout-gsc',"$W\cp_iwz_audio_layout.gsc")
  if($AudioBank){ $aa+=@('--bank-root',$AudioBank) }; if($AudioModels){ $aa+=@('--model-root',$AudioModels) }
  python -I "$AudioSdk\add_audio.py" @aa
  if($LASTEXITCODE){ throw 'add_audio failed' }
}
$null = New-Item -ItemType Directory -Force "$W\zonetool\$Map\techsets\ps"
if(!(Test-Path "$W\zonetool\$Map\techsets\ps\null.hlsl.cso")){ [IO.File]::WriteAllBytes("$W\zonetool\$Map\techsets\ps\null.hlsl.cso",[byte[]]@()) }
$csv="$W\zone_source\$Map.csv"; $lines=Get-Content $csv
$req=@('techsets_common','techsets_global','techsets_common_core_mp','techsets_global_core_mp','techsets_common_mp','techsets_global_mp','techsets_common_cp','techsets_global_cp','techsets_cp_zmb')|ForEach-Object {"require,$_"}
Set-Content $csv (@($lines[0])+$req+$lines[1..($lines.Count-1)]) -Encoding ascii
if(Test-Path "$W\zone\$Map.ff"){ Remove-Item "$W\zone\$Map.ff" }
$b = Invoke-Zt @('-buildzone',$Map) 2400
$b | Select-String -Pattern 'FATAL|TIMEOUT|ERROR|Successfully compiled' | Select-Object -First 15
if(!(Test-Path "$W\zone\$Map.ff")){ $b | Select-Object -Last 30; throw 'buildzone produced no fastfile' }
New-Item -ItemType Directory $UmOut -Force | Out-Null
Copy-Item "$W\zone\$Map.ff" "$UmOut\$Map.ff" -Force
if($Arena -and (Test-Path $Arena)){ Copy-Item $Arena "$UmOut\$Map.arena" -Force }
"built $UmOut\$Map.ff $((Get-Item "$UmOut\$Map.ff").Length) bytes"
