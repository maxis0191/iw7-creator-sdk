param(
  [Parameter(Mandatory)][string]$Work,          # new ZoneTool work folder (must not exist; same volume as the stock)
  [Parameter(Mandatory)][string]$StockRoot,     # retained test stock (a game folder kept for tests; never a played one)
  [Parameter(Mandatory)][string]$SeedWork,      # an existing ZoneTool work folder: gives tlsdll.dll and main\fileSysCheck.cfg
  [Parameter(Mandatory)][string]$ZoneTool,      # zonetool.exe with -iwzcompile
  [Parameter(Mandatory)][string]$TemplateDump)  # folder of stock dumps (cp_zmb, patch_cp_zmb, techsets_*): cp_zmb becomes the template
# A ZoneTool work folder that costs no disk: the big zone and pak files are extra names (hard links) for the data of the
# retained test stock. Nothing is ever written through those names: ZoneTool only reads them and writes zone\<map>.ff.
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $Work){ throw "exists: $Work" }
foreach($p in $StockRoot,$SeedWork,$ZoneTool,(Join-Path $TemplateDump 'cp_zmb')){ if(!(Test-Path -LiteralPath $p)){ throw "missing: $p" } }
New-Item -ItemType Directory $Work,"$Work\zone","$Work\main","$Work\zonetool","$Work\dump","$Work\zone_source" | Out-Null
foreach($f in 'iw7_ship.exe','amd_ags_x64.dll','bink2w64.dll','d3dcompiler_46.dll','steam_api.dll','steam_api64.dll','Steam.dll'){ Copy-Item -LiteralPath (Join-Path $StockRoot $f) -Destination (Join-Path $Work $f) }
Copy-Item -LiteralPath (Join-Path $SeedWork 'tlsdll.dll') -Destination (Join-Path $Work 'tlsdll.dll')
Copy-Item -LiteralPath (Join-Path $SeedWork 'main\fileSysCheck.cfg') -Destination (Join-Path $Work 'main\fileSysCheck.cfg')
Copy-Item -LiteralPath $ZoneTool -Destination (Join-Path $Work 'zonetool.exe')
$n=0
Get-ChildItem -LiteralPath $StockRoot -File | Where-Object { $_.Extension -in '.ff','.pak' } | ForEach-Object {
  New-Item -ItemType HardLink -Path (Join-Path "$Work\zone" $_.Name) -Target $_.FullName | Out-Null; $n++ }
New-Item -ItemType Junction -Path (Join-Path $Work 'zonetool\cp_zmb_tpl') -Target (Join-Path $TemplateDump 'cp_zmb') | Out-Null
"work folder ready: $n zone files linked, template $(Join-Path $TemplateDump 'cp_zmb')"
