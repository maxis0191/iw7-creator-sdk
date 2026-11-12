param(
  [Parameter(Mandatory)][string]$Work,          # ZoneTool work folder (new-work-from-stock.ps1); its dump\ holds the zone dumps
  [Parameter(Mandatory)][string]$Out,           # new folder: the pack (zone_source\<zone>.csv, zonetool\<zone>\), and <zone>.ff with -Build
  [string]$Characters=(Join-Path $PSScriptRoot 'characters_5_8.json'),
  [ValidatePattern('^[a-z0-9_]+$')][string]$Zone='mod',
  [string]$RuntimeDir,                          # stock dumps with techsets_*\<zone>.csv (default: machine.ps1 TemplateDump)
  [string]$Scheduler,                          # a Resource-Scheduler.Core.ps1; empty: zt.ps1 resolves it (scheduler.ps1)
  [ValidateRange(0,14400)][int]$WaitForSlotSeconds=3600,
  [switch]$Build)                               # also build the pack alone as zone <zone> (a test mod: mods\<name>\mod.ff)
# One command for a character pack: dumps what the work folder lacks (each source zone's models, materials, images and
# physics, and its techsets zone), writes the pack with char_pack.py, and with -Build compiles it. Every ZoneTool run
# goes through zt.ps1 (the build reservation, in the scheduler's waiting order).
$ErrorActionPreference='Stop'
$Work=[IO.Path]::GetFullPath($Work); $Out=[IO.Path]::GetFullPath($Out)
if(Test-Path -LiteralPath $Out){ throw "exists: $Out" }
if(!(Test-Path -LiteralPath "$Work\zonetool.exe")){ throw "not a ZoneTool work folder: $Work" }
if(!$RuntimeDir){ $RuntimeDir=(& "$PSScriptRoot\machine.ps1" TemplateDump -MustExist) }
$zt=@{Work=$Work;Scheduler=$Scheduler;WaitForSlotSeconds=$WaitForSlotSeconds}
if(!$Scheduler){ $zt.Remove('Scheduler') }
$spec=Get-Content -LiteralPath $Characters -Raw | ConvertFrom-Json
$zones=@($spec.characters | ForEach-Object zone | Sort-Object -Unique)
$clock=[Diagnostics.Stopwatch]::StartNew()
# One ZoneTool run per source zone: its techsets zone, the zone itself, and its patch zone (patch_<zone> defines some
# images the map only references: Elvira's dress in patch_cp_town), the set the game itself loads for one map. Measured
# 11 Nov 2026: four maps with their techsets in one run passed, but adding three patch zones to one run hit the game's
# pool of 16 'animclass' assets (a hidden fatal dialog; zt.ps1 now ends such a run at once). Inside a run the techsets
# zone comes first: -dumpzonetypes keeps its type filter for the rest of the run. A finished zone leaves
# dump\.charpack-<zone>.done; a run that did not print "Zone ... dumped." for every zone it asked is refused.
foreach($z in $zones){
  $done="$Work\dump\.charpack-$z.done"
  if(Test-Path -LiteralPath $done){ continue }
  $ask=@('-dumpzone',"techsets_$z",'-dumpzonetypes',$z,'xmodel,xmodelsurfs,material,image,physicsasset,physicsfxshape')
  $names=@("techsets_$z",$z)
  if(Test-Path -LiteralPath "$Work\zone\patch_$z.ff"){ $ask+=@('-dumpzonetypes',"patch_$z",'material,image'); $names+="patch_$z" }
  $said=(& "$PSScriptRoot\zt.ps1" @zt -Owner "character pack: dump $z" -ZtArgs $ask -TimeoutSec 1800) -join "`n"
  $log=Get-ChildItem -LiteralPath $Work -Filter 'zt-*.out.log' | Sort-Object LastWriteTime | Select-Object -Last 1
  $text=Get-Content -LiteralPath $log.FullName -Raw
  foreach($n in $names){ if($text -notmatch [regex]::Escape("Zone `"$n`" dumped.")){ throw "dump of $n did not finish: $($log.FullName)`n$said" } }
  Set-Content -LiteralPath $done -Value $log.Name
}
$dumpArgs=@(); foreach($z in $zones){ $dumpArgs+='--dump'; $dumpArgs+="$z=$Work\dump\$z;$Work\dump\techsets_$z;$Work\dump\patch_$z" }
$dumpArgs+=@('--runtime-extra',"$Work\dump")
# A zone whose character models name a procedural bone set or a scriptable that no shared zone defines (Pam's body in
# cp_disco: procedurual_female_undershoulder, pam_grier) also needs those assets and the effects the scriptable plays
# (char_pack.py --needs reads it from the models and the zone's dump list). One more run for each such zone.
$need=@(& python -I -B "$PSScriptRoot\char_pack.py" $Out --needs --characters $Characters --runtime-dir $RuntimeDir @dumpArgs)
if($LASTEXITCODE){ throw 'char_pack.py --needs failed' }
foreach($line in $need){
  $z,$types=($line -split '#')[0].Trim() -split '\s+'
  $done="$Work\dump\.charpack-$z.extra.done"
  if(Test-Path -LiteralPath $done){ continue }
  $said=(& "$PSScriptRoot\zt.ps1" @zt -Owner "character pack: dump $z extras" -ZtArgs @('-dumpzonetypes',$z,$types) -TimeoutSec 1800) -join "`n"
  $log=Get-ChildItem -LiteralPath $Work -Filter 'zt-*.out.log' | Sort-Object LastWriteTime | Select-Object -Last 1
  if((Get-Content -LiteralPath $log.FullName -Raw) -notmatch [regex]::Escape("Zone `"$z`" dumped.")){ throw "extra dump of $z did not finish: $($log.FullName)`n$said" }
  Set-Content -LiteralPath $done -Value "$types $($log.Name)"
}
"dumps ready: $($zones -join ', ') ($([int]$clock.Elapsed.TotalSeconds) s)"
& python -I -B "$PSScriptRoot\char_pack.py" $Out --characters $Characters --zone $Zone --runtime-dir $RuntimeDir @dumpArgs
if($LASTEXITCODE -eq 3){
  # Materials, techsets or images found in no dump: ask ZoneTool which of them the zones loaded at start hold (common,
  # techsets_common: kept for every map). Those become the shared list "startup"; then the pack is made again.
  $query="$Out\startup-query.csv"; $answer="$Work\dump\startup-answer.csv"
  Copy-Item -LiteralPath $query -Destination "$Work\startup-query.csv" -Force
  & "$PSScriptRoot\zt.ps1" @zt -Owner 'character pack: assets loaded at start' -ZtArgs @('-assetsloaded','startup-query.csv','dump\startup-answer.csv') -TimeoutSec 900 | Out-Null
  if(!(Test-Path -LiteralPath $answer)){ throw "ZoneTool wrote no answer (needs x64-zt with -assetsloaded): $Work" }
  $rows=@(Get-Content -LiteralPath $answer | Where-Object { $_ -like '*,loaded' } | ForEach-Object { $_ -replace ',loaded$','' })
  [IO.Directory]::CreateDirectory("$Work\dump\startup") | Out-Null
  $old=@(); if(Test-Path -LiteralPath "$Work\dump\startup\startup.csv"){ $old=@(Get-Content -LiteralPath "$Work\dump\startup\startup.csv") }
  Set-Content -LiteralPath "$Work\dump\startup\startup.csv" -Value (@($old+$rows) | Sort-Object -Unique)
  "assets loaded at start: $($rows.Count) of $(@(Get-Content -LiteralPath $answer).Count) asked"
  Remove-Item -LiteralPath $Out -Recurse -Force
  & python -I -B "$PSScriptRoot\char_pack.py" $Out --characters $Characters --zone $Zone --runtime-dir $RuntimeDir @dumpArgs
}
if($LASTEXITCODE){ throw "char_pack.py failed ($LASTEXITCODE): $Out\charpack-report.json" }
if(!$Build){ return }
# The work folder's own source of zone <zone> is replaced by the pack (links, no copy of the data).
$src="$Work\zonetool\$Zone"
if(Test-Path -LiteralPath $src){ Remove-Item -LiteralPath $src -Recurse -Force }
& robocopy "$Out\zonetool\$Zone" $src /E /MT:16 /NFL /NDL /NJH /NJS /NP | Out-Null
if($LASTEXITCODE -ge 8){ throw "pack copy failed ($LASTEXITCODE)" }
Copy-Item -LiteralPath "$Out\zone_source\$Zone.csv" -Destination "$Work\zone_source\$Zone.csv" -Force
Remove-Item -LiteralPath "$Work\zone\$Zone.ff" -ErrorAction SilentlyContinue
& "$PSScriptRoot\zt.ps1" @zt -Owner "character pack: build $Zone" -ZtArgs '-buildzone',$Zone
if(!(Test-Path -LiteralPath "$Work\zone\$Zone.ff")){ throw "$Zone.ff was not built (see the zt-*.out.log of $Work)" }
Copy-Item -LiteralPath "$Work\zone\$Zone.ff" -Destination "$Out\$Zone.ff"
$log=Get-ChildItem -LiteralPath $Work -Filter 'zt-*.out.log' | Sort-Object LastWriteTime | Select-Object -Last 1
Copy-Item -LiteralPath $log.FullName -Destination "$Out\build.log"
"built $Out\$Zone.ff $((Get-Item "$Out\$Zone.ff").Length) bytes in $([int]$clock.Elapsed.TotalSeconds) s; log $Out\build.log"
exit 0
