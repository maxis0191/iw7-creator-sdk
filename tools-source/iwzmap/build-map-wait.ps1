param([string]$UmOut, [switch]$Zt, [int]$Tries=120, [string]$Src=(Join-Path $PSScriptRoot 'out\sz_src'), [string]$Out=(Join-Path $PSScriptRoot 'out'), [string]$Arena)
# Builds zonetool (optional) and the map with the generated tome, waiting while another owner holds the resource lease.
$S=$PSScriptRoot
for($k=0;$k -lt $Tries;$k++){
  try {
    if($Zt){ $b=& "$S\build-zt.ps1"; if(($b -join "`n") -notmatch 'exit 0'){ $b; throw 'zonetool build failed' }; $Zt=$false; 'zonetool built' }
    $env:IWZ_GEN_TOME='1'; $env:IWZ_KEEP_ENTSHAPES='1'
    try { $p = & "$S\pipeline.ps1" -Src $Src -Script "$S\cp_iwz.gsc" -Out $Out -NoProbe -Fresh 2>&1 } finally { Remove-Item Env:IWZ_GEN_TOME,Env:IWZ_KEEP_ENTSHAPES -ErrorAction SilentlyContinue }
    $p | Select-Object -Last 4
    $log=Get-ChildItem (& "$PSScriptRoot\machine.ps1" Runtime 'iwz-map-m2-a') -Filter 'zt-*.out.log' | Sort-Object LastWriteTime | Select-Object -Last 2
    $log | ForEach-Object { Select-String -Path $_.FullName -Pattern 'relit|Umbra tome|Successfully compiled' | ForEach-Object Line }
    if($UmOut){ New-Item -ItemType Directory $UmOut -Force | Out-Null; Copy-Item (Join-Path $Out 'um_cp_iwz\cp_iwz.ff') "$UmOut\cp_iwz.ff" -Force; if($Arena){ Copy-Item $Arena "$UmOut\cp_iwz.arena" -Force }; "copied to $UmOut" }
    break
  } catch {
    if($_.Exception.Message -match 'Resource busy|Heavy job already reserved'){ Start-Sleep 60; continue }
    throw
  }
}
