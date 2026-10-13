# Dedicated policy only. Native ownership/registration/cleanup remains H1Native.
Set-StrictMode -Version Latest
function Assert-SpawnTipHostArguments([string[]]$ActualArguments,[string]$ActualImage,
    [string]$ExpectedImage,[string]$EntryPath,[string]$PlanPath,[string]$PlanSHA256) {
    # Reuse Assert-T7CatalogueHostArguments' exact argv policy, with this
    # profile's smaller argument tail. Do not parse/reconstruct quoted strings.
    $expected=@($ExpectedImage,'-NoProfile','-NoExit','-File',$EntryPath,
        '-PlanPath',$PlanPath,'-PlanSHA256',$PlanSHA256,'-Run')
    if($ActualImage -cne $ExpectedImage -or $ActualArguments.Count -ne $expected.Count){throw 'Exact NoProfile/NoExit/File host arguments and executable required.'}
    # Managed pwsh reports pwsh.dll at argv[0]. MainModule supplies the separate
    # executable identity; argv[0] cannot establish that identity or any switch.
    for($index=1;$index -lt $expected.Count;$index++) {
        if($ActualArguments[$index] -cne $expected[$index]){throw 'Exact NoProfile/NoExit/File host arguments and executable required.'}
    }
    [ordered]@{Image=$ActualImage;NoProfile=$true;NoExit=$true;DirectFileLaunch=$true;ExactArgumentsVerified=$true}
}
function Assert-SpawnTipPlan($Plan,[string]$Repo,[string]$Entry) {
    $keys='AuditLogBytes,AuditSeconds,AuditSource,BinaryInputsVerified,BinaryLimitBytes,Bindings,CommitBytes,CompilerLogBytes,CompileSeconds,DeadlineSeconds,EstimatesAreMeasured,MetadataReserveBytes,OutputLimitBytes,Payload,PhysicalBytes,ReferencePins,Repo,RunRoot,Schema,StackLimitBytes'
    if((@($Plan.PSObject.Properties.Name|Sort-Object)-join ',') -cne $keys -or
       $Plan.Schema -cne 'iw7.spawn-tip-plan/1' -or $Plan.Repo -cne $Repo){throw 'Exact spawn-tip plan shape required.'}
    foreach($key in 'BinaryInputsVerified','EstimatesAreMeasured') {
        if($Plan.$key -isnot [bool] -or $Plan.$key){throw 'Plan must not claim measured binaries/budgets.'}
    }
    $limits=@{PhysicalBytes=4GB;CommitBytes=6GB;DeadlineSeconds=180;CompileSeconds=20;AuditSeconds=60;
        OutputLimitBytes=64MB;MetadataReserveBytes=1MB;CompilerLogBytes=64KB;AuditLogBytes=4MB;
        BinaryLimitBytes=64KB;StackLimitBytes=128KB}
    foreach($key in $limits.Keys){if($Plan.$key -is [bool] -or $Plan.$key -ne $limits[$key]){throw ('Fixed reviewed bound differs: '+$key)}}
    if($Plan.Payload -cne 'iw7-mod/custom_scripts/cp/sdk_spawn_tip.gsc'){throw 'Source payload contract differs.'}
    Assert-H1Path $Plan.RunRoot;Assert-H1Path $Plan.AuditSource
    if([IO.Path]::GetDirectoryName($Plan.RunRoot) -cne (Join-Path $Repo 'runtime') -or (Test-Path -LiteralPath $Plan.RunRoot)){
        throw 'Fresh immediate runtime child required.'
    }
    $script:SpawnTipPins=@{}
    if(@($Plan.Bindings).Count -ne 28){throw 'Exact 28-file input inventory required.'}
    foreach($pin in $Plan.Bindings) {
        if((@($pin.PSObject.Properties.Name|Sort-Object)-join ',') -cne 'Bytes,IsText,Path,Role,SHA256' -or
           $pin.IsText -isnot [bool] -or $pin.Bytes -is [bool] -or $pin.Bytes -le 0 -or $pin.Bytes -gt 32MB -or
           $pin.SHA256 -cnotmatch '^[0-9a-f]{64}$' -or $script:SpawnTipPins.ContainsKey($pin.Role)){throw 'Invalid/repeated binding.'}
        Assert-H1Path $pin.Path;$script:SpawnTipPins[$pin.Role]=$pin
    }
    if(@($Plan.Bindings.Path|Sort-Object -Unique).Count -ne 28){throw 'Binding aliases refused.'}
    $relative=@{Runner='tools-source/gsc-spawn-tip/Run-SpawnTip.ps1';Profile='tools-source/gsc-spawn-tip/SpawnTip.Profile.ps1';
        Phase='tools-source/gsc-spawn-tip/spawn_tip.py';Core='tools-source/asset-bridge/h1-fixture/H1Native.Core.ps1';
        Scheduler='ops/Resource-Scheduler.Core.ps1';Memory='ops/Resource-Memory.ps1';Recorder='ops/Resource-RecorderOwnedProcess.Core.ps1';
        MemoryNative='ops/native/ResourceMemory.cs';JobSource='tools-source/asset-bridge/animation/Probe-NativeJob.cs';
        Consumption='sdk/modding/audit_gsc_consumption.py';Source='sdk/modding/examples/server-spawn-tip/sdk_spawn_tip.gsc'}
    foreach($role in $relative.Keys) {
        $pin=$script:SpawnTipPins[$role]
        if(!$pin -or !$pin.IsText -or $pin.Path -cne (Join-Path $Repo $relative[$role]) -or $pin.Bytes -gt 2MB){throw 'Repository source binding differs.'}
    }
    if($script:SpawnTipPins.Runner.Path -cne $Entry){throw 'Wrong entry point.'}
    $audit=Join-Path $Plan.AuditSource 'build/native-reference-qualification-20261012-v8'
    $auditPaths=@{References=(Join-Path $Plan.AuditSource 'audit/references.py');ReferenceProfile=(Join-Path $Plan.AuditSource 'audit/reference-profile.json');
        V8Build=(Join-Path $audit 'build-receipt.json');V8Supervision=(Join-Path $audit 'supervision.json')}
    foreach($role in $auditPaths.Keys){$pin=$script:SpawnTipPins[$role];if(!$pin -or !$pin.IsText -or $pin.Path -cne $auditPaths[$role] -or $pin.Bytes -gt 2MB){throw 'V8 source/receipt path differs.'}}
    $expected=@{
        Source='eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23';
        Consumption='42dd0dcb01c014cfbfbabb18d404d4c6ccd1b6d04ed27a5b16e63dde54e72d07';
        References='fdb52f27225c61b563a09cd710cfeca769a9d01a8c971b882edeb277efe98a7c';
        ReferenceProfile='e87230812b01059ece4327d9d465b8b20e5e1162d3cd698492aed70405bbf360';
        V8Build='7279357cf636295561ff66dd1e085372d93841147859073349868f89a7dcb6e7';
        V8Supervision='f1a1f3e42d3b3c10efca4cab804df91a756f8dac11bbb97f95289e8b29538575';
        JobSource='ddefa72ff2b98286cd585d1178c13e67dcd646bbcf39d51365660901366c5ca8'}
    foreach($role in $expected.Keys){if($script:SpawnTipPins[$role].SHA256 -cne $expected[$role]){throw ('Qualified text pin differs: '+$role)}}
    $binary=@{
        Compiler=@(23029248,'1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb');
        Auditor=@(1248768,'fbaeff90961d1c5c3aec5f293c6dcb7b9dd92ab049e6aebe3ea399b47a007211');
        Python=@(104952,'4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a');
        Host=@(301368,'362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139');
        JobAssembly=@(13312,'5f613ebb83019dbf4bfa4f6a93c5329098343729b70acc2cfa70aa8b64f195f8')}
    foreach($role in $binary.Keys){$pin=$script:SpawnTipPins[$role];if(!$pin -or $pin.IsText -or $pin.Bytes -ne $binary[$role][0] -or $pin.SHA256 -cne $binary[$role][1]){throw 'Expected binary pin differs.'}}
    if($script:SpawnTipPins.Auditor.Path -cne (Join-Path $audit 'native/Release/iw7-gsc-audit.exe')){throw 'Retained qualified V8 executable required.'}
    $profileGuard=Open-H1Pin $script:SpawnTipPins.ReferenceProfile
    try{$profile=Read-H1SmallJson $script:SpawnTipPins.ReferenceProfile.Path 64KB}finally{$profileGuard.Dispose()}
    if(@($profile.table_files).Count -ne 8){throw 'Eight exact physical table files required.'}
    for($i=0;$i -lt 8;$i++) {
        $pin=$script:SpawnTipPins['Table'+$i];$row=$profile.table_files[$i]
        if(!$pin -or !$pin.IsText -or $pin.Path -cne (Join-Path $Plan.AuditSource $row.path) -or $pin.SHA256 -cne $row.sha256 -or $pin.Bytes -gt 2MB){throw 'Physical V8 table binding differs.'}
    }
    $p=$Plan.ReferencePins
    if((@($p.PSObject.Properties.Name|Sort-Object)-join ',') -cne 'consumption_validator_sha256,decoder,profile_sha256,reference_validator_sha256' -or
       (@($p.decoder.PSObject.Properties.Name|Sort-Object)-join ',') -cne 'source_revision,source_sha256,tables_sha256,tool_sha256' -or
       $p.profile_sha256 -cne $expected.ReferenceProfile -or $p.reference_validator_sha256 -cne $expected.References -or
       $p.consumption_validator_sha256 -cne $expected.Consumption -or $p.decoder.tool_sha256 -cne $binary.Auditor[1] -or
       $p.decoder.source_revision -cne '03d3956d648b7aa4637fe1007f9d69ea463631e9' -or
       $p.decoder.source_sha256 -cne 'bd53e01813dd80d44c871108fa1a3730db1b03e89b084e818098f49f12352d51' -or
       $p.decoder.tables_sha256 -cne '6e3ed82737908b5c7be76290a178a66b5c63456a12097e964139154f4b46de4b'){throw 'Independent reference identity differs.'}
}

function Assert-SpawnTipChild($Report,$Plan,[string]$PlanSHA256,$State,$Context) {
    if($Report.Schema -cne 'iw7.spawn-tip-child/1' -or $Report.PlanSHA256 -cne $PlanSHA256 -or
       $Report.LeaseToken -cne $State.LeaseToken -or $Report.RunId -cne $State.RunId -or
       $Report.SourceSHA256 -cne $script:SpawnTipPins.Source.SHA256 -or $Report.InputSHA256 -cnotmatch '^[0-9a-f]{64}$') {throw 'Child receipt identity differs.'}
    foreach($key in 'EncodedReferenceAbsence','InputsReverified','ChildOnly') {if($Report.$key -isnot [bool] -or !$Report.$key){throw 'Child completion missing.'}}
    if($Report.JobClosureProven -isnot [bool] -or $Report.JobClosureProven){throw 'Child cannot attest job closure.'}
    foreach($key in 'asset_dependency_closure_verified','native_builtin_semantics_verified','runtime_validation_passed','owner_acceptance','package_ready'){
        if($Report.Limits.$key -isnot [bool] -or $Report.Limits.$key){throw 'Child overclaims runtime/package scope.'}
    }
    $phase=Join-Path $Plan.RunRoot 'phase'
    $names=@('compiled/iw7/sdk_spawn_tip.gscbin','compile.command.json','compile.stdout.log','compile.stderr.log',
        'audit.stdout.json','audit.stderr.log','disassembly.gscasm','references.bound.json')
    if(@($Report.Artifacts).Count -ne $names.Count){throw 'Child artifact inventory differs.'}
    foreach($name in $names){
        $rows=@($Report.Artifacts|Where-Object Path -CEQ (Join-Path $phase $name))
        if($rows.Count -ne 1 -or $rows[0].Bytes -gt 4MB){throw 'Missing/big child artifact.'}
        $Context.Guards.Add((Open-H1Pin $rows[0]))
    }
    $binary=@($Report.Artifacts|Where-Object Path -CEQ (Join-Path $phase $names[0]))[0]
    if($binary.SHA256 -cne $Report.InputSHA256 -or $binary.Bytes -gt $Plan.BinaryLimitBytes){throw 'Compiled proof input differs.'}
    $allowed=@($names|ForEach-Object {Join-Path $phase $_})+@(Join-Path $phase 'child.json')+@(Join-Path $phase 'stdout.log')+@(Join-Path $phase 'stderr.log')+@(Join-Path $Plan.RunRoot 'stop.request')
    $null=Measure-H1Output $Plan.RunRoot
    foreach($file in [IO.Directory]::EnumerateFiles($Plan.RunRoot,'*',[IO.SearchOption]::AllDirectories)){
        if($file -cnotin $allowed){throw 'Unexpected compiler/phase output.'}
    }
}

function Initialize-SpawnTipOwner([string]$Path) { $null=[Reflection.Assembly]::LoadFrom($Path) }
function Invoke-SpawnTipRun($Plan,[string]$PlanSHA256,$Guards) {
    $context=[pscustomobject]@{Owner=$null;Closed=$true;Lease=$null;Guards=$Guards}
    [AppDomain]::CurrentDomain.SetData('IW7.SpawnTip.Active',$context)
    $state=[ordered]@{Schema='iw7.spawn-tip-run/1';Status='Pending';Stage='GscAudit';PlanSHA256=$PlanSHA256;
        RunId=[guid]::NewGuid().ToString('N');DeadlineSeconds=180;PhysicalBytes=4GB;CommitBytes=6GB;EstimatesAreMeasured=$false;
        MaxObservedOutputBytes=0L;TreeClosureConfirmed=$true;LeaseReleased=$false;LeaseToken=$null;Quarantined=$false;
        TerminationRequested=$false;EncodedReferenceAbsence=$false;RuntimeValidated=$false;PackageReady=$false;OwnerAccepted=$false}
    $created=$false;$failure=$null;$started=$null
    try {
        $context.Lease=Enter-IW7ResourceLease -Scope $Plan.RunRoot -Kind Build -PhysicalBytes 4GB -CommitBytes 6GB -Owner 'Spawn-tip offline compiler and V8 audit'
        $state.LeaseToken=$context.Lease.Token;$started=Get-H1Clock
        if(Test-Path -LiteralPath $Plan.RunRoot){throw 'Run output appeared during admission.'}
        [IO.Directory]::CreateDirectory((Join-Path $Plan.RunRoot 'phase'))|Out-Null;$created=$true
        foreach($pin in $Plan.Bindings|Where-Object {!$_.IsText}){$Guards.Add((Open-H1Pin $pin));Assert-H1Deadline $started 180}
        Initialize-SpawnTipOwner $script:SpawnTipPins.JobAssembly.Path
        $start=[Diagnostics.ProcessStartInfo]::new($script:SpawnTipPins.Python.Path)
        $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.WindowStyle='Hidden';$start.WorkingDirectory=Join-Path $Plan.RunRoot 'phase'
        foreach($name in 'PYTHONPATH','PYTHONHOME'){[void]$start.Environment.Remove($name)}
        foreach($arg in @('-I','-B',$script:SpawnTipPins.Phase.Path,'child','--plan',$script:SpawnTipPlanPath,'--plan-sha256',$PlanSHA256,
            '--lease-token',$state.LeaseToken,'--run-id',$state.RunId)){$start.ArgumentList.Add($arg)}
        if(Test-Path -LiteralPath (Join-Path $Plan.RunRoot 'stop.request')){throw 'Coordinator stop requested before launch.'}
        Invoke-H1OwnedStage $Plan $state $context $start $script:SpawnTipPins.Python.SHA256 $start.WorkingDirectory $started
        $childPath=Join-Path $start.WorkingDirectory 'child.json'
        $item=Get-Item -LiteralPath $childPath
        if($item.Length -gt 1MB){throw 'Child receipt too large.'}
        $childGuard=[IO.FileStream]::new($childPath,'Open','Read','Read');$Guards.Add($childGuard)
        $report=Read-H1SmallJson $childPath 1MB
        Assert-SpawnTipChild $report $Plan $PlanSHA256 $state $context
        foreach($pin in $Plan.Bindings){$guard=Open-H1Pin $pin;try{}finally{$guard.Dispose()};Assert-H1Deadline $started 180}
        Test-H1Budget $Plan $state;Assert-H1Deadline $started 180
        $state.Child=$report;$state.EncodedReferenceAbsence=$true;$state.Status='OfflineReferencesQualified'
    }catch{$failure=$_;$state.Status='Failed';$state.Error=$_.Exception.Message}
    finally {
        Complete-H1Stage $context $state
        if(!$state.LeaseReleased -and $state.LeaseToken -and !$failure){$failure='Lease not released';$state.Status='Quarantined'}
        if($created){
            $state.FinishedUtc=[datetime]::UtcNow.ToString('o')
            try{if($null -ne $started -and !$state.Quarantined){Assert-H1Deadline $started 180};Write-H1Receipt $Plan $state $Plan.RunRoot}
            catch{$state.Status='Failed';$state.ReceiptError=$_.Exception.Message;$failure=$_}
        }
        if($context.Closed -and !$context.Lease){
            foreach($guard in $Guards){$guard.Dispose()};$Guards.Clear()
            [AppDomain]::CurrentDomain.SetData('IW7.SpawnTip.Active',$null)
        }
    }
    return [pscustomobject]@{State=$state;Context=$context;Failure=$failure}
}
