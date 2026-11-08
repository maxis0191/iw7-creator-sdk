param(
  [Parameter(Mandatory)][string]$Tag,                         # run name: <Runs>\<Tag> (must not exist)
  [Parameter(Mandatory)][string]$UsermapDir,                  # cp_iwz.ff + cp_iwz.arena
  [ValidateSet('views','walk','gameplay','walkcap')][string]$Mode='views',
  [string]$Fixture,                                           # views/walk: the generated iwzmap_sz2_local.gsc; gameplay: the gameplay fixture
  [string]$Only='',                                           # views: capture only names containing this text
  [string]$Part='0/1',                                        # walkcap: part k/n of the walkthrough positions
  [string]$Ab='',                                             # views: A/B commands ("cmd|cmd"): each view captured as is and as <name>_b after them
  [string]$AbReset='',                                        # views: commands run after each B capture
  [string]$DvarProbe='',                                      # dvar names ("a|b|c") printed with their value at spawn ([IWZ local] DVAR)
  [int]$Seconds=420,
  [string]$Runs='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level\runs',
  [string]$Server='C:\Users\ezvalo\Documents\IW7-Paris-Server\.claude\worktrees\custom-zombies-map-iwz-26cd2d',
  [string]$SourcePackage='C:\Users\ezvalo\AppData\Local\Temp\claude\ffc8c2fd82d25eb3\3d781a32-1ec5-4875-9f47-5fae74b66b77\scratchpad\srcpkg-a',
  [string]$InjectDll='C:\Users\ezvalo\AppData\Local\Temp\claude\ffc8c2fd82d25eb3\3d781a32-1ec5-4875-9f47-5fae74b66b77\scratchpad\errjournal\iw7_error_journal.dll',
  [string]$GameRoot='C:\Users\ezvalo\Desktop\iw_game_files',
  [int]$Tries=60)
# Short leased private local session of Station Zero v2 through the server's local runner (sv_lanOnly, random password,
# loopback, private desktop, staged files restored). Waits while the game or the runtime lease is taken.
$ErrorActionPreference='Stop'
$out=Join-Path $Runs $Tag
$extra='+set vid_width 1920 +set vid_height 1080 +set r_mode 1920x1080 +set cg_fov 65'
switch($Mode){
  'views'    { $extra+=' +set paris_iwz_mode views +set paris_iwz_noweapons 1 +set paris_iwz_fxhold 1 +set paris_iwz_cmds "cg_draw2D 0"'; if($Only){ $extra+=" +set paris_iwz_only $Only" }
               if($Ab){ $extra+=" +set paris_iwz_ab `"$Ab`"" }; if($AbReset){ $extra+=" +set paris_iwz_ab_reset `"$AbReset`"" } }
  'walk'     { $extra+=' +set paris_iwz_mode walk' }
  'walkcap'  { $extra+=" +set paris_iwz_mode walkcap +set paris_iwz_noweapons 1 +set paris_iwz_wc_part $Part" + ' +set paris_iwz_cmds "cg_draw2D 0"' }
  'gameplay' { $extra+=' +set paris_iwz_gameplay 1 +set paris_iwz_autouse 1 +set developer_script 1' }
}
if($DvarProbe){ $extra+=" +set paris_iwz_dvarprobe `"$DvarProbe`"" }
for($k=0;$k -lt $Tries;$k++){
  $main=(Resolve-Path $GameRoot).Path
  $busy=@(Get-CimInstance Win32_Process|Where-Object {$_.ExecutablePath -and $_.ExecutablePath.StartsWith($main+'\',[StringComparison]::OrdinalIgnoreCase)}).Count
  if($busy){ "game occupied, waiting"; Start-Sleep 10; continue }
  try {
    $r = & "$Server\ops\iwzmap\Test-IWZMapLocal.ps1" -SourcePackage $SourcePackage -GameRoot $GameRoot -OutputRoot $out -UsermapDir $UsermapDir -Map cp_iwz -Fixture $Fixture -ExtraArgs $extra -Seconds $Seconds -InjectDll $InjectDll
    $r
    $j = Get-Content (Join-Path $out 'result.local.json') -Raw | ConvertFrom-Json
    if($j.Error -match 'Resource busy|Heavy job already reserved|occupied|wait before heavy admission|wait for its owner|Unowned local image|Unattached lab process|Resource lease not found|Child identity unavailable|Reserved process identity unavailable|Reserved child is still alive|Heavy child may still be alive'){ Remove-Item $out -Recurse -Force; Start-Sleep 10; continue }
    break
  } catch {
    if($_.Exception.Message -match 'Resource busy|Heavy job already reserved|occupied|wait before heavy admission|wait for its owner|Unowned local image|Unattached lab process|Resource lease not found|Child identity unavailable|Reserved process identity unavailable|Reserved child is still alive|Heavy child may still be alive'){ if(Test-Path $out){ Remove-Item $out -Recurse -Force }; Start-Sleep 10; continue }
    throw
  }
}
