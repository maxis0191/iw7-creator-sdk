param([Parameter(Mandatory)][string]$Work,[Parameter(Mandatory)][string[]]$ZtArgs,[string]$Owner='IWZ custom map zonetool',[int]$TimeoutSec=1200)
$ErrorActionPreference='Stop'
. (& "$PSScriptRoot\machine.ps1" Components 'ops\Resource-Scheduler.Core.ps1' -MustExist)
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
