param(
  [Parameter(Mandatory)][string]$Tag,                  # run folder name under fx\runs (must not exist)
  [Parameter(Mandatory)][string]$UsermapDir,           # dir with cp_iwz.ff/.arena, or '-' for a stock map
  [string]$Map='cp_iwz',
  [Parameter(Mandatory)][string]$Fixture,
  [string]$Extra='',
  [int]$Seconds=420,
  [string]$DllEnv='',                                  # "NAME=value|NAME=value" set for the injected diagnostic DLL
  [string]$InjectDll='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\tools\fxperf\iw7_fxperf.dll',
  [int]$MaxWaitMinutes=180)
# FX agent: one short private local session through the server's runner (lease, lock, staged files restored).
# Retries every 60 s while the runtime lease / lock is busy or another agent's test client runs; stops (exit 3)
# when the base game is occupied by anything else (the owner's game).
$ErrorActionPreference='Stop'
$Runs='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\runs'
$Server='C:\Users\ezvalo\Documents\IW7-Paris-Server\.claude\worktrees\custom-zombies-map-iwz-26cd2d'
$Pkg='C:\Users\ezvalo\AppData\Local\Temp\claude\ffc8c2fd82d25eb3\3d781a32-1ec5-4875-9f47-5fae74b66b77\scratchpad\srcpkg-a'
$Game='C:\Users\ezvalo\Desktop\iw_game_files'
$out=Join-Path $Runs $Tag
$t0=Get-Date
$busyRx='Resource busy|Heavy job already reserved|wait before heavy admission|wait for its owner|Unowned local image|Unattached lab process|Resource lease not found|Child identity unavailable|Reserved process identity unavailable|Base game occupied|Reserved child is still alive|lease retained'
while($true){
  $procs=@(Get-CimInstance Win32_Process|Where-Object {$_.ExecutablePath -and $_.ExecutablePath.StartsWith($Game+'\',[StringComparison]::OrdinalIgnoreCase)})
  # other agents' private test clients (copied images) wait; anything else is the owner's game
  $foreign=@($procs|Where-Object {$_.Name -notmatch '^iw7-iwzmap-local\.exe$|bo3wpn|-test-client|-lab'})
  if($foreign.Count){ "OWNER_GAME: base game occupied by $(($foreign|ForEach-Object {"$($_.ProcessId):$($_.Name)"}) -join ','); stopping"; exit 3 }
  if($procs.Count -or ((Get-Date)-$t0).TotalMinutes -gt $MaxWaitMinutes){
    if(((Get-Date)-$t0).TotalMinutes -gt $MaxWaitMinutes){ 'gave up waiting'; exit 4 }
    Start-Sleep 10; continue    # another agent's test client: poll for a gap every 10 s (no lease attempt meanwhile)
  }
  foreach($kv in ($DllEnv -split '[|]'|Where-Object {$_})){ $k,$v=$kv -split '=',2; Set-Item "Env:$k" $v }
  try {
    $r = & "$Server\ops\iwzmap\Test-IWZMapLocal.ps1" -SourcePackage $Pkg -GameRoot $Game -OutputRoot $out -UsermapDir $UsermapDir -Map $Map -Fixture $Fixture -ExtraArgs $Extra -Seconds $Seconds -InjectDll $InjectDll
    $j=Get-Content (Join-Path $out 'result.local.json') -Raw | ConvertFrom-Json
    if($j.Error -match $busyRx){ "busy: $($j.Error)"; Remove-Item $out -Recurse -Force; Start-Sleep 60; continue }
    $r | Select-Object -First 8
    "RUN $Tag FF=$($j.FFSHA256) InGame=$($j.InGame) Restored=$($j.Restored) Error=$($j.Error) RestoreSkipped=$($j.RestoreSkipped)"
    if($j.RestoreSkipped){ 'OWNER_GAME: the owner started the base game during the run'; exit 3 }
    break
  } catch {
    if($_.Exception.Message -match $busyRx){ "busy: $($_.Exception.Message)"; if(Test-Path $out){ Remove-Item $out -Recurse -Force }; Start-Sleep 60; continue }
    throw
  } finally { foreach($kv in ($DllEnv -split '[|]'|Where-Object {$_})){ $k=($kv -split '=',2)[0]; Remove-Item "Env:$k" -ErrorAction SilentlyContinue } }
}
