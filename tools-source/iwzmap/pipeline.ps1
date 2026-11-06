param([string]$Map='cp_iwz',[string]$Src,[string]$Script,[string]$Tag,[switch]$Rebuild,[switch]$NoProbe,[switch]$Fresh,[double]$FloorZ=0,
  [string]$Server='C:\Users\ezvalo\Documents\IW7-Paris-Server',                                           # server checkout (probe runner)
  [string]$ZoneToolExe='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-map\build\bin\x64\Release\zonetool.exe',
  [string]$Work='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-m2-a',                                    # zonetool work dir (game zones linked)
  [string]$TemplateDump='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump',                     # stock dumps (cp_zmb, techsets_*)
  [string]$Out=(Join-Path $PSScriptRoot 'out'),                                                         # receives um_<map>/
  [string]$SourcePackage)                                                                               # prepared server inputs (probe)
$ErrorActionPreference='Stop'
$S=$PSScriptRoot; $R=$Server
$ZT=$ZoneToolExe
$W=$Work
$D=$TemplateDump
if($Rebuild){ $b = & "$S\build-zt.ps1"; if(($b -join "`n") -notmatch 'exit 0'){ $b; throw 'zonetool build failed' } }
Copy-Item $ZT "$W\zonetool.exe" -Force
if(Test-Path "$W\iwz_src"){ Remove-Item "$W\iwz_src" -Recurse -Force }
Copy-Item -Recurse $Src "$W\iwz_src"
if(Test-Path "$W\dump\$Map"){ Remove-Item -LiteralPath "$W\dump\$Map" -Recurse -Force }
$c = & "$S\zt.ps1" -Work $W -ZtArgs @('-iwzcompile','cp_zmb_tpl','cp_zmb',$Map,"$W\iwz_src") -TimeoutSec 900
if(($c -join "`n") -notmatch 'iwzmap: wrote'){ $c | Select-Object -Last 15; throw 'iwzcompile failed' }
($c | Select-String 'iwzmap: wrote').Line
if($Fresh -and (Test-Path "$W\zonetool\$Map")){ Remove-Item -LiteralPath "$W\zonetool\$Map" -Recurse -Force }
python -I "$S\assemble.py" $W $Map $Script "$D\patch_cp_zmb" "$D\techsets_cp_zmb" "$D\techsets_global_cp" "$D\techsets_global" "$D\cp_zmb"
$null = New-Item -ItemType Directory -Force "$W\zonetool\$Map\techsets\ps"
if(!(Test-Path "$W\zonetool\$Map\techsets\ps\null.hlsl.cso")){ [IO.File]::WriteAllBytes("$W\zonetool\$Map\techsets\ps\null.hlsl.cso",[byte[]]@()) }
$csv="$W\zone_source\$Map.csv"; $lines=Get-Content $csv
$req=@('techsets_common','techsets_global','techsets_common_core_mp','techsets_global_core_mp','techsets_common_mp','techsets_global_mp','techsets_common_cp','techsets_global_cp','techsets_cp_zmb')|ForEach-Object {"require,$_"}
Set-Content $csv (@($lines[0])+$req+$lines[1..($lines.Count-1)]) -Encoding ascii
if(Test-Path "$W\zone\$Map.ff"){ Remove-Item "$W\zone\$Map.ff" }
$b = & "$S\zt.ps1" -Work $W -ZtArgs @('-buildzone',$Map) -TimeoutSec 2400
$b | Select-String -Pattern 'FATAL|TIMEOUT|WARNING' | Select-Object -First 10
if(!(Test-Path "$W\zone\$Map.ff")){ throw 'buildzone produced no fastfile' }
$um=Join-Path $Out "um_$Map"; $null=New-Item -ItemType Directory -Force $um
Copy-Item "$W\zone\$Map.ff" "$um\$Map.ff" -Force
"built $((Get-Item "$um\$Map.ff").Length) bytes"
if(!$NoProbe){
  & "$R\ops\iwzmap\Test-IWZMap.ps1" -SourcePackage $SourcePackage -CandidateRoot 'C:\Users\ezvalo\Documents\IW7-Runtime\private-test-server' -GameRoot 'C:\Users\ezvalo\Desktop\iw_game_files' -OutputRoot "C:\Users\ezvalo\Documents\IW7-Runtime\iwz-probe-$Tag" -UsermapDir $um -Map $Map -Probe "$R\tests\fixtures\iwzmap_probe.gsc" -FloorZ $FloorZ -TimeoutSeconds 240
}
