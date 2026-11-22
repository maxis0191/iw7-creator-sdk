param(
  [Parameter(Mandatory)][string]$Src,                                                                 # emit folder of blend2iwz.py (docs/IWZ-EMIT-CONTRACT.md)
  [Parameter(Mandatory)][string]$UmOut,                                                               # usermap dir to fill (<Map>.ff, .arena)
  [string]$Map='',                                                                                    # the map's name (cp_ + up to 12 of a-z 0-9 _); default: layout.json "map" of the emit (the exporter writes the scene's iwz_map), else cp_iwz
  [string]$Title='',                                                                                  # the name in the map browser and the lobby (at most 30 characters); default: layout.json "title", else the map name in capitals
  [string]$Description='An IWZ custom map',                                                           # the browser's one-line description (at most 30 characters)
  [string]$Art='',                                                                                    # folder with image_<map>.tga, image_<map>_vote.tga (and zmb_poster_<map>_c.tga): the browser art; default: generated, the title on a neutral plate
  [switch]$NoArt,                                                                                     # no <map>_art.ff (the map is then in the list without pictures)
  [string]$FrontendDump=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-map-m2-a\dump\cp_frontend'),    # cp_frontend dump with the stock poster model (xmodel, xsurface): without it the art has no theater poster
  [string]$Work=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-blend\ztwork'),                           # own zonetool work dir (new-work.ps1 + zonetool\cp_zmb_tpl junction), NOT the Station Zero one
  [string]$ZoneToolExe=(& "$PSScriptRoot\machine.ps1" MapCompiler),                                   # the one pinned compiler of every map build (machine.ps1: IWZ_ZONETOOL_EXE, else zonetool-lightvol-ea60b19)
  [string]$TemplateDump=(& "$PSScriptRoot\machine.ps1" TemplateDump),
  [string]$Arena='',                                                                                  # an arena file to copy as <map>.arena; default: generated from the map name and the title
  [int]$Tries=600,
  [switch]$Bake,                                                                                      # light bake first: layout_lights.py + lmbake.py on $Src -> "$Src`_lm" (the baked copy is then built)
  [int]$Rays=144,
  [switch]$ReuseCompile,                                                                              # keep the previous iwzcompile output of the same -Src (dump\<map>)
  [switch]$Incremental,                                                                               # no effect: incremental assembly is the default (kept for old command lines)
  [switch]$QuickKey,                                                                                 # key the stock dumps by a stamp (frozen reference dumps: milliseconds) instead of listing every file (about 15 s)
  [switch]$FullAssemble,                                                                              # assemble everything: ignore the kept tree even when its key matches
  [switch]$GatesOnly,                                                                                 # run the offline gates and stop (no ZoneTool)
  [string]$PerkMachines=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level\p1\machines\port'),   # the four authored new-perk machines (kept: the level script calls the perk module, perks\README.md)
  [string]$DeadeyeImage=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\assets\dumps\cp_disco\images\cp_zmb_perk_icon_deadeye.iw7Image'),
  [string]$DeadeyeKitDump=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\kitimport\ztwork\dump'),
  [string]$DeadeyeScriptable=(& "$PSScriptRoot\machine.ps1" Runtime 'iwz-stage2\level\ztwork-p1\dump\cp_disco\scriptable\zm_perk_machine_deadeye_sign'))
# Generic zombies map build from a Blender emit folder. NOT RUN by the worker that wrote it; the lead runs it. It is the build-sz2.ps1
# sequence without what is Station Zero's (no --gap-regions portal names, no audio module, no kit / FX import, no darkness, no
# Station Zero game-script modules) and with an offline gate stage in front.
#
# What it runs, in this order (every ZoneTool run under the machine-wide resource lease, like build-sz2.ps1):
#   1  gates, plain Python, no game:  python iwz_emitcheck.py check <Src>      (collision and navigation of the emit)
#                                     python iwz_emitcheck.py reach <Src> --all-spawners   (every spawner has a route on the real
#                                     navgraph, stacked floors included; sz2_navconn.py reads plan.json as one floor per column and
#                                     reports false seams on a map with a floor over another, so it is not a gate here)
#                                     python <server>\ops\iwzmap\iwzmap_ents_lint.py <Src>\ents.txt --gsc <Src>\cp_iwz.gsc  (when the server checkout is present)
#                                     both gates fail the build on an error; -GatesOnly stops here
#   2  -Bake:   bake\layout_lights.py <Src> lights.json ; bake\lmbake.py <Src> lights.json <Src>_lm --rays <Rays> --bounces 3 --denoise 1
#               (bake python = machine.ps1 BakePython); the other emit files are copied over and the baked copy is built
#   3  zonetool -iwzcompile cp_zmb_tpl cp_zmb <Map> <Src>     IWZ_GEN_TOME=1 IWZ_KEEP_ENTSHAPES=1, plus IWZ_KEEP_SUBMODELS=1 IWZ_TRIGGER_SHAPES=1
#               when layout.json has doors (the debris blocker sub-model of the template, sz2_submodels.json)
#   4  volume_check.py <compiled maps\cp> <Map> --plan plan.json --require-spawners --layout layout.json   (no --gap-regions)
#   5  assemble.py <Work> <Map> <Src>\cp_iwz.gsc <template dumps>     then   sz2_assemble.py <Work> <Map> <Src>   (custom materials, modules of the emit)
#   6  perks\add_perks.py, perks\add_perk_sounds.py, perks\add_localize.py   (the level script cp_iwz3.gsc links against cp_iwz_perks)
#   7  zonetool -buildzone <Map>                                copies <Map>.ff (and .sabl/.sabs, .arena) to <UmOut>
#   8  <Map>_art.ff   (unless -NoArt) the browser art: make_art.py --plate draws the title on a neutral plate when -Art gives no images,
#                     build_art.py prepares the zone, zonetool -buildzone <Map>_art; <Map>.arena is generated (map_identity.py) unless -Arena
# Identity: the map name comes from layout.json "map" (the exporter's iwz_map) unless -Map says it; every name below follows it
#   (docs/MAP-BUILD-LOOP.md lists the places). Two maps built to two usermap dirs sit side by side.
# Output: <UmOut>\<Map>.ff, <UmOut>\<Map>_art.ff, <UmOut>\<Map>.arena, <UmOut>.build.json (seconds per stage), <UmOut>.volume_check.json, <UmOut>.compile.log.
$ErrorActionPreference='Stop'
$S=$PSScriptRoot; $W=$Work; $D=$TemplateDump
$py='python'
function Run-Gate([string]$Name,[scriptblock]$Block){ $o=& $Block 2>&1; $c=$LASTEXITCODE; ($o | Select-Object -Last 6) | ForEach-Object { "  [$Name] $_" }; if($c){ throw "gate $Name failed (exit $c)" } }
$idArgs=@('resolve',$Src); if($Map){ $idArgs+=@('--map',$Map) }
$idOut=& $py -I -B "$S\map_identity.py" @idArgs 2>&1
if($LASTEXITCODE){ throw ($idOut -join ' ') }
$Map=([string]($idOut | Select-Object -Last 1)).Trim()
$layout0=Get-Content "$Src\layout.json" -Raw | ConvertFrom-Json
if(-not $Title){ $Title=if($layout0.title){ [string]$layout0.title } else { (& $py -I -B "$S\map_identity.py" title $Map).Trim() } }
$lvl=if(Test-Path "$Src\$Map.gsc"){ "$Src\$Map.gsc" } else { "$Src\cp_iwz.gsc" }       # the exporter always writes cp_iwz.gsc; assemble.py moves its script paths to the map
if(-not (Test-Path $lvl)){ throw "level script missing: $Src\$Map.gsc or $Src\cp_iwz.gsc" }
"map $Map  title '$Title'  level script $lvl"
Run-Gate 'emitcheck' { & $py -I -B "$S\iwz_emitcheck.py" check $Src }
Run-Gate 'reach' { & $py -I -B "$S\iwz_emitcheck.py" reach $Src --all-spawners }
$lint=Join-Path (& "$S\machine.ps1" Server) 'ops\iwzmap\iwzmap_ents_lint.py'
if(Test-Path $lint){ Run-Gate 'ents_lint' { & $py -I -B $lint "$Src\ents.txt" --gsc $lvl } }
if($GatesOnly){ return }
if($Bake){
  $PY=(& "$S\machine.ps1" BakePython)+'\Scripts\python.exe'
  $build="$Src`_lm"
  $lj="$Src.lights.json"
  & $PY -I "$S\bake\layout_lights.py" $Src $lj
  if($LASTEXITCODE){ throw 'layout_lights failed' }
  if(Test-Path $build){ Remove-Item $build -Recurse -Force }
  & $PY -I "$S\bake\lmbake.py" $Src $lj $build --rays $Rays --bounces 3 --denoise 1 2>&1 | Select-Object -Last 8
  if(!(Test-Path "$build\lightmap\secondary.dds")){ throw 'bake produced no lightmap' }
  Get-ChildItem $Src -File | Where-Object { $_.Name -notin @('world.bin','lighting.txt') } | ForEach-Object { Copy-Item $_.FullName (Join-Path $build $_.Name) -Force }
  if(Test-Path "$Src\modules"){ Copy-Item "$Src\modules" "$build\modules" -Recurse -Force }
  $Src=$build
  $lvl=Join-Path $Src (Split-Path $lvl -Leaf)
}
$layout=Get-Content "$Src\layout.json" -Raw | ConvertFrom-Json
$hasDoors=(@($layout.doors).Count -gt 0)
# Deadeye Dewdrops is a cp_disco machine relocated from a parked map scriptable: only when the map places one
$hasDeadeye=(@($layout.interactions | Where-Object { $_.kind -eq 'perk_machine_deadeye' }).Count -gt 0)
if(-not $hasDeadeye){ $DeadeyeKitDump=''; $DeadeyeScriptable='' }
# the perk module is part of every map built from cp_iwz3.gsc; its four new machines are kept as in build-sz2.ps1
$perkKit=@(); $KitDumps=@(); $KitModels=''
if($PerkMachines -and (Test-Path $PerkMachines)){ $perkKit+='perks:iwz_perk_machine_bakers,perks:iwz_perk_machine_voyage,perks:iwz_perk_machine_grudge,perks:iwz_perk_machine_double'; $KitDumps+="perks=$PerkMachines" }
if($DeadeyeKitDump -and (Test-Path "$DeadeyeKitDump\cp_disco\xmodel")){ $perkKit+='cp_disco:cp_disco_perk_dewdrops,cp_disco:cp_disco_perk_dewdrops_off'; $KitDumps+="cp_disco=$DeadeyeKitDump\cp_disco;$DeadeyeKitDump\techsets_cp_disco" }
if($perkKit.Count){ $KitModels=($perkKit | Where-Object { $_ }) -join ',' }
$times=[ordered]@{}; $t0=Get-Date; $tp=Get-Date
function Lap([string]$Name){ $script:times[$Name]=[int]((Get-Date)-$script:tp).TotalSeconds; $script:tp=Get-Date }
function Invoke-Zt([string[]]$a,[int]$t){
  for($k=0;$k -lt $Tries;$k++){
    try { return (& "$S\zt.ps1" -Work $W -ZtArgs $a -TimeoutSec $t -HeldLease $script:held -Owner $(if($env:IWZ_BUILD_OWNER){$env:IWZ_BUILD_OWNER}else{'IWZ Blender map build'})) }
    catch { if($_.Exception.Message -match 'Resource busy|Heavy job already reserved|busy|wait before heavy admission|wait for its owner'){ Start-Sleep 15; continue }; throw }
  }
  throw 'resource lease not obtained'
}
New-Item -ItemType Directory -Force $W | Out-Null
New-Item -ItemType Directory -Force $UmOut | Out-Null     # before the compile: its log and volume_check.json are written next to it
$null = New-Item -ItemType Directory -Force (Split-Path $UmOut -Parent)
Copy-Item $ZoneToolExe "$W\zonetool.exe" -Force
. (& "$S\scheduler.ps1" '')
$held=$null; $heldClock=[Diagnostics.Stopwatch]::StartNew()
$ownerName=if($env:IWZ_BUILD_OWNER){$env:IWZ_BUILD_OWNER}else{'IWZ Blender map build'}
while(-not $held){
  try{ $held=Enter-IW7ResourceLease -Scope $W -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner $ownerName }
  catch{
    $busy=if(Get-Command Test-IW7RetryableRefusal -ErrorAction SilentlyContinue){ (Test-IW7RetryableRefusal $_.Exception.Message) -or $_.Exception.Message -like 'Resource admission lock busy*' }else{ $_.Exception.Message -match 'Resource busy|busy' }
    if(!$busy -or $heldClock.Elapsed.TotalSeconds -gt $Tries*15){ throw }
    Start-Sleep -Seconds 5
  }
}
"waited for the build reservation $([int]$heldClock.Elapsed.TotalSeconds) s"
try {
if($ReuseCompile -and (Test-Path "$W\dump\$Map\maps\cp\$Map.d3dbsp.ents")){ "reusing compiled $W\dump\$Map" } else {
if(Test-Path "$W\iwz_src"){ Remove-Item "$W\iwz_src" -Recurse -Force }
Copy-Item -Recurse $Src "$W\iwz_src"
if(Test-Path "$W\dump\$Map"){ Remove-Item -LiteralPath "$W\dump\$Map" -Recurse -Force }
$env:IWZ_GEN_TOME='1'; $env:IWZ_KEEP_ENTSHAPES='1'
if($hasDoors){ $env:IWZ_KEEP_SUBMODELS='1'; $env:IWZ_TRIGGER_SHAPES='1' }
try { $c = Invoke-Zt @('-iwzcompile','cp_zmb_tpl','cp_zmb',$Map,"$W\iwz_src") 900 } finally { Remove-Item Env:IWZ_GEN_TOME,Env:IWZ_KEEP_ENTSHAPES,Env:IWZ_KEEP_SUBMODELS,Env:IWZ_TRIGGER_SHAPES -ErrorAction SilentlyContinue }
$full = Get-ChildItem "$W\zt-*.out.log" | Sort-Object LastWriteTime | Select-Object -Last 1
if($full){ Copy-Item $full.FullName "$UmOut.compile.log" -Force -ErrorAction SilentlyContinue }
if(($c -join "`n") -notmatch 'iwzmap: wrote'){ $c | Select-Object -Last 25; throw 'iwzcompile failed' }
($c | Select-String 'iwzmap: wrote|relit|brush models|generated trigger|lightmap').Line | Select-Object -First 30
}
if($hasDoors -and (Test-Path "$Src\plan.json")){
  & $py -I "$S\volume_check.py" "$W\dump\$Map\maps\cp" $Map --plan "$Src\plan.json" --require-spawners --layout "$Src\layout.json" --json "$UmOut.volume_check.json" | Select-Object -Last 4
  if($LASTEXITCODE){ throw 'volume_check failed' }
}
Lap 'compile'
# Incremental assembly is the default (docs/MAP-BUILD-LOOP.md): the stock links (135,676) and what the modules added stay in
# zonetool\<map> when the key of every input of the assembly (assemble_key.py) equals the one stored beside the kept tree by the last
# build that finished. Only the generated world is linked again and the modules run again over the kept tree. -FullAssemble forces everything.
$sub=[ordered]@{}; $ts=Get-Date
function Mark([string]$Name){ $script:sub[$Name]=[math]::Round(((Get-Date)-$script:ts).TotalSeconds,1); $script:ts=Get-Date }
$dumpList=@("$D\patch_cp_zmb","$D\techsets_cp_zmb","$D\techsets_global_cp","$D\techsets_global","$D\cp_zmb")
$mk=if($QuickKey){ '--stamp' } else { '--manifest' }     # every stock dump below: full listing (about 15 s for 136k files) or the quick stamp (see assemble_key.py)
$kp=@('--text',"map=$Map",'--text',"IWZ_FULL_STOCK=$env:IWZ_FULL_STOCK",'--text',"IWZ_KEEP_STOCK_REFS=$env:IWZ_KEEP_STOCK_REFS",
  '--file',$ZoneToolExe,'--file',"$S\assemble.py",'--file',"$S\sz2_assemble.py",'--file',"$S\kit_import.py",'--tree',"$S\perks",'--tree',"$S\content")
foreach($dp in $dumpList){ $kp+=@($mk,$dp) }
foreach($td in [IO.Directory]::GetDirectories($D,'techsets_*')){ $rcsv=Join-Path $td ((Split-Path $td -Leaf)+'.csv'); if(Test-Path $rcsv){ $kp+=@('--file',$rcsv) } }
foreach($kd in $KitDumps){ foreach($kpath in (($kd -split '=',2)[-1] -split ';')){ if($kpath -and (Test-Path -LiteralPath $kpath)){ $kp+=@($mk,$kpath) } } }
foreach($kf in @($DeadeyeImage,$DeadeyeScriptable)){ if($kf -and (Test-Path -LiteralPath $kf -PathType Leaf)){ $kp+=@('--file',$kf) } elseif($kf -and (Test-Path -LiteralPath $kf)){ $kp+=@($mk,$kf) } }
$kp+=@('--text',('args='+(@($KitModels,($KitDumps -join '|')) -join "`n")))
$modKey=& "$S\Get-AssembleKey.ps1" @kp
Mark 'key'
$keyFile="$W\zonetool\$Map\.iwz_modules.key"
$inc=@()
$kept=Test-Path -LiteralPath $keyFile
if($kept -and -not $FullAssemble -and ((Get-Content -LiteralPath $keyFile -Raw) -eq $modKey)){ $inc=@('--incremental'); "incremental assembly: the kept tree was made from the same inputs (key $($modKey.Substring(0,12)))" }
elseif(Test-Path "$W\zonetool\$Map"){
  $why=if($FullAssemble){ '-FullAssemble' } elseif($kept){ 'an input of the assembly changed' } else { 'no finished assembly to keep' }
  "full assembly: $why"; Remove-Item -LiteralPath "$W\zonetool\$Map" -Recurse -Force
}
Remove-Item -LiteralPath $keyFile -Force -ErrorAction SilentlyContinue     # the key is written again only when this assembly finishes
& $py -I "$S\assemble.py" $W $Map $lvl @dumpList @inc | Select-Object -Last 3
if($LASTEXITCODE){ throw 'assemble failed' }
& $py -I "$S\sz2_assemble.py" $W $Map $Src
if($LASTEXITCODE){ throw 'sz2_assemble failed' }
Mark 'link'
$pa=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--template-dump',$D)
if($DeadeyeImage -and (Test-Path $DeadeyeImage)){ $pa+=@('--deadeye-image',$DeadeyeImage) }
& $py -I "$S\perks\add_perks.py" @pa
if($LASTEXITCODE){ throw 'add_perks failed' }
if($KitModels){
  $ka=@($W,$Map); foreach($kd in $KitDumps){ $ka+=@('--dump',$kd) }
  $ka+=@('--models',$KitModels)
  foreach($td in [IO.Directory]::GetDirectories($D,'techsets_*')){ $rcsv=Join-Path $td ((Split-Path $td -Leaf)+'.csv'); if(Test-Path $rcsv){ $ka+=@('--runtime-csv',$rcsv) } }
  & $py -I "$S\kit_import.py" @ka
  if($LASTEXITCODE){ throw 'kit_import failed' }
}
if($DeadeyeScriptable -and (Test-Path $DeadeyeScriptable)){
  & $py -I "$S\perks\add_deadeye_machine.py" "$W\zone_source\$Map.csv" "$W\zonetool\$Map" $Map --scriptable $DeadeyeScriptable --report "$UmOut.deadeye.json"
  if($LASTEXITCODE){ throw 'add_deadeye_machine failed' }
}
$ps=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",$Map,'--aliases',"$D\cp_zmb\sound\cp_zmb.all.aliases.csv",'--aliases',(& "$S\machine.ps1" Runtime 'iwz-stage2\audio\lab\dump\cp_disco\sound\cp_disco.all.aliases.csv'),'--stock-bank',(& "$S\machine.ps1" Runtime 'private-test-server\cp_disco.sabl'),'--stock-bank',(& "$S\machine.ps1" Runtime 'private-test-server\cp_disco.sabs'),'--report',"$UmOut.perk_sounds.json")
& $py -I "$S\perks\add_perk_sounds.py" @ps
if($LASTEXITCODE){ throw 'add_perk_sounds failed' }
& $py -I -B "$S\map_identity.py" strings $Map $Title "$S\perks\strings.json" "$W\strings_$Map.json"
if($LASTEXITCODE){ throw 'map_identity strings failed' }
$la=@("$W\zone_source\$Map.csv","$W\zonetool\$Map",'--strings',(& "$S\machine.ps1" Runtime 'iw7-dump-lui\localize.json'),'--extra',"$W\strings_$Map.json",'--report',"$UmOut.localize.tsv")
foreach($lz in 'eng_cp_zmb','eng_patch_cp_zmb'){ if(Test-Path "$W\dump\$lz\localizedstrings"){ $la+=@('--strings',"$W\dump\$lz\localizedstrings") } }
& $py -I "$S\perks\add_localize.py" @la
if($LASTEXITCODE){ throw 'add_localize failed' }
$null = New-Item -ItemType Directory -Force "$W\zonetool\$Map\techsets\ps"
if(!(Test-Path "$W\zonetool\$Map\techsets\ps\null.hlsl.cso")){ [IO.File]::WriteAllBytes("$W\zonetool\$Map\techsets\ps\null.hlsl.cso",[byte[]]@()) }
$csv="$W\zone_source\$Map.csv"; $lines=Get-Content $csv
$req=@('techsets_common','techsets_global','techsets_common_core_mp','techsets_global_core_mp','techsets_common_mp','techsets_global_mp','techsets_common_cp','techsets_global_cp','techsets_cp_zmb')|ForEach-Object {"require,$_"}
Set-Content $csv (@($lines[0])+$req+$lines[1..($lines.Count-1)]) -Encoding ascii
foreach($ext in 'ff','sabl','sabs'){ if(Test-Path "$W\zone\$Map.$ext"){ Remove-Item "$W\zone\$Map.$ext" } }
[IO.File]::WriteAllText($keyFile,$modKey)
Mark 'modules'
Lap 'assemble'
$b = Invoke-Zt @('-buildzone',$Map) 2400
Lap 'zone'
$b | Select-String -Pattern 'FATAL|TIMEOUT|ERROR|Successfully compiled' | Select-Object -First 15
if(!(Test-Path "$W\zone\$Map.ff")){ $b | Select-Object -Last 30; throw 'buildzone produced no fastfile' }
New-Item -ItemType Directory $UmOut -Force | Out-Null
Copy-Item "$W\zone\$Map.ff" "$UmOut\$Map.ff" -Force
foreach($ext in 'sabl','sabs'){
  if(Test-Path "$UmOut\$Map.$ext"){ Remove-Item "$UmOut\$Map.$ext" -Force }
  if(Test-Path "$W\zone\$Map.$ext"){ Copy-Item "$W\zone\$Map.$ext" "$UmOut\$Map.$ext" -Force }
}
if($Arena){ if(-not (Test-Path $Arena)){ throw "arena file not found: $Arena" }; Copy-Item $Arena "$UmOut\$Map.arena" -Force }
else { & $py -I -B "$S\map_identity.py" arena $Map $Title "$UmOut\$Map.arena" --description $Description; if($LASTEXITCODE){ throw 'map_identity arena failed' } }
Lap 'copy'
# the browser art zone <map>_art.ff: the client loads usermaps\<map>\<map>_art.ff in the front end and defaults the arena's images to
# image_<map> and image_<map>_vote; the theater poster needs the stock poster model of a cp_frontend dump
if(-not $NoArt){
  $artDir=$Art
  if(-not $artDir){
    $artDir="$UmOut.art"; New-Item -ItemType Directory -Force $artDir | Out-Null
    & $py -I "$S\make_art.py" --plate $Title $artDir $Map | Select-Object -Last 1
    if($LASTEXITCODE){ throw 'make_art failed' }
  }
  foreach($n in "image_$Map","image_${Map}_vote"){ if(-not (Test-Path "$artDir\$n.tga")){ throw "art image missing: $artDir\$n.tga" } }
  $frontend=if($FrontendDump -and (Test-Path "$FrontendDump\xmodel\zmb_poster_dlc1.xmb")){ @($FrontendDump) } else { @() }
  if(-not $frontend){ 'no cp_frontend dump with the poster model: the art zone has the list and vote images only' }
  & $py -I "$S\build_art.py" $W $Map "$W\zonetool\$Map" $artDir @frontend | Select-Object -Last 2
  if($LASTEXITCODE){ throw 'build_art failed' }
  if(Test-Path "$W\zone\${Map}_art.ff"){ Remove-Item "$W\zone\${Map}_art.ff" }
  $ab = Invoke-Zt @('-buildzone',"${Map}_art") 900
  if(!(Test-Path "$W\zone\${Map}_art.ff")){ $ab | Select-Object -Last 30; throw 'buildzone produced no art fastfile' }
  Copy-Item "$W\zone\${Map}_art.ff" "$UmOut\${Map}_art.ff" -Force
  Lap 'art'
}
$times.total=[int]((Get-Date)-$t0).TotalSeconds
[ordered]@{map=$Map;title=$Title;src=$Src;ff_bytes=(Get-Item "$UmOut\$Map.ff").Length;art=(-not $NoArt);incremental=[bool]$inc;seconds=$times;assemble_parts=$sub;key=$modKey;zonetool=$ZoneToolExe} | ConvertTo-Json | Set-Content "$UmOut.build.json"
"built $UmOut\$Map.ff $((Get-Item "$UmOut\$Map.ff").Length) bytes in $($times.total) s (compile $($times.compile), assemble $($times.assemble) [key $($sub.key), link $($sub.link), modules $($sub.modules)], zone $($times.zone), art $($times.art))"
} finally {
  $relUntil=[datetime]::UtcNow.AddMinutes(30); $done=$false
  while(-not $done){
    try{ Exit-IW7ResourceLease -Token $held.Token | Out-Null; $done=$true }
    catch{ if($_.Exception.Message -notlike 'Heavy child may still be alive*' -or [datetime]::UtcNow -ge $relUntil){ throw }; Start-Sleep -Seconds 5 }
  }
}
