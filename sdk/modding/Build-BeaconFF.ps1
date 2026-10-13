param(
    [Parameter(Mandatory)][string]$SourceRoot,
    [Parameter(Mandatory)][string]$SourceReceiptSHA256,
    [Parameter(Mandatory)][string]$StockRoot,
    [Parameter(Mandatory)][string]$StockReceipt,
    [Parameter(Mandatory)][string]$StockReceiptSHA256,
    [string]$StockBindingReceipt,
    [string]$StockBindingReceiptSHA256,
    [string]$ReviewedStockManifest,
    [string]$ReviewedStockManifestSHA256,
    [Parameter(Mandatory)][string]$CandidateRoot,
    [string]$CandidateArtifactSHA256,
    [Parameter(Mandatory)][string]$ReaderRoot,
    [Parameter(Mandatory)][string]$RunRoot,
    [Parameter(Mandatory)][string]$OpsRoot,
    [Parameter(Mandatory)][string]$JobSource,
    [string]$JobSourceSHA256,
    [switch]$Run
)
# Default is a read-only plan: no native import, lease, staging or process.
$ErrorActionPreference='Stop'
. "$OpsRoot/Base-Client.Core.ps1"
. "$PSScriptRoot/BeaconFF.Core.ps1"
$sdkRepo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$RunRoot=Resolve-IW7BasePath (Join-Path $sdkRepo 'runtime') ([IO.Path]::GetRelativePath((Join-Path $sdkRepo 'runtime'),[IO.Path]::GetFullPath($RunRoot)))
if(Test-Path -LiteralPath $RunRoot){throw 'Fresh beacon build directory required.'}
$SourceRoot=(Resolve-Path -LiteralPath $SourceRoot).Path
$StockRoot=(Resolve-Path -LiteralPath $StockRoot).Path
$CandidateRoot=[IO.Path]::GetFullPath($CandidateRoot)
$ReaderRoot=(Resolve-Path -LiteralPath $ReaderRoot).Path
$receiptPath=Resolve-IW7BasePath $SourceRoot 'source-receipt.local.json'
Assert-BeaconHash $receiptPath $SourceReceiptSHA256
$measuredSourceReceiptSHA256=(Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
if($measuredSourceReceiptSHA256 -ine $SourceReceiptSHA256){throw 'Source receipt changed during measurement.'}
$receipt=Read-BeaconJson $receiptPath
if($receipt.schema -cne 'iw7.beacon-source-receipt/1' -or $receipt.zone -cne 'sdk_beacon' -or $receipt.ff_built -or $receipt.output -ine $SourceRoot){throw 'Original unbuilt beacon receipt required.'}
$names=@('xmodel/paris_model_probe.xmb','xsurface/paris_model_probe_lod0.xsb','zone_source/sdk_beacon.csv','zone_source/paris_model_probe_recipient.csv','netconststrings/ncs_mdl_paris_model_probe.json')
foreach($entry in $receipt.files){$p=Resolve-IW7BasePath $SourceRoot $entry.path;if((Get-Item -LiteralPath $p).Length -ne $entry.bytes){throw 'Beacon input size changed.'};Assert-BeaconHash $p $entry.sha256}
if(@($receipt.files).Count -ne 10 -or @($names|Where-Object {$_ -cnotin $receipt.files.path}).Count){throw 'Exact prepared beacon inputs required.'}
Assert-BeaconHash $StockReceipt $StockReceiptSHA256
$stockState=Read-BeaconJson $StockReceipt
if($stockState.Schema -cne 'iw7.model-ff-build/1' -or !$stockState.Restored -or !$stockState.StockPreserved -or $stockState.RetainedLeaseToken){throw 'Completed retained stock transaction required.'}
$stockPins=@($StockBindingReceipt,$StockBindingReceiptSHA256,$ReviewedStockManifest,$ReviewedStockManifestSHA256)
if(@($stockPins|Where-Object {$_}).Count -notin @(0,4)){throw 'Supply all four stock observation/manifest arguments together.'}
$stockCore=$null;$stockCoreSHA256=$null
$inputs=@();$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
if($StockBindingReceipt){
    # Reuse the reviewed pure contract. Plan reads only these bounded receipts,
    # never identities or large retail content; those checks require admission.
    $stockCore=Resolve-IW7BasePath (Split-Path $OpsRoot -Parent) 'tools-source/asset-bridge/common/StockBinding.Core.ps1'
    $stockCoreSHA256=(Get-FileHash -LiteralPath $stockCore -Algorithm SHA256).Hash
    . $stockCore
    Assert-BeaconHash $StockBindingReceipt $StockBindingReceiptSHA256
    Assert-BeaconHash $ReviewedStockManifest $ReviewedStockManifestSHA256
    $observation=Read-BeaconJson $StockBindingReceipt
    $reviewed=Read-BeaconJson $ReviewedStockManifest
    $inputs=@(Get-FFStockBindingInputs $stockState $observation $reviewed $StockRoot $StockReceiptSHA256 $ReviewedStockManifestSHA256)
    foreach($entry in $inputs){
        $null=$seen.Add($entry.Relative)
        $entry|Add-Member NoteProperty BaselineMode $entry.Mode
        $entry.Mode=if($entry.Relative -ceq 'main/fileSysCheck.cfg'){'Copy'}else{'HardLink'}
    }
}else{
foreach($entry in $stockState.Inputs){
    $source=Resolve-IW7BasePath $StockRoot $entry.Relative
    if($source -ine $entry.Source -or !$seen.Add($entry.Relative)){throw 'Stock source scope/duplicate differs.'}
    $file=Get-Item -LiteralPath $source
    if($file.Length -ne $entry.Bytes -or $file.Attributes.HasFlag([IO.FileAttributes]::ReadOnly)){throw 'Retained stock size/read-only link gate failed.'}
    # All immutable stock is linked; only the mutable 77-byte sentinel is copied.
    $inputs+=[pscustomobject]@{Relative=$entry.Relative;Source=$source;Mode=$(if($entry.Relative -ceq 'main/fileSysCheck.cfg'){'Copy'}else{'HardLink'});
        Bytes=$file.Length;ModifiedUtc=$file.LastWriteTimeUtc.ToString('o');Attributes=[int]$file.Attributes}
}
}
if(!$seen.Contains('main/code_pre_gfx.ff') -or !$seen.Contains('zone/assetfile1.pak') -or !$seen.Contains('iw7_ship.exe') -or $inputs.Count -gt 96){throw 'Exact bounded bootstrap stock required.'}
$readerProvenance=Resolve-IW7BasePath $ReaderRoot 'writer-provenance.json'
$reader=Resolve-IW7BasePath $ReaderRoot 'model-writer.exe'
$rp=Read-BeaconJson $readerProvenance
if($rp.WriterSHA256 -cne 'B77B422EE5441E45243122974D9B3BFC117F9CB60F153D4FEC4F3ABBAC1D0926' -or $rp.Roundtrip.lod0_dist -ne 1000000 -or !$rp.Roundtrip.read_existing_supported){throw 'Exact original LOD1M reader required.'}
Assert-BeaconHash $reader $rp.WriterSHA256
$candidate=$null
$preparationContract=$null
$preparationPath=Join-Path $CandidateRoot 'preparation.local.json'
if(Test-Path -LiteralPath $preparationPath){
    $preparation=Read-BeaconJson $preparationPath;Assert-BeaconPreparation $preparation
    $preparationContract=[ordered]@{Status='SourcePreparationContractVerified';PreparationSHA256=(Get-FileHash -LiteralPath $preparationPath).Hash;
        PatchCount=3;PatchedCPPs=5;CompileUnits=413;DependencyLibraries=18;MapRuntimeValidated=$false;BuildValidated=$false}
}
if($CandidateArtifactSHA256){$candidate=Assert-BeaconCandidate $CandidateRoot $CandidateArtifactSHA256}
$work=Join-Path $RunRoot 'work'
$plan=[ordered]@{Schema='iw7.beacon-ff-plan/1';Work=$work;SourceRoot=$SourceRoot;SourceFiles=$names;StockInputs=$inputs;
    SourceReceiptSHA256=$measuredSourceReceiptSHA256;
    StockBindingReceipt=$StockBindingReceipt;StockBindingReceiptSHA256=$StockBindingReceiptSHA256;
    ReviewedStockManifest=$ReviewedStockManifest;ReviewedStockManifestSHA256=$ReviewedStockManifestSHA256;
    StockBindingCoreSHA256=$stockCoreSHA256;StockContentAndIdentityRecheckPending=[bool]$StockBindingReceipt;
    StagingCopyBytes=[long](($inputs|Where-Object Mode -CEQ Copy|Measure-Object Bytes -Sum).Sum);
    CandidatePending=($null -eq $candidate);Candidate=$candidate;CandidatePreparation=$preparationContract;Reader=$reader;JobSource=$JobSource;JobSourceSHA256=$JobSourceSHA256;
    Phases=@('buildzone sdk_beacon','verifyzone sdk_beacon','dumpzone sdk_beacon','reader --verify-existing roundtrip');
    PhysicalBytes=8GB;CommitBytes=11GB;TimeoutSeconds=240;ReaderTimeoutSeconds=30;LogBytesPerStream=2MB;NewOutputStopBytes=64MB;
    CopyStock=$false;CopyPreparedSources=$false;SentinelCopyOnly=$true;PAKs=@('zone/assetfile1.pak');CPPreload=$false;Ready=$false}
$plan.PhaseAdapterSHA256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'beacon_tool_phase.py')).Hash
if(!$Run){$plan|ConvertTo-Json -Depth 8;return}
if(!$candidate -or !$JobSourceSHA256){throw 'Explicit final candidate receipt and shared final job source pin required.'}
Assert-BeaconHash $JobSource $JobSourceSHA256
if('IW7.CommunityBuild.BuildJob' -as [type]){throw 'Use a fresh PowerShell host for source-bound shared job.'}
. "$OpsRoot/Resource-Scheduler.Core.ps1"
. "$OpsRoot/model-lab/ModelFF.Core.ps1"
$guards=[Collections.Generic.List[IDisposable]]::new();$lease=$null;$owner=$null;$closed=$true;$saved=$false
$state=[ordered]@{Schema='iw7.beacon-ff-build/1';Work=$work;Inputs=$inputs;Plan=$plan;Status='Preparing';Phases=@();Restored=$false;
    StockPreserved=$false;RestorationStatus='Pending';CleanupError=$null;RetainedLeaseToken=$null;FF=$null;MaxObservedBytes=0L;FinalObservedBytes=$null;
    InventoryVerified=$false;GeometryRoundtripVerified=$false;RecipientReferenceResolved=$false;Ready=$false}
$statePath=Join-Path $RunRoot 'state.local.json'
function Save-BeaconState {$state|ConvertTo-Json -Depth 14|Set-Content -LiteralPath $statePath -Encoding utf8}
function Measure-BeaconOutput([switch]$Final) {
    $exempt=@($state.Inputs|Where-Object {$_.Mode -ceq 'HardLink' -and $_.TargetId -and $_.TargetId -ceq $_.SourceId}|ForEach-Object Relative)
    $bytes=Measure-BeaconOutputFiles @(Get-ChildItem -LiteralPath $RunRoot -File -Recurse -Force) $work $exempt
    $state.MaxObservedBytes=[math]::Max($state.MaxObservedBytes,$bytes)
    if($Final){$state.FinalObservedBytes=$bytes}
    Assert-BeaconOutputBudget $bytes
}
function Invoke-BeaconPhase([string]$Phase,[string]$Exe,[string]$Hash) {
    $logs=Join-Path $RunRoot $Phase
    $python=(Get-Command python -ErrorAction Stop).Source
    $arguments=@((Join-Path $PSScriptRoot 'beacon_tool_phase.py'),'--phase',$Phase,'--exe',$Exe,'--sha256',$Hash,'--work',$work,'--logs',$logs,'--roundtrip',(Join-Path $RunRoot 'roundtrip'))
    $quoted=@(foreach($arg in $arguments){if(!$arg -or $arg -match '["\x00-\x1f]' -or $arg.EndsWith('\')){throw 'Unsupported phase path.'};'"'+$arg+'"'})
    $script:owner=[IW7.CommunityBuild.BuildJob]::Prepare($python,($quoted -join ' '),$work);$script:closed=$false
    $identity=Get-BeaconJobIdentity $owner $python $Phase
    $state.Phases+=,$identity;Save-BeaconState
    $owner.Resume();$start=[datetime]::UtcNow;$attached=$false
    while(!$owner.Exited -and !$attached){
        try{Add-IW7ResourceProcess -Token $lease.Token -ProcessId $owner.PID;$attached=$true}
        catch{if($_.Exception.Message -notlike 'Child identity unavailable*' -or [datetime]::UtcNow -gt $start.AddSeconds(5)){throw};Start-Sleep -Milliseconds 100}
    }
    $seconds=if($Phase -ceq 'read'){35}else{245}
    while(!$owner.Exited -or $owner.Active -ne 0){
        if($owner.Exited -and $owner.Active -ne 0){throw 'Phase parent exited with descendants; stop original job.'}
        if([datetime]::UtcNow -gt $start.AddSeconds($seconds)){throw 'Beacon phase timeout; stop original job.'}
        if(Test-Path -LiteralPath (Join-Path $RunRoot 'stop.request')){throw 'Coordinator requested owned stop.'}
        Measure-BeaconOutput
        $memory=Get-IW7ResourceSnapshot;if($memory.Committed -gt $memory.CommitLimit*0.85){throw 'Commit pressure exceeded85 percent.'}
        Start-Sleep -Milliseconds 100
    }
    $identity.ExitCode=$owner.ExitCode;$identity.JobActiveAtClose=$owner.Active
    $script:closed=$true;$owner.Dispose();$script:owner=$null;Save-BeaconState
    # A short phase may have ended between polls; include its logs and receipt.
    Measure-BeaconOutput;Save-BeaconState;Measure-BeaconOutput
    $phaseResult=Read-BeaconJson (Join-Path $logs 'phase.json')
    if($identity.ExitCode -ne 0 -or $phaseResult.exit_code -ne 0 -or $phaseResult.failure){throw 'Native phase failed; bounded logs retained.'}
    return [IO.File]::ReadAllText((Join-Path $logs 'stdout.log'))
}
try {
    $lease=Enter-IW7ResourceLease -Scope $work -Kind Extract -PhysicalBytes 8GB -CommitBytes 11GB -Owner 'Beacon FF build inventory dump reader'
    $state.RetainedLeaseToken=$lease.Token
    $receiptPins=@{};$receiptPins[$receiptPath]=$measuredSourceReceiptSHA256;$receiptPins[$StockReceipt]=$StockReceiptSHA256
    if($StockBindingReceipt){
        $receiptPins[$StockBindingReceipt]=$StockBindingReceiptSHA256;$receiptPins[$ReviewedStockManifest]=$ReviewedStockManifestSHA256
        $receiptPins[$stockCore]=$stockCoreSHA256
    }
    foreach($path in $receiptPins.Keys){$guards.Add([IO.File]::Open($path,'Open','Read','Read'));Assert-BeaconHash $path $receiptPins[$path]}
    $guards.Add([IO.File]::Open($JobSource,'Open','Read','Read'));Assert-BeaconHash $JobSource $JobSourceSHA256
    $adapter=Join-Path $PSScriptRoot 'beacon_tool_phase.py';$guards.Add([IO.File]::Open($adapter,'Open','Read','Read'));Assert-BeaconHash $adapter $plan.PhaseAdapterSHA256
    Add-Type -LiteralPath $JobSource
    Add-Type -LiteralPath "$OpsRoot/hud-lab/HudFileIdentity.cs"
    foreach($name in $names){$p=Resolve-IW7BasePath $SourceRoot $name;$f=Get-Item -LiteralPath $p;$state.Inputs+=,[pscustomobject]@{Relative=$name;Source=$p;Mode='HardLink';Bytes=$f.Length;ModifiedUtc=$f.LastWriteTimeUtc.ToString('o');Attributes=[int]$f.Attributes}}
    $f=Get-Item -LiteralPath $candidate.Path
    $state.Inputs+=,[pscustomobject]@{Relative='zonetool.exe';Source=$candidate.Path;Mode='HardLink';Bytes=$f.Length;ModifiedUtc=$f.LastWriteTimeUtc.ToString('o');Attributes=[int]$f.Attributes}
    foreach($entry in $state.Inputs){
        $null=Resolve-IW7BasePath (Split-Path $entry.Source -Parent) (Split-Path $entry.Source -Leaf)
        $guards.Add([IO.File]::Open($entry.Source,'Open','Read','Read'))
        $sourceId=[IW7HudFileIdentity]::Read($entry.Source)
        if($StockBindingReceipt){Assert-FFStockIdentity $entry $sourceId}
        $entry|Add-Member NoteProperty SourceId $sourceId
    }
    if($StockBindingReceipt){Assert-FFStockContent $state.Inputs}
    Assert-ModelFFInputs $state.Inputs $work -SourceOnly
    $guards.Add([IO.File]::Open($reader,'Open','Read','Read'))
    Assert-BeaconHash $candidate.Path $candidate.SHA256;Assert-BeaconHash $reader $rp.WriterSHA256
    foreach($name in $names){$entry=@($receipt.files|Where-Object path -CEQ $name)[0];Assert-BeaconHash (Join-Path $SourceRoot $name) $entry.sha256}
    if(Test-Path -LiteralPath $RunRoot){throw 'Beacon run directory appeared during admission; preserve it.'}
    New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop|Out-Null
    [IO.Directory]::CreateDirectory($work)|Out-Null
    $state.Transaction=Save-IW7BaseTransaction ([pscustomobject]@{GameRoot=$work;MutableFiles=@($state.Inputs.Relative)+@('zone/sdk_beacon.ff');ProfileDirectory='unused';ProfileDirectories=@()}) (Join-Path $RunRoot 'backup');$saved=$true;Save-BeaconState
    foreach($entry in $state.Inputs){
        $target=Resolve-IW7BasePath $work $entry.Relative;[IO.Directory]::CreateDirectory((Split-Path $target))|Out-Null
        if($entry.Mode -ceq 'Copy'){Copy-Item -LiteralPath $entry.Source -Destination $target}else{New-Item -ItemType HardLink -Path $target -Target $entry.Source|Out-Null}
        $entry|Add-Member NoteProperty TargetId ([IW7HudFileIdentity]::Read($target))
        if($entry.Mode -ceq 'HardLink' -and $entry.TargetId -cne $entry.SourceId){throw 'Staged NTFS identity differs.'}
        if($entry.Mode -ceq 'Copy'){
            if($entry.TargetId -ceq $entry.SourceId){throw 'Sentinel copy aliases stock; do not alter its attributes.'}
            $copy=Get-Item -LiteralPath $target
            if($copy.IsReadOnly){$copy.IsReadOnly=$false}
        }
    }
    Assert-ModelFFInputs $state.Inputs $work
    $state.Status='Building';Save-BeaconState
    $null=Invoke-BeaconPhase build (Join-Path $work 'zonetool.exe') $candidate.SHA256
    $ff=Resolve-IW7BasePath $work 'zone/sdk_beacon.ff';$size=(Get-Item -LiteralPath $ff).Length
    if($size -lt 1 -or $size -gt 1MB){throw 'Beacon FF must be nonempty and at most1MiB.'}
    Copy-Item -LiteralPath $ff -Destination (Join-Path $RunRoot 'mod.ff')
    $state.FF=@{Bytes=$size;SHA256=(Get-FileHash -LiteralPath $ff).Hash;Path='mod.ff'};Save-BeaconState
    $rows=@(Get-BeaconInventory (Invoke-BeaconPhase verify (Join-Path $work 'zonetool.exe') $candidate.SHA256))
    $rows|Set-Content -LiteralPath (Join-Path $RunRoot 'assets.csv');$state.InventoryVerified=$true;Save-BeaconState
    $null=Invoke-BeaconPhase dump (Join-Path $work 'zonetool.exe') $candidate.SHA256
    foreach($name in $names[0..1]){
        $p=Resolve-IW7BasePath (Join-Path $work 'dump/sdk_beacon') $name
        if((Get-Item -LiteralPath $p).Length -gt 8192){throw 'Original model re-dump exceeded bound.'}
        $target=Join-Path $RunRoot ('roundtrip/'+$name);[IO.Directory]::CreateDirectory((Split-Path $target))|Out-Null;Copy-Item -LiteralPath $p -Destination $target
    }
    $geometry=(Invoke-BeaconPhase read $reader $rp.WriterSHA256)|ConvertFrom-Json
    Assert-ModelFFDistanceCandidate $geometry
    if(!$geometry.geometry_roundtrip_verified -or $geometry.ready -or $geometry.vertices -ne 24 -or $geometry.triangles -ne 12 -or $geometry.bones -ne 1 -or $geometry.material_reference -cne 'mopw/character_park_clown_zombie_shoes'){throw 'Original model semantic reader differs.'}
    $state.Geometry=$geometry;$state.GeometryRoundtripVerified=$true
    Save-BeaconState;Measure-BeaconOutput -Final;Save-BeaconState;Measure-BeaconOutput -Final
    $state.Status='BootstrapInventoryAndGeometryVerified'
} catch {$state.Failure=$_.Exception.Message;$state.Status='Failed';throw}
finally {
    if($owner){
        try{$owner.Stop();$until=[datetime]::UtcNow.AddSeconds(15);while(($owner.Active -ne 0 -or !$owner.Exited) -and [datetime]::UtcNow -lt $until){Start-Sleep -Milliseconds 100};$closed=($owner.Active -eq 0 -and $owner.Exited)}catch{$closed=$false}
        $owner.Dispose()
    }
    if($closed){foreach($guard in $guards){$guard.Dispose()}}
    if($saved){
        Save-BeaconState
        if($closed){
            Complete-ModelFFRestore $state $statePath $lease.Token
            try{Measure-BeaconOutput -Final;Save-BeaconState;Measure-BeaconOutput -Final}
            catch{$state.Status='Failed';$state.Failure=$_.Exception.Message;Save-BeaconState;throw}
        }
        else{$state.CleanupError='Owned tree closure unconfirmed; preserve inputs and reservation.';Save-BeaconState}
    }elseif($lease -and $closed){Exit-IW7ResourceLease -Token $lease.Token}
}
