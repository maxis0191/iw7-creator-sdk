# Pure argument/identity tests. No process, executable read, native type or lease.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'SpawnTip.Profile.ps1')
$passed=0
function Check([bool]$Value,[string]$Reason){if(!$Value){throw $Reason};$script:passed++}
function Refuses([scriptblock]$Action,[string]$Reason){
    $refused=$false
    try{& $Action|Out-Null}catch{$refused=$true}
    Check $refused $Reason
}
$image='C:\synthetic\pwsh.exe';$entry='C:\synthetic\Run-SpawnTip.ps1'
$plan='C:\synthetic\plan.json';$hash='a'*64
$argvExact=@($image,'-NoProfile','-NoExit','-File',$entry,'-PlanPath',$plan,'-PlanSHA256',$hash,'-Run')
$proof=Assert-SpawnTipHostArguments $argvExact $image $image $entry $plan $hash
Check ($proof.Image -ceq $image -and $proof.NoProfile -and $proof.NoExit -and $proof.DirectFileLaunch -and $proof.ExactArgumentsVerified) 'Exact host witness missing.'
$managed=$argvExact.Clone();$managed[0]='C:\synthetic\pwsh.dll'
$proof=Assert-SpawnTipHostArguments $managed $image $image $entry $plan $hash
Check ($proof.Image -ceq $image -and $proof.ExactArgumentsVerified) 'Managed argv[0] was confused with the executable.'
Refuses {Assert-SpawnTipHostArguments $managed 'C:\wrong\pwsh.exe' $image $entry $plan $hash} 'Managed argv accepted a different MainModule image.'
Refuses {Assert-SpawnTipHostArguments $argvExact 'C:\wrong\pwsh.exe' $image $entry $plan $hash} 'Expected argv[0] masked a different executable.'
foreach($index in 1..($argvExact.Count-1)) {
    $changed=$argvExact.Clone();$changed[$index]='wrong'
    Refuses {Assert-SpawnTipHostArguments $changed $image $image $entry $plan $hash} ('Changed argument accepted: '+$index)
}
$missing=@($argvExact[0..1])+@($argvExact[3..9])
Refuses {Assert-SpawnTipHostArguments $missing $image $image $entry $plan $hash} 'Missing NoExit accepted.'
$after=@($missing)+@('-NoExit')
Refuses {Assert-SpawnTipHostArguments $after $image $image $entry $plan $hash} 'NoExit after the script was treated as a host switch.'
$tricky='C:\synthetic\folder -NoExit payload\plan.json'
$pathOnly=@($image,'-NoProfile','-File',$entry,'-PlanPath',$tricky,'-PlanSHA256',$hash,'-Run')
# Preserve the original regression: quoted raw text matched even without a switch.
$raw='"'+$image+'" -NoProfile -File "'+$entry+'" -PlanPath "'+$tricky+'" -PlanSHA256 '+$hash+' -Run'
Check ($raw -match '(?i)(?:^|\s)-NoExit(?:\s|$)') 'Regression fixture does not reproduce the old raw-string bug.'
Refuses {Assert-SpawnTipHostArguments $pathOnly $image $image $entry $tricky $hash} 'Path text was treated as a host switch.'
$trickyValid=$argvExact.Clone();$trickyValid[6]=$tricky
$proof=Assert-SpawnTipHostArguments $trickyValid $image $image $entry $tricky $hash
Check $proof.ExactArgumentsVerified 'Opaque path argument with real NoExit should remain valid.'
$embedded=$argvExact.Clone();$embedded[2]='prefix -NoExit suffix'
Refuses {Assert-SpawnTipHostArguments $embedded $image $image $entry $plan $hash} 'An embedded switch string was accepted as a token.'
Refuses {Assert-SpawnTipHostArguments ($argvExact+@('extra')) $image $image $entry $plan $hash} 'Additional argument accepted.'
$command=$argvExact.Clone();$command[3]='-Command'
Refuses {Assert-SpawnTipHostArguments $command $image $image $entry $plan $hash} 'Command launch accepted as direct File launch.'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Run-SpawnTip.ps1') -Raw
Check ($source.Contains('[Environment]::GetCommandLineArgs()') -and !$source.Contains('[Environment]::CommandLine ')) 'Entry did not replace raw-string validation.'
Check ($source.IndexOf('$hostContract=Assert-SpawnTipHostArguments') -lt $source.IndexOf('. $script:SpawnTipPins.Scheduler.Path')) 'Host proof must precede scheduler import/admission.'
[ordered]@{Schema='iw7.spawn-tip-host-source-tests/1';Assertions=$passed;RealHostLaunched=$false;BinaryInputsRead=$false;LeaseAcquired=$false}|ConvertTo-Json
