# Default Plan is source-only. A separately reviewed exact-plan GO enables -Run.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$PlanPath,[Parameter(Mandatory)][string]$PlanSHA256,[switch]$Run)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
if(!$IsWindows -or [IntPtr]::Size -ne 8 -or $PSVersionTable.PSVersion.Major -lt 7){throw 'Windows x64 PowerShell 7 required.'}
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$guards=[Collections.Generic.List[object]]::new();$retain=$false
function Open-SpawnTipBootstrap($Path,[long]$Bytes,[string]$Hash) {
    if(![IO.Path]::IsPathFullyQualified($Path) -or [IO.Path]::GetFullPath($Path) -cne $Path -or $Path -match '["\r\n]'){throw 'Canonical bootstrap path required.'}
    for($p=$Path;$p;$p=[IO.Path]::GetDirectoryName($p)){if(([IO.File]::GetAttributes($p) -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Redirected bootstrap refused.'}}
    if($Bytes -le 0 -or $Bytes -gt 2MB -or $Hash -cnotmatch '^[0-9a-f]{64}$'){throw 'Bounded bootstrap source pin required.'}
    $s=[IO.FileStream]::new($Path,'Open','Read','Read');$guards.Add($s)
    if($s.Length -ne $Bytes){throw 'Bootstrap length differs.'}
    $h=[Security.Cryptography.SHA256]::Create();try{$actual=[Convert]::ToHexString($h.ComputeHash($s)).ToLowerInvariant()}finally{$h.Dispose()}
    if($actual -cne $Hash){throw 'Bootstrap hash differs.'};$s.Position=0;return $s
}
function Assert-SpawnTipUniqueJson($Node,[int]$Depth=0) {
    if($Depth -gt 20){throw 'Plan JSON depth exceeded.'}
    if($Node.ValueKind -eq [System.Text.Json.JsonValueKind]::Object){
        $names=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach($p in $Node.EnumerateObject()){if(!$names.Add($p.Name)){throw 'Duplicate plan JSON key.'};Assert-SpawnTipUniqueJson $p.Value ($Depth+1)}
    }elseif($Node.ValueKind -eq [System.Text.Json.JsonValueKind]::Array){foreach($n in $Node.EnumerateArray()){Assert-SpawnTipUniqueJson $n ($Depth+1)}}
}
try {
    $size=(Get-Item -LiteralPath $PlanPath).Length
    if($size -gt 128KB){throw 'Plan exceeds 128 KiB.'}
    $stream=Open-SpawnTipBootstrap $PlanPath $size $PlanSHA256
    $reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,4096,$true)
    try{$json=$reader.ReadToEnd()}finally{$reader.Dispose()}
    $doc=[System.Text.Json.JsonDocument]::Parse($json);try{Assert-SpawnTipUniqueJson $doc.RootElement}finally{$doc.Dispose()}
    $plan=$json|ConvertFrom-Json -Depth 20
    $core=Join-Path $repo 'tools-source/asset-bridge/h1-fixture/H1Native.Core.ps1'
    $profile=Join-Path $PSScriptRoot 'SpawnTip.Profile.ps1'
    foreach($path in @($PSCommandPath,$core,$profile)) {
        $pin=@($plan.Bindings|Where-Object {$_.Path -ceq $path -and $_.IsText -is [bool] -and $_.IsText})
        if($pin.Count -ne 1){throw 'Exact bootstrap binding missing.'}
        $null=Open-SpawnTipBootstrap $path $pin[0].Bytes $pin[0].SHA256
    }
    . $core
    . $profile
    Assert-SpawnTipPlan $plan $repo $PSCommandPath
    foreach($pin in $plan.Bindings|Where-Object IsText){$guards.Add((Open-H1Pin $pin))}
    if(!$Run){[ordered]@{Status='PlanCheckedPendingGO';TextBindings=23;BinaryInputsRead=$false;LeaseAcquired=$false;FilesCreated=$false;RuntimeReady=$false}|ConvertTo-Json;return}
    # Keep the original host and in-memory H1 quarantine reachable on uncertainty.
    $hostContract=Assert-SpawnTipHostArguments ([Environment]::GetCommandLineArgs()) `
        ([Diagnostics.Process]::GetCurrentProcess().MainModule.FileName) $script:SpawnTipPins.Host.Path $PSCommandPath $PlanPath $PlanSHA256
    if(('IW7.AnimationProbe.NativeJob' -as [type]) -or ('IW7ResourceMemoryV1' -as [type])){throw 'Fresh host required.'}
    . $script:SpawnTipPins.Scheduler.Path
    $script:SpawnTipPlanPath=$PlanPath
    $retain=$true # An unexpected supervisor exception must retain input guards.
    $result=Invoke-SpawnTipRun $plan $PlanSHA256 $guards
    $retain=(!$result.Context.Closed -or $null -ne $result.Context.Lease)
    $result.State|ConvertTo-Json -Depth 16
    if($retain){throw 'Original job/admission quarantined: retain this host and guards; no PID kill or lease deletion.'}
    if($result.Failure){throw $result.Failure}
}finally{if(!$retain -and $guards.Count){foreach($g in $guards){$g.Dispose()};$guards.Clear()}}
