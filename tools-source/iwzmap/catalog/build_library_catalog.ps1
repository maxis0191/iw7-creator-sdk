# builds the library catalogue over every dump on disk (about 30 s): .\build_library_catalog.ps1 [-Out <catalog.json>]
param([string]$Runtime = (Join-Path $env:USERPROFILE 'Documents\IW7-Runtime'), [string]$Out)
if (-not $Out) { $Out = Join-Path $Runtime 'iwz-blend\library\catalog.json' }
$ref = Join-Path $Runtime 'iwz-map-ref-a\dump'; $kit = Join-Path $Runtime 'iwz-stage2\kitimport\ztwork\dump'
$game = (Get-ChildItem (Join-Path $Runtime 'bench') -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'imagefile19.pak') } | Select-Object -First 1).FullName
$ch = Join-Path $Runtime 'chars58\ztwork\dump'
$gl = "$ref\techsets_global_cp;$ref\techsets_global"
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
python -I (Join-Path $PSScriptRoot 'iwzcat.py') build `
  --zone "cp_zmb=$ref\cp_zmb;$ref\patch_cp_zmb;$ref\techsets_cp_zmb;$gl" `
  --zone "cp_disco=$kit\cp_disco;$kit\techsets_cp_disco;$gl" `
  --zone "cp_final=$kit\cp_final;$kit\techsets_cp_final;$gl" `
  --zone "cp_rave=$ch\cp_rave;$ch\patch_cp_rave;$ch\techsets_cp_rave;$gl" `
  --zone "cp_town=$ch\cp_town;$ch\patch_cp_town;$ch\techsets_cp_town;$gl" `
  --zone "global_cp=$ref\global_cp;$gl" `
  --zone "global_core_mp=$ref\global_core_mp;$ref\techsets_global_core_mp" `
  --zone "common_core_mp=$ref\common_core_mp;$ref\techsets_common_core_mp;$ref\techsets_global_core_mp" `
  --zone "mp_frontend=$ref\mp_frontend;$ref\techsets_common_mp;$ref\techsets_global_mp" `
  --zone "patch_cp_frontend=$ref\patch_cp_frontend;$ref\techsets_global_cp" `
  --always-loaded cp_zmb,global_cp,global --shared "$ref\global_cp;$ref\global" `
  --base-paks $game --placements (Join-Path $Runtime 'worldkit\cp_zmb.sqlite') --out $Out
