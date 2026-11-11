param([Parameter(Mandatory)][string]$Work,[Parameter(Mandatory)][string[]]$ZtArgs,[string]$Owner='IWZ custom map zonetool',[int]$TimeoutSec=1200,
  [string]$Scheduler='',                                 # Resource-Scheduler.Core.ps1; empty: scheduler.ps1 resolves and guards it
  [ValidateRange(0,14400)][int]$WaitForSlotSeconds=0)    # wait this long for the shared reservation, asking the scheduler every 5 s
# One ZoneTool run under the machine-wide build reservation.
$ErrorActionPreference='Stop'
. (& "$PSScriptRoot\scheduler.ps1" $Scheduler)
$waitClock=[Diagnostics.Stopwatch]::StartNew()
$until=[datetime]::UtcNow.AddSeconds($WaitForSlotSeconds)
# Ask the scheduler itself every 5 s, never only look at its status: since 11 Nov 2026 a refused request that asks
# again keeps its place in the scheduler's waiting order, and a waiting build stops new sessions until it is served.
# A build that only looked at the status until nothing was held never got a place and waited 25 to 75 minutes behind
# other agents' back-to-back sessions. A busy slot and a compiler or extractor running without a reservation are
# asked again; any other refusal is thrown at once.
$lease=$null
while(-not $lease){
  try{ $lease=Enter-IW7ResourceLease -Scope $Work -Kind Build -PhysicalBytes 6GB -CommitBytes 8GB -Owner $Owner }
  catch{
    # The scheduler names its own retryable refusals (Test-IW7RetryableRefusal, with the waiting order): use them. On
    # 11 Nov 2026 a dump stopped on 'Reserved process identity unavailable; reservation retained.' (another agent's
    # leased process ending), a refusal the scheduler counts as a wait, while this loop knew only two others.
    $busy=if(Get-Command Test-IW7RetryableRefusal -ErrorAction SilentlyContinue){ Test-IW7RetryableRefusal $_.Exception.Message }
      else{ $_.Exception.Message -like 'Resource busy:*' -or $_.Exception.Message -like 'An existing compiler/extractor/Java analysis is running;*' }
    # the scheduler's admission lock held by another caller for its 5 s bound is a moment of contention, not a refusal
    # (11 Nov 2026: a queued P1 dump stopped on it after 20 min of waiting; server runners: PR #478)
    if($_.Exception.Message -like 'Resource admission lock busy*'){ $busy=$true }
    if(!$busy -or $WaitForSlotSeconds -le 0 -or [datetime]::UtcNow -ge $until){ throw }
    Start-Sleep -Seconds 5
  }
}
"waited for the build reservation $([int]$waitClock.Elapsed.TotalSeconds) s"
try{
  $tag=[DateTime]::UtcNow.ToString('HHmmss')
  # The log goes straight to a file through cmd.exe. Start-Process -RedirectStandardOutput pipes it through PowerShell,
  # and ZoneTool writes every line unbuffered: on 11 Nov 2026 the prefab room's zone step took 337 s that way and 49 s
  # with this redirection, same content (ff_compare.py). Standard input is NUL: nothing reads it in a headless run.
  $q={ param($a) if($a -match '[\s"]'){ '"'+($a -replace '"','\"')+'"' } else { $a } }
  $line=((@("$Work\zonetool.exe",'-headless','-unbuffered-io')+$ZtArgs) | ForEach-Object { & $q $_ }) -join ' '
  $p=Start-Process -FilePath "$env:ComSpec" -ArgumentList "/d /s /c `"$line < NUL > `"$Work\zt-$tag.out.log`" 2> `"$Work\zt-$tag.err.log`"`"" -WorkingDirectory $Work -PassThru -WindowStyle Hidden
  $zt=$null; for($k=0;$k -lt 50 -and -not $zt;$k++){ $zt=Get-CimInstance Win32_Process -Filter "ParentProcessId=$($p.Id) AND Name='zonetool.exe'" | Select-Object -First 1; if(-not $zt){ Start-Sleep -Milliseconds 200 } }
  if($zt){ try{ Add-IW7ResourceProcess -Token $lease.Token -ProcessId $zt.ProcessId | Out-Null }catch{} }
  try{ Add-IW7ResourceProcess -Token $lease.Token -ProcessId $p.Id | Out-Null }catch{}
  # time stamps for every log line (zt_timeline.py report <file> says where the minutes went)
  try{ Start-Process -FilePath python -ArgumentList @('-I',"`"$PSScriptRoot\zt_timeline.py`"",'follow',"`"$Work\zt-$tag.out.log`"","`"$Work\zt-$tag.timeline.tsv`"",'--pid',"$($p.Id)") -WindowStyle Hidden | Out-Null }catch{}
  $deadline=[datetime]::UtcNow.AddSeconds($TimeoutSec)
  # A game error inside ZoneTool (Com_Error) opens a hidden "Fatal Error" message box and waits on it forever; nothing
  # reaches the log. Measured 11 Nov 2026: a dump of four patch zones in one run stopped on "Exceeded limit of 16
  # 'animclass' assets." and used a core for 23 minutes. The windows of our ZoneTool are read every 10 s: such a box
  # ends the run at once, with its text in the log and on the output.
  if(-not ('ZtDialog' -as [type])){
    Add-Type @'
using System;using System.Text;using System.Runtime.InteropServices;
public static class ZtDialog{public delegate bool P(IntPtr h,IntPtr l);
[DllImport("user32.dll")]static extern bool EnumWindows(P f,IntPtr l);
[DllImport("user32.dll")]static extern bool EnumChildWindows(IntPtr w,P f,IntPtr l);
[DllImport("user32.dll")]static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
[DllImport("user32.dll",CharSet=CharSet.Unicode)]static extern int GetWindowText(IntPtr h,StringBuilder s,int n);
public static string Fatal(uint pid){string r=null;EnumWindows((h,l)=>{uint p;GetWindowThreadProcessId(h,out p);if(p!=pid)return true;
var t=new StringBuilder(256);GetWindowText(h,t,256);if(!t.ToString().Contains("Error"))return true;var b=new StringBuilder(t.ToString());
EnumChildWindows(h,(c,m)=>{var s=new StringBuilder(4096);GetWindowText(c,s,4096);if(s.Length>0&&s.ToString()!="OK")b.Append(": "+s);return true;},IntPtr.Zero);
r=b.ToString();return false;},IntPtr.Zero);return r;}}
'@
  }
  $dialogAt=[datetime]::UtcNow
  while(-not $p.WaitForExit(2000)){
    $log = Get-Content "$Work\zt-$tag.out.log" -Raw -ErrorAction SilentlyContinue
    if($log -and $log.Contains('[ FATAL ]')){ Start-Sleep 2; if(-not $p.HasExited){ if($zt){ Stop-Process -Id $zt.ProcessId -Force -ErrorAction SilentlyContinue }; $p.Kill() }; "FATAL"; break }
    if($zt -and [datetime]::UtcNow -ge $dialogAt){
      $dialogAt=[datetime]::UtcNow.AddSeconds(10)
      $box=[ZtDialog]::Fatal([uint32]$zt.ProcessId)
      if($box){
        Stop-Process -Id $zt.ProcessId -Force -ErrorAction SilentlyContinue; if(-not $p.HasExited){ $p.Kill() }; $p.WaitForExit(10000) | Out-Null
        try{ Add-Content -LiteralPath "$Work\zt-$tag.out.log" -Value "[ FATAL ][ zt.ps1 ]: game error dialog: $box" }catch{}
        "FATAL (dialog) $box"; break
      }
    }
    if([datetime]::UtcNow -gt $deadline){ if($zt){ Stop-Process -Id $zt.ProcessId -Force -ErrorAction SilentlyContinue }; $p.Kill(); "TIMEOUT"; break }
  }
  $p.WaitForExit(10000) | Out-Null
  "exit $($p.ExitCode)"; Get-Content "$Work\zt-$tag.out.log" -Tail 25; Get-Content "$Work\zt-$tag.err.log" -Tail 10
} finally {
  # The scheduler keeps a Build lease while ANY compiler runs on the machine, ours or not ('Heavy child may still be
  # alive'). Once our ZoneTool has exited, ask again every 5 s for up to 30 min instead of leaving the lease behind.
  $released=$false; $exitUntil=[datetime]::UtcNow.AddMinutes(30)
  while(-not $released){
    try{ Exit-IW7ResourceLease -Token $lease.Token | Out-Null; $released=$true }
    catch{
      if(-not ($p -and $p.HasExited) -or $_.Exception.Message -notlike 'Heavy child may still be alive*' -or [datetime]::UtcNow -ge $exitUntil){ throw }
      Start-Sleep -Seconds 5
    }
  }
}
