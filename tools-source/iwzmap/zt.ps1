param([Parameter(Mandatory)][string]$Work,[Parameter(Mandatory)][string[]]$ZtArgs,[string]$Owner='IWZ custom map zonetool',[int]$TimeoutSec=1200,
  [string]$Scheduler=$env:IW7_RESOURCE_SCHEDULER,        # Resource-Scheduler.Core.ps1 of iw7-mod-components (or of prepared inputs: <inputs>\ops)
  [ValidateRange(0,14400)][int]$WaitForSlotSeconds=0)    # wait this long for the shared reservation to be free (read-only look every 5 s), then ask once
# One ZoneTool run under the machine-wide build reservation. Nothing here retries a refused reservation.
$ErrorActionPreference='Stop'
if(!$Scheduler){
  # no machine path: the components checkout next to this repository (or next to the folder of worktrees it is in)
  foreach($c in @((Join-Path $PSScriptRoot '..\..\..\iw7-mod-components\ops\Resource-Scheduler.Core.ps1'),(Join-Path $PSScriptRoot '..\..\..\..\iw7-mod-components\ops\Resource-Scheduler.Core.ps1'))){
    if(Test-Path -LiteralPath $c){ $Scheduler=(Resolve-Path -LiteralPath $c).Path; break }
  }
}
if(!$Scheduler -or !(Test-Path -LiteralPath $Scheduler)){ throw 'Resource scheduler not found: pass -Scheduler or set IW7_RESOURCE_SCHEDULER.' }
. $Scheduler
if($WaitForSlotSeconds -gt 0){
  $until=[datetime]::UtcNow.AddSeconds($WaitForSlotSeconds)
  while(@((Get-IW7ResourceStatus).Leases).Count -and [datetime]::UtcNow -lt $until){ Start-Sleep -Seconds 5 }
}
$lease=Enter-IW7ResourceLease -Scope $Work -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner $Owner
try{
  $tag=[DateTime]::UtcNow.ToString('HHmmss')
  $p=Start-Process -FilePath "$Work\zonetool.exe" -ArgumentList (@('-headless','-unbuffered-io')+$ZtArgs) -WorkingDirectory $Work -RedirectStandardOutput "$Work\zt-$tag.out.log" -RedirectStandardError "$Work\zt-$tag.err.log" -PassThru -NoNewWindow
  try{ Add-IW7ResourceProcess -Token $lease.Token -ProcessId $p.Id | Out-Null }catch{}
  $deadline=[datetime]::UtcNow.AddSeconds($TimeoutSec)
  while(-not $p.WaitForExit(2000)){
    $log = Get-Content "$Work\zt-$tag.out.log" -Raw -ErrorAction SilentlyContinue
    if($log -and $log.Contains('[ FATAL ]')){ Start-Sleep 2; if(-not $p.HasExited){ $p.Kill() }; "FATAL"; break }
    if([datetime]::UtcNow -gt $deadline){ $p.Kill(); "TIMEOUT"; break }
  }
  $p.WaitForExit(10000) | Out-Null
  "exit $($p.ExitCode)"; Get-Content "$Work\zt-$tag.out.log" -Tail 25; Get-Content "$Work\zt-$tag.err.log" -Tail 10
} finally { Exit-IW7ResourceLease -Token $lease.Token | Out-Null }
