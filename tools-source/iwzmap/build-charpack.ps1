param(
  [Parameter(Mandatory)][string]$Work,          # ZoneTool work folder (new-work-from-stock.ps1); its dump\ holds the zone dumps
  [Parameter(Mandatory)][string]$Out,           # new folder: the pack (zone_source\<zone>.csv, zonetool\<zone>\), and <zone>.ff with -Build
  [string]$Characters=(Join-Path $PSScriptRoot 'characters_5_8.json'),
  [ValidatePattern('^[a-z0-9_]+$')][string]$Zone='mod',
  [string]$RuntimeDir,                          # stock dumps with techsets_*\<zone>.csv (default: machine.ps1 TemplateDump)
  [string]$Scheduler='',                         # Resource-Scheduler.Core.ps1; empty: scheduler.ps1 resolves and guards it
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
"dumps ready: $($zones -join ', ') ($([int]$clock.Elapsed.TotalSeconds) s)"
$dumpArgs=@(); foreach($z in $zones){ $dumpArgs+='--dump'; $dumpArgs+="$z=$Work\dump\$z;$Work\dump\techsets_$z;$Work\dump\patch_$z" }
& python -I -B "$PSScriptRoot\char_pack.py" $Out --characters $Characters --zone $Zone --runtime-dir $RuntimeDir @dumpArgs
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
