param([Parameter(Mandatory)][string]$Work,[string]$ZoneTool=(& "$PSScriptRoot\machine.ps1" Runtime 'kino-ff-work-full\zonetool.exe'))
$ErrorActionPreference='Stop'
$g=(& "$PSScriptRoot\machine.ps1" GameRoot)
$k=(& "$PSScriptRoot\machine.ps1" Runtime 'kino-ff-work-full')
if(Test-Path $Work){throw "exists $Work"}
New-Item -ItemType Directory $Work,"$Work\zone","$Work\main" | Out-Null
foreach($f in 'iw7_ship.exe','amd_ags_x64.dll','bink2w64.dll','d3dcompiler_46.dll','steam_api.dll','steam_api64.dll','Steam.dll'){Copy-Item "$g\$f" "$Work\$f"}
Copy-Item "$k\tlsdll.dll" "$Work\tlsdll.dll"
Copy-Item $ZoneTool "$Work\zonetool.exe"
Copy-Item "$g\main\fileSysCheck.cfg" "$Work\main\fileSysCheck.cfg"
Get-ChildItem $g -File | Where-Object { $_.Extension -in '.ff','.pak' } | ForEach-Object { New-Item -ItemType HardLink -Path "$Work\zone\$($_.Name)" -Target $_.FullName | Out-Null }
"ok $((Get-ChildItem "$Work\zone").Count) zone files"
