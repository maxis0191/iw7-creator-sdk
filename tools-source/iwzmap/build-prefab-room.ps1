param(
  [Parameter(Mandatory)][string]$Src,            # prefab_room.py output (world.bin, colmap.hkx, ..., <map>.gsc, <map>.arena)
  [Parameter(Mandatory)][string]$UmOut,          # usermap folder to fill (<map>.ff, <map>.arena)
  [Parameter(Mandatory)][string]$Work,           # own ZoneTool work folder (new-work-from-stock.ps1)
  [Parameter(Mandatory)][string]$ZoneToolExe,    # zonetool.exe with -iwzcompile
  [Parameter(Mandatory)][string]$TemplateDump,   # folder of stock dumps: cp_zmb, patch_cp_zmb, techsets_cp_zmb, techsets_global_cp, techsets_global
  [string]$Map='cp_pfr',
  [string]$Scheduler=$env:IW7_RESOURCE_SCHEDULER,
  [string]$Probes='',                            # 'neutral': every lighting.txt room gets a plain reflection probe (IWZ_PROBES)
  [ValidateRange(0,14400)][int]$WaitForSlotSeconds=3600,
  [string]$Owner='IWZ prefab room build',
  [string]$ZoneBuildExe='',                      # another zonetool.exe for the zone step (default: the same binary)
  [string]$KitModels='',                         # kit_import.py: models of other zones or authored ports 'a,b' (or 'zone:name'); smodels.txt may place them
  [string[]]$KitDumps=@(),                       # '<zone>=<dump root>;<techsets dump root>' (README, kit import)
  [string]$KitReport='',
  [switch]$ReuseCompile,                         # keep the compile output already in <work>\dump\<map> (same -Src)
  [switch]$CompileOnly)
# Prefab Room build: iwzcompile (generated visibility tome) -> assemble -> zone check -> buildzone. Every ZoneTool run takes
# the machine-wide build reservation through zt.ps1 (which waits for it; nothing is retried). Times go to <UmOut>.build.json.
$ErrorActionPreference='Stop'
$S=$PSScriptRoot; $W=(Resolve-Path -LiteralPath $Work).Path; $D=(Resolve-Path -LiteralPath $TemplateDump).Path
$times=[ordered]@{}; $t0=Get-Date
function Zt([string[]]$a,[int]$t){ & "$S\zt.ps1" -Work $W -ZtArgs $a -TimeoutSec $t -Owner $Owner -Scheduler $Scheduler -WaitForSlotSeconds $WaitForSlotSeconds }
Copy-Item -LiteralPath $ZoneToolExe -Destination "$W\zonetool.exe" -Force
if($ReuseCompile -and (Test-Path "$W\dump\$Map\maps\cp\$Map.d3dbsp.ents")){ "reusing the compile output in $W\dump\$Map" } else {
if(Test-Path "$W\iwz_src"){ Remove-Item "$W\iwz_src" -Recurse -Force }
Copy-Item -Recurse $Src "$W\iwz_src"
if(Test-Path "$W\dump\$Map"){ Remove-Item -LiteralPath "$W\dump\$Map" -Recurse -Force }
if($KitModels){
  # kit models placed as static models: the compiler reads their .xmb from <source>\xmodel (x64-zt iwzmap read_smodels)
  $ka=@($W,$Map,'--models',$KitModels,'--stage-xmodels',"$W\iwz_src"); foreach($kd in $KitDumps){ $ka+=@('--dump',$kd) }
  python -I "$S\kit_import.py" @ka
  if($LASTEXITCODE){ throw 'kit_import --stage-xmodels failed' }
}
$env:IWZ_GEN_TOME='1'; $env:IWZ_KEEP_ENTSHAPES='1'
if($Probes){ $env:IWZ_PROBES=$Probes }
$t=Get-Date
try { $c = Zt @('-iwzcompile','cp_zmb_tpl','cp_zmb',$Map,"$W\iwz_src") 900 } finally { Remove-Item Env:IWZ_GEN_TOME,Env:IWZ_KEEP_ENTSHAPES,Env:IWZ_PROBES -ErrorAction SilentlyContinue }
$times.compile=[int]((Get-Date)-$t).TotalSeconds
$full = Get-ChildItem "$W\zt-*.out.log" | Sort-Object LastWriteTime | Select-Object -Last 1
if($full){ Copy-Item $full.FullName "$UmOut.compile.log" -Force -ErrorAction SilentlyContinue }
if(($c -join "`n") -notmatch 'iwzmap: wrote'){ $c | Select-Object -Last 25; throw 'iwzcompile failed' }
($c | Select-String 'iwzmap: wrote|static models|no template instance|IWZ_SMODEL_DONOR|Umbra tome|not in the template|not used by the template').Line | Select-Object -First 12
}
if($CompileOnly){ return }
if($ZoneBuildExe){ Copy-Item -LiteralPath $ZoneBuildExe -Destination "$W\zonetool.exe" -Force }
$t=Get-Date
if(Test-Path "$W\zonetool\$Map"){ Remove-Item -LiteralPath "$W\zonetool\$Map" -Recurse -Force }
python -I "$S\assemble.py" $W $Map "$Src\$Map.gsc" "$D\patch_cp_zmb" "$D\techsets_cp_zmb" "$D\techsets_global_cp" "$D\techsets_global" "$D\cp_zmb" | Select-Object -Last 2
if($LASTEXITCODE){ throw 'assemble failed' }
if($KitModels){
  # the kit models themselves into the zone (geometry, materials, image headers, techsets the template lacks)
  $ka=@($W,$Map,'--models',$KitModels); foreach($kd in $KitDumps){ $ka+=@('--dump',$kd) }
  if($KitReport){ $ka+=@('--report',$KitReport) }
  foreach($td in [IO.Directory]::GetDirectories($D,'techsets_*')){ $rcsv=Join-Path $td ((Split-Path $td -Leaf)+".csv"); if(Test-Path $rcsv){ $ka+=@('--runtime-csv',$rcsv) } }
  python -I "$S\kit_import.py" @ka
  if($LASTEXITCODE){ throw 'kit_import failed' }
}
$null = New-Item -ItemType Directory -Force "$W\zonetool\$Map\techsets\ps"
if(!(Test-Path "$W\zonetool\$Map\techsets\ps\null.hlsl.cso")){ [IO.File]::WriteAllBytes("$W\zonetool\$Map\techsets\ps\null.hlsl.cso",[byte[]]@()) }
$csv="$W\zone_source\$Map.csv"; $lines=Get-Content $csv
$req=@('techsets_common','techsets_global','techsets_common_core_mp','techsets_global_core_mp','techsets_common_mp','techsets_global_mp','techsets_common_cp','techsets_global_cp','techsets_cp_zmb')|ForEach-Object {"require,$_"}
Set-Content $csv (@($lines[0])+$req+$lines[1..($lines.Count-1)]) -Encoding ascii
$times.assemble=[int]((Get-Date)-$t).TotalSeconds
foreach($ext in 'ff','sabl','sabs'){ if(Test-Path "$W\zone\$Map.$ext"){ Remove-Item "$W\zone\$Map.$ext" } }
$t=Get-Date
$b = Zt @('-buildzone',$Map) 2400
$times.zone=[int]((Get-Date)-$t).TotalSeconds
$b | Select-String -Pattern 'FATAL|TIMEOUT|Successfully compiled' | Select-Object -First 6
if(!(Test-Path "$W\zone\$Map.ff")){ $b | Select-Object -Last 30; throw 'buildzone produced no fastfile' }
New-Item -ItemType Directory $UmOut -Force | Out-Null
Copy-Item "$W\zone\$Map.ff" "$UmOut\$Map.ff" -Force
if(Test-Path "$Src\$Map.arena"){ Copy-Item "$Src\$Map.arena" "$UmOut\$Map.arena" -Force }
$times.total=[int]((Get-Date)-$t0).TotalSeconds
[ordered]@{map=$Map;ff_bytes=(Get-Item "$UmOut\$Map.ff").Length;seconds=$times;zonetool=$ZoneToolExe;zone_build_zonetool=$(if($ZoneBuildExe){$ZoneBuildExe}else{$ZoneToolExe});probes=$Probes} | ConvertTo-Json | Set-Content "$UmOut.build.json"
"built $UmOut\$Map.ff $((Get-Item "$UmOut\$Map.ff").Length) bytes in $($times.total) s (compile $($times.compile), assemble $($times.assemble), zone $($times.zone))"
