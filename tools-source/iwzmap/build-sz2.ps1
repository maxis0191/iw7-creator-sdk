param(
  [Parameter(Mandatory)][string]$Src,                                                                 # station_zero2.py output
  [Parameter(Mandatory)][string]$UmOut,                                                               # usermap dir to fill (cp_iwz.ff, .arena)
  [string]$Map='cp_iwz',
  [string]$Work=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level\ztwork'),                     # own zonetool work dir (new-work.ps1 + zonetool\cp_zmb_tpl junction)
  [string]$ZoneToolExe=(& "$PSScriptRoot\machine.ps1" ZoneToolExe 'x64-zt-iwz-map'),
  [string]$TemplateDump=(& "$PSScriptRoot\machine.ps1" TemplateDump),
  [string]$Arena=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-release\cp_iwz-rc1\usermaps\cp_iwz\cp_iwz.arena'),
  [int]$Tries=600,
  [switch]$KeepSubmodels,                                                                             # door blockers: zonetool codex/iwzmap-door-brushmodels
  [switch]$CompileOnly,
  [switch]$NavObstacles,                                                                              # IWZ_SUBMODEL_NAVOBST=keep (closed doors cut the navmesh)
  [string]$AudioSdk='',                                                                               # sdk codex/iwzmap-audio tools-source\iwzmap\audio: adds the audio module
  [string]$AudioBank='', [string]$AudioModels='',
  [string]$KitModels='',                                                                              # kit_import.py: foreign-zone xmodels 'a,b,c' (or 'zone:name')
  [string]$KitJson='', [string]$KitTier='', [string]$KitZones='',                                     # or rows of a kit_final.json (filtered by tier / source zones)
  [string[]]$KitDumps=@(),                                                                            # '<zone>=<dump root>;<techsets dump root>' (zonetool -dumpzonetypes <zone> xmodel,xmodelsurfs,material,image,physicsasset,physicsfxshape; zonetool -dumpzone techsets_<zone>)
  [string[]]$KitRuntimeCsv=@(),                                                                       # extra csvs of runtime techset zones (techsets_common)
  [string]$KitReport='',
  [string]$FxImport='',                                                                               # fx\fx_import.py: foreign-zone vfx '<zone>:<vfx>,...'
  [string[]]$FxDumps=@(),                                                                             # '<zone>=<vfx dump root>;<kit dump root>;<techsets dump root>'
  [string]$FxReport='',
  [switch]$Darkness, [string]$DarkArgs='',                                                         # (DarkArgs: add_darkness options, e.g. "--dark-exposure 8 --exposures 4,6")                                                                                  # darkness\add_darkness.py: darkness + flashlight modules (generator IWZ_DARK=1)
  [string]$FxNcsSkip='',                                                                             # experiment: imported effects left out of the level effect list
  [switch]$ReuseCompile,                                                                             # keep the previous iwzcompile output of the same -Src (dump\<map>)
  [string]$DeadeyeImage=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\assets\dumps\cp_disco\images\cp_zmb_perk_icon_deadeye.iw7Image'),  # P1: Deadeye Dewdrops' HUD icon (not in the template zone)
  [string]$PerkMachines=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level\p1\machines\port'),       # P1: the four authored perk machines (perks\machines\README.md)
  [string]$DeadeyeKitDump=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\kitimport\ztwork\dump'),        # P1: cp_disco dump with Deadeye's machine (models, scriptable)
  [string]$DeadeyeScriptable=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level\ztwork-p1\dump\cp_disco\scriptable\zm_perk_machine_deadeye_sign'),  # P1: zonetool -dumpzonetypes cp_disco scriptable
  [switch]$Incremental)                                                                              # keep the stock links and the module outputs of the previous assembly (same modules and dumps)
# Station Zero v2 build: iwzcompile (generated tome) -> assemble (+ custom materials) -> buildzone, every zonetool run under
# the machine-wide resource lease (zt.ps1); waits and retries while another owner holds the heavy slot.
$ErrorActionPreference='Stop'
$S=$PSScriptRoot; $W=$Work; $D=$TemplateDump
# P1 perk machines, always part of the map: the four authored machines and Deadeye's own cp_disco machine (its two models
# here; its scriptable by perks\add_deadeye_machine.py after the kit import)
$perkKit=@()
if($PerkMachines -and (Test-Path $PerkMachines)){ $perkKit+='perks:iwz_perk_machine_bakers,perks:iwz_perk_machine_voyage,perks:iwz_perk_machine_grudge,perks:iwz_perk_machine_double'; $KitDumps=@($KitDumps)+"perks=$PerkMachines" }
if($DeadeyeKitDump -and (Test-Path "$DeadeyeKitDump\cp_disco\xmodel")){ $perkKit+='cp_disco:cp_disco_perk_dewdrops,cp_disco:cp_disco_perk_dewdrops_off'; $KitDumps=@($KitDumps)+"cp_disco=$DeadeyeKitDump\cp_disco;$DeadeyeKitDump\techsets_cp_disco" }
if($perkKit.Count){ $KitModels=((@($KitModels)+$perkKit) | Where-Object { $_ }) -join ',' }
$times=[ordered]@{}; $t0=Get-Date; $tp=Get-Date
function Lap([string]$Name){ $script:times[$Name]=[int]((Get-Date)-$script:tp).TotalSeconds; $script:tp=Get-Date }
function Invoke-Zt([string[]]$a,[int]$t){
  for($k=0;$k -lt $Tries;$k++){
    try { return (& "$S\zt.ps1" -Work $W -ZtArgs $a -TimeoutSec $t -HeldLease $script:held -Owner $(if($env:IWZ_BUILD_OWNER){$env:IWZ_BUILD_OWNER}else{'IWZ Station Zero v2 level build'})) }
    catch { if($_.Exception.Message -match 'Resource busy|Heavy job already reserved|busy|wait before heavy admission|wait for its owner'){ Start-Sleep 15; continue }; throw }
  }
  throw 'resource lease not obtained'
}
Copy-Item $ZoneToolExe "$W\zonetool.exe" -Force
# One build reservation for the whole build (compile, assembly, zone). Each ZoneTool run used to take its own, so the
# zone step went back to the end of the machine's waiting order after the compile: W2 build b waited 1,721 s for the
# compile and 2,371 s for the zone (4,573 s of wall time for about 7 minutes of work). The assembly between them is
# held too: about 1 s incremental, 5 to 8 minutes for a full one.
. (& "$S\scheduler.ps1" '')
$held=$null; $heldClock=[Diagnostics.Stopwatch]::StartNew()
$ownerName=if($env:IWZ_BUILD_OWNER){$env:IWZ_BUILD_OWNER}else{'IWZ Station Zero v2 level build'}
while(-not $held){
  try{ $held=Enter-IW7ResourceLease -Scope $W -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner $ownerName }
  catch{
    $busy=if(Get-Command Test-IW7RetryableRefusal -ErrorAction SilentlyContinue){ (Test-IW7RetryableRefusal $_.Exception.Message) -or $_.Exception.Message -like 'Resource admission lock busy*' }else{ $_.Exception.Message -match 'Resource busy|busy' }
    if(!$busy -or $heldClock.Elapsed.TotalSeconds -gt $Tries*15){ throw }
    Start-Sleep -Seconds 5
  }
}
"waited for the build reservation $([int]$heldClock.Elapsed.TotalSeconds) s (held for compile, assembly and zone)"
try {
if($ReuseCompile -and (Test-Path "$W\dump\$Map\maps\cp\$Map.d3dbsp.ents")){ "reusing compiled $W\dump\$Map" } else {
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
}
if($KeepSubmodels -and (Test-Path "$Src\plan.json")){
  # gate: compiled trigger volumes must be point-testable and hold their spawners / zone cells (volume_check.py,
  # volumes agent, SDK codex/iwzmap-volumes 12f2f8f)
  python -I "$S\volume_check.py" "$W\dump\$Map\maps\cp" $Map --plan "$Src\plan.json" --require-spawners --gap-regions 'portal:a_tunnel_platform_b,portal:d_hall_stair_a,portal:d_platform_tunnel,portal:d_platform_corridor' --layout "$Src\layout.json" --json "$UmOut.volume_check.json" | Select-Object -Last 4
  if($LASTEXITCODE){ throw 'volume_check failed' }
}
if($CompileOnly){ return }
Lap 'compile'
# -Incremental: the stock links and what the modules added stay when the modules ran with the same arguments last time
# (the key below); only the generated world is linked again and the modules run again over the kept tree.
$modKey=(@($D,$AudioSdk,$AudioBank,$AudioModels,$KitModels,$KitJson,$KitTier,$KitZones,($KitDumps -join '|'),($KitRuntimeCsv -join '|'),$FxImport,($FxDumps -join '|'),$FxNcsSkip,[string][bool]$Darkness,$DarkArgs,$DeadeyeScriptable) -join "`n")
$keyFile="$W\zonetool\$Map\.iwz_modules.key"
$inc=@()
if($Incremental -and (Test-Path -LiteralPath $keyFile) -and ((Get-Content -LiteralPath $keyFile -Raw) -eq $modKey)){ $inc=@('--incremental'); 'incremental assembly: same modules as the kept tree' }
elseif(Test-Path "$W\zonetool\$Map"){ if($Incremental){ 'incremental asked, but the modules or their arguments changed: assembling everything' }; Remove-Item -LiteralPath "$W\zonetool\$Map" -Recurse -Force }
python -I "$S\assemble.py" $W $Map "$Src\cp_iwz.gsc" "$D\patch_cp_zmb" "$D\techsets_cp_zmb" "$D\techsets_global_cp" "$D\techsets_global" "$D\cp_zmb" @inc | Select-Object -Last 3
if($LASTEXITCODE){ throw 'assemble failed' }
python -I "$S\sz2_assemble.py" $W $Map $Src
if($LASTEXITCODE){ throw 'sz2_assemble failed' }
# perks module (P1, perks\README.md): scripts, HUD icons, the bit table's new rows; always, the level script calls it
$pa=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--template-dump',$D)
if($DeadeyeImage -and (Test-Path $DeadeyeImage)){ $pa+=@('--deadeye-image',$DeadeyeImage) }
python -I "$S\perks\add_perks.py" @pa
if($LASTEXITCODE){ throw 'add_perks failed' }
if($AudioSdk){
  # audio module (audio agent): placement script from this layout, bank + teddy model + scripts into the zone
  python -I "$AudioSdk\audio_layout.py" --layout "$Src\layout.json" --spec "$AudioSdk\station_zero_audio_layout.json" --bank "$AudioSdk\station_zero_audio.json" --out "$W\cp_iwz_audio_layout.gsc" --report "$UmOut.audio_positions.json"
  if($LASTEXITCODE){ throw 'audio_layout failed' }
  $aa=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--layout-gsc',"$W\cp_iwz_audio_layout.gsc")
  if($AudioBank){ $aa+=@('--bank-root',$AudioBank) }; if($AudioModels){ $aa+=@('--model-root',$AudioModels) }
  python -I "$AudioSdk\add_audio.py" @aa
  if($LASTEXITCODE){ throw 'add_audio failed' }
}
if($KitModels -or $KitJson){
  # foreign-zone kit models (cp_disco, cp_final, ...): link their dumps (models, materials, image headers, missing techsets), add xmodel rows
  $ka=@($W,$Map); foreach($kd in $KitDumps){ $ka+=@("--dump",$kd) }
  if($KitModels){ $ka+=@('--models',$KitModels) }
  if($KitJson){ $ka+=@('--kit',$KitJson); if($KitTier){ $ka+=@('--tier',$KitTier) }; if($KitZones){ $ka+=@('--zones',$KitZones) } }
  if($KitReport){ $ka+=@('--report',$KitReport) }
  # techsets/shaders the template map's techset zones define at runtime: referenced, not embedded again
  foreach($td in [IO.Directory]::GetDirectories($D,'techsets_*')){ $rcsv=Join-Path $td ((Split-Path $td -Leaf)+".csv"); if(Test-Path $rcsv){ $ka+=@("--runtime-csv",$rcsv) } }
  # optional extra runtime csvs (techsets_common cannot be dumped: ZoneTool loads it at startup)
  foreach($rcsv in @($KitRuntimeCsv)){ if($rcsv -and (Test-Path $rcsv)){ $ka+=@("--runtime-csv",$rcsv) } }
  python -I "$S\kit_import.py" @ka
  if($LASTEXITCODE){ throw 'kit_import failed' }
}
$deScr=$DeadeyeScriptable
if($deScr -and (Test-Path $deScr)){
  # P1: Deadeye Dewdrops' own machine (cp_disco scriptable) on the spare template perk scriptable scenegen relocated
  python -I "$S\perks\add_deadeye_machine.py" "$W\zone_source\$Map.csv" "$W\zonetool\$Map" $Map --scriptable $deScr --report "$UmOut.deadeye.json"
  if($LASTEXITCODE){ throw 'add_deadeye_machine failed' }
}
if($Darkness){
  # darkness module + weapon flashlight (darkness agent): rawfiles after the level script row
  python -I "$S\darkness\add_darkness.py" "$W\zone_source\$Map.csv" "$W\zonetool\$Map" $Map @($DarkArgs -split ' ' | Where-Object { $_ })
  if($LASTEXITCODE){ throw 'add_darkness failed' }
}
if($FxImport){
  # foreign-zone effects: link the vfx + children + materials/images/techsets, add vfx rows, append the names to the
  # level effect list (netconststrings/ncs_efx_level.json): IW7 registers effects only through that list
  $fa=@($W,$Map,'--fx',$FxImport); foreach($fd in $FxDumps){ $fa+=@('--dump',$fd) }
  foreach($td in [IO.Directory]::GetDirectories($D,'techsets_*')){ $rcsv=Join-Path $td ((Split-Path $td -Leaf)+".csv"); if(Test-Path $rcsv){ $fa+=@('--runtime-csv',$rcsv) } }
  if($FxReport){ $fa+=@('--report',$FxReport) }
  if($FxNcsSkip){ $fa+=@('--ncs-skip',$FxNcsSkip) }
  python -I "$S\fx\fx_import.py" @fa
  if($LASTEXITCODE){ throw 'fx_import failed' }
}
# P1: the stock perk jingles and machine sounds in the map's bank (after the audio module, which writes the bank json)
$ps=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--aliases',"$D\cp_zmb\sound\cp_zmb.all.aliases.csv",'--aliases',(& "$S\machine.ps1" Runtime 'iwz-stage2\audio\lab\dump\cp_disco\sound\cp_disco.all.aliases.csv'),'--stock-bank',(& "$S\machine.ps1" Runtime 'private-test-server\cp_disco.sabl'),'--stock-bank',(& "$S\machine.ps1" Runtime 'private-test-server\cp_disco.sabs'),'--report',"$UmOut.perk_sounds.json")
python -I "$S\perks\add_perk_sounds.py" @ps
if($LASTEXITCODE){ throw 'add_perk_sounds failed' }
# P1: every localized string the zone's scripts use, in the zone (a usermap loads no language zone of its template),
# last so it sees every module's scripts
$la=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",'--strings',(& "$S\machine.ps1" Runtime 'iw7-dump-lui\localize.json'),'--extra',"$S\perks\strings.json",'--report',"$UmOut.localize.tsv")
foreach($lz in 'eng_cp_zmb','eng_patch_cp_zmb'){ if(Test-Path "$W\dump\$lz\localizedstrings"){ $la+=@('--strings',"$W\dump\$lz\localizedstrings") } }
python -I "$S\perks\add_localize.py" @la
if($LASTEXITCODE){ throw 'add_localize failed' }
$null = New-Item -ItemType Directory -Force "$W\zonetool\$Map\techsets\ps"
if(!(Test-Path "$W\zonetool\$Map\techsets\ps\null.hlsl.cso")){ [IO.File]::WriteAllBytes("$W\zonetool\$Map\techsets\ps\null.hlsl.cso",[byte[]]@()) }
$csv="$W\zone_source\$Map.csv"; $lines=Get-Content $csv
$req=@('techsets_common','techsets_global','techsets_common_core_mp','techsets_global_core_mp','techsets_common_mp','techsets_global_mp','techsets_common_cp','techsets_global_cp','techsets_cp_zmb')|ForEach-Object {"require,$_"}
Set-Content $csv (@($lines[0])+$req+$lines[1..($lines.Count-1)]) -Encoding ascii
foreach($ext in 'ff','sabl','sabs'){ if(Test-Path "$W\zone\$Map.$ext"){ Remove-Item "$W\zone\$Map.$ext" } }
[IO.File]::WriteAllText($keyFile,$modKey)
Lap 'assemble'
$b = Invoke-Zt @('-buildzone',$Map) 2400
Lap 'zone'
$b | Select-String -Pattern 'FATAL|TIMEOUT|ERROR|Successfully compiled' | Select-Object -First 15
if(!(Test-Path "$W\zone\$Map.ff")){ $b | Select-Object -Last 30; throw 'buildzone produced no fastfile' }
New-Item -ItemType Directory $UmOut -Force | Out-Null
Copy-Item "$W\zone\$Map.ff" "$UmOut\$Map.ff" -Force
# sound bank files (audio module): the usermap needs them next to the FF, and stale ones from an earlier build must go
foreach($ext in 'sabl','sabs'){
  if(Test-Path "$UmOut\$Map.$ext"){ Remove-Item "$UmOut\$Map.$ext" -Force }
  if((Test-Path "$W\zone\$Map.$ext")){ Copy-Item "$W\zone\$Map.$ext" "$UmOut\$Map.$ext" -Force }
}
if($Arena -and (Test-Path $Arena)){ Copy-Item $Arena "$UmOut\$Map.arena" -Force }
$times.total=[int]((Get-Date)-$t0).TotalSeconds
[ordered]@{map=$Map;ff_bytes=(Get-Item "$UmOut\$Map.ff").Length;incremental=[bool]$inc;seconds=$times;zonetool=$ZoneToolExe} | ConvertTo-Json | Set-Content "$UmOut.build.json"
"built $UmOut\$Map.ff $((Get-Item "$UmOut\$Map.ff").Length) bytes in $($times.total) s (compile $($times.compile), assemble $($times.assemble), zone $($times.zone))"
} finally {
  # release the build reservation; the scheduler keeps it while a compiler of ours may still be ending
  $relUntil=[datetime]::UtcNow.AddMinutes(30); $done=$false
  while(-not $done){
    try{ Exit-IW7ResourceLease -Token $held.Token | Out-Null; $done=$true }
    catch{ if($_.Exception.Message -notlike 'Heavy child may still be alive*' -or [datetime]::UtcNow -ge $relUntil){ throw }; Start-Sleep -Seconds 5 }
  }
}
