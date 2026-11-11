param([string]$Path='')   # an explicit Resource-Scheduler.Core.ps1 (a script's -Scheduler parameter); empty: resolve
# The one place where the map tools find the machine's resource scheduler core. Prints its path after the guard;
# the caller dot-sources it: . (& "$PSScriptRoot\scheduler.ps1")
#
# Order: -Path; else $env:IW7_RESOURCE_SCHEDULER; else the core of the prepared workspace this script runs from
# (bootstrap.ps1 composes ops\Resource-Scheduler.Core.ps1 at the components pin of product.json); else
# $env:IWZ_COMPONENTS\ops\Resource-Scheduler.Core.ps1. There is no default checkout: the main components checkout
# was 11 commits behind on 11 Nov 2026, and a build that loaded it took the machine ahead of every queued caller.
#
# Guard: the core must define the waiting order (Assert-IW7QueueTurn, components PR 129) and the fit rule
# (Test-IW7TicketCanFit, components PR 130, pin a0990f32). An older core neither keeps a place in the queue nor
# refuses a request that can never fit, so it is refused here before anything of it is loaded. The check reads the
# file text only: nothing of the core runs, no lease or scheduler state is touched.
$ErrorActionPreference='Stop'
$markers=[ordered]@{
  'Assert-IW7QueueTurn'='the waiting order (requests are served in arrival order)'
  'Test-IW7TicketCanFit'='the fit rule (a request that can never fit is refused at once)'
}
$from=''
if($Path){ $from='the -Scheduler parameter' }
elseif($env:IW7_RESOURCE_SCHEDULER){ $Path=$env:IW7_RESOURCE_SCHEDULER; $from='$env:IW7_RESOURCE_SCHEDULER' }
else{
  $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
  if(Test-Path -LiteralPath (Join-Path $root 'source-workspace.json')){
    $Path=Join-Path $root 'ops\Resource-Scheduler.Core.ps1'; $from="the prepared workspace $root"
  } elseif($env:IWZ_COMPONENTS){
    $Path=Join-Path $env:IWZ_COMPONENTS 'ops\Resource-Scheduler.Core.ps1'; $from='$env:IWZ_COMPONENTS'
  } else {
    throw ("No resource scheduler core named. Run the map tools from a prepared workspace (./bootstrap.ps1 -Output runtime/<name>, " +
      "then tools-source\iwzmap there), or set `$env:IW7_RESOURCE_SCHEDULER to ops\Resource-Scheduler.Core.ps1 of a components " +
      "worktree that has the waiting order and the fit rule (pin/server-447c1ad-shareable, or origin/main once components PR 130 " +
      "is merged). The main components checkout is not used by default.")
  }
}
if(!(Test-Path -LiteralPath $Path -PathType Leaf)){ throw "Resource scheduler core not found: $Path (from $from)." }
$Path=(Resolve-Path -LiteralPath $Path).Path
$text=[IO.File]::ReadAllText($Path)
$missing=@($markers.Keys | Where-Object { $text -notmatch "(?m)^\s*function\s+$([regex]::Escape($_))\b" })
if($missing){
  $what=($missing | ForEach-Object { "$($markers[$_]) ($_)" }) -join ' and '
  throw ("Refused: the resource scheduler core $Path (from $from) is too old: it lacks $what, so a build started with it " +
    "would take the machine ahead of every queued caller. Point `$env:IW7_RESOURCE_SCHEDULER at the core of a fresh " +
    "components worktree that has both (git -C <iw7-mod-components> worktree add <folder> origin/pin/server-447c1ad-shareable, " +
    "or origin/main once components PR 130 is merged) or run the tools from a prepared workspace of this SDK.")
}
$Path
