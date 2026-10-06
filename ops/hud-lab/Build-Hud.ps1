param(
    [ValidateSet('Prepare','Build','Restore')][string]$Action='Prepare',
    [string]$StockToolRoot,
    [string]$RunRoot,
    [string]$ToolProvenance,
    [ValidateSet('Spaceland','Bootstrap')][string]$VerificationContext='Spaceland'
)
$ErrorActionPreference='Stop'
$ops=Split-Path $PSScriptRoot -Parent
$repo=Split-Path $ops -Parent
. "$ops/Base-Client.Core.ps1"
. "$ops/Lab-Paths.ps1"
. "$ops/Resource-Scheduler.Core.ps1"
. "$ops/Memory-Budget.ps1"
if (!('IW7HudFileIdentity' -as [type])) { Add-Type -Path "$PSScriptRoot/HudFileIdentity.cs" }

function Assert-HudInputsUnchanged($Inputs,[string]$Work,[switch]$SourceOnly) {
    foreach ($entry in $Inputs) {
        $null=Resolve-IW7BasePath (Split-Path $entry.Source -Parent) (Split-Path $entry.Source -Leaf)
        $source=Get-Item -LiteralPath $entry.Source
        $expectedUtc=([datetimeoffset]$entry.ModifiedUtc).UtcDateTime
        if ($source.Length -ne $entry.Bytes -or $source.LastWriteTimeUtc.Ticks -ne $expectedUtc.Ticks -or
            [int]$source.Attributes -ne $entry.SourceAttributes -or
            [IW7HudFileIdentity]::Read($entry.Source) -ne $entry.SourceId) {
            throw 'Stock input identity/size/time changed; preserve links and evidence for hash diagnosis.'
        }
        if (!$SourceOnly) {
            $target=Get-Item -LiteralPath (Resolve-IW7BasePath $Work $entry.Relative)
            if ($target.Length -ne $entry.Bytes -or $target.LastWriteTimeUtc.Ticks -ne $expectedUtc.Ticks -or
                [IW7HudFileIdentity]::Read($target.FullName) -ne $entry.TargetId) { throw 'Prepared input identity/size/time changed; preserve links and evidence.' }
        }
    }
}

function Assert-HudWorkVacant([string]$Work) {
    foreach ($p in @(Get-CimInstance Win32_Process | Where-Object Name -Match '^(?:iw7.*|zonetool.*)\.exe$')) {
        if (!$p.ExecutablePath -or $p.ExecutablePath.StartsWith($Work+'\',[StringComparison]::OrdinalIgnoreCase)) {
            throw 'Asset process identity unknown or HUD work occupied; preserve transaction.'
        }
    }
}
function Write-HudJson($Object,[string]$Path) {
    $Object | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $Path -Encoding utf8
}
function Complete-HudRestore($State,[string]$StatePath,[string]$LeaseToken) {
    $State | Add-Member NoteProperty RetainedLeaseToken $LeaseToken -Force
    try {
        Assert-HudWorkVacant $State.Work
        Assert-HudInputsUnchanged $State.Inputs $State.Work
        Restore-IW7BaseTransaction $State.Transaction
        Assert-HudInputsUnchanged $State.Inputs $State.Work -SourceOnly
        $State.Restored=$true
        $State | Add-Member NoteProperty StockPreserved $true -Force
        $State | Add-Member NoteProperty RestorationStatus 'Confirmed' -Force
        Write-HudJson $State $StatePath
    } catch {
        $State | Add-Member NoteProperty RestorationStatus 'Refused' -Force
        $State | Add-Member NoteProperty RestorationFailure $_.Exception.Message -Force
        Write-HudJson $State $StatePath
        throw
    }
    # Never release from finally: all ownership/input/restore guards must pass.
    Exit-IW7ResourceLease -Token $LeaseToken
    $State.RetainedLeaseToken=$null
    Write-HudJson $State $StatePath
}
function Get-HudVerifiedInventory([string]$Log,[switch]$BootstrapOnly) {
    $expectedZone=if($BootstrapOnly){'paris_lab_hud'}else{'cp_zmb'}
    if (!$Log.Contains('Loading zone "'+$expectedZone+'"') -or $Log -match 'could not be found|\[ ERROR \]|\[ FATAL \]') { throw 'Offline log lacks required context load or reports errors.' }
    $lines=@($Log -split '\r?\n' | Where-Object {$_ -match 'Loading asset '})
    $rows=@(foreach($line in $lines) {
        if ($line -notmatch 'Loading asset "([^"\r\n]+)" of type ([a-z0-9]+)\.$') { throw 'Malformed verify asset record.' }
        $Matches[2]+','+$Matches[1]
    })
    if ($rows.Count -ne 2 -or 'luafile,ui_scripts/paris_lab_hud/__init__.lua' -notin $rows -or 'rawfile,paris_lab_hud' -notin $rows) { throw 'Unexpected verified FF inventory; not the minimal HUD package.' }
    $rows
}
if ($Action -eq 'Prepare') {
    if (!$StockToolRoot) { throw 'Existing complete stock tool workspace required.' }
    $stock=(Resolve-Path -LiteralPath $StockToolRoot).Path.TrimEnd('\','/')
    $null=Assert-IW7LabPath $stock $stock
    if (!$RunRoot) { $RunRoot=Join-Path $repo ('runtime/hud-build-'+[datetime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N')) }
    $RunRoot=Assert-IW7LabPath $RunRoot (Join-Path $repo 'runtime')
    if (Test-Path -LiteralPath $RunRoot) { throw 'Fresh HUD run required; no existing directory is overwritten.' }
    # Explicit bootstrap/recipient allowlist; no SAB, stock clone or generated FF.
    $zones=@('code_pre_gfx','code_post_gfx','common','common_mp','common_cp','common_core_mp',
        'global','global_mp','global_cp','global_core_mp','cp_zmb')
    $names=@($zones | ForEach-Object { "$_.ff";"patch_$_.ff";"techsets_$_.ff" })
    $inputs=@()
    foreach ($folder in @('main','zone')) {
        foreach ($file in @(Get-ChildItem -LiteralPath (Resolve-IW7BasePath $stock $folder) -File -Filter '*.ff')) {
            if ($file.Name -in $names) {
                if ($file.Attributes -band [IO.FileAttributes]::ReadOnly) { throw 'Read-only shared stock cannot be safely unlinked with this transaction; choose an existing Archive-only tool input.' }
                $relative=$folder+'/'+$file.Name
                $null=Resolve-IW7BasePath $stock $relative
                $inputs+=[pscustomobject]@{Relative=$relative;Source=$file.FullName;Bytes=$file.Length;ModifiedUtc=$file.LastWriteTimeUtc.ToString('o');Mode='HardLink'}
            }
        }
    }
    # Only the PAK named by the exact-owned bootstrap failure, corroborated by
    # the retained Doom diagnostic. Do not enumerate/link the entire PAK stock.
    $bootstrap=Get-Content -LiteralPath "$PSScriptRoot/bootstrap-dependencies.json" -Raw | ConvertFrom-Json
    if($bootstrap.schema -cne 'iw7.hud-bootstrap/1' -or $bootstrap.tool_source -cne 'fab935826c898806855376662a8a03317b3ad8f1'){throw 'Unreviewed bootstrap dependency manifest.'}
    $seenPaks=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($dependency in @($bootstrap.dependencies | Where-Object {$VerificationContext -eq 'Spaceland' -or $_.phase -eq 'bootstrap'})) {
    if($dependency.relative -cnotmatch '^zone/assetfile[1-9][0-9]*\.pak$' -or !$seenPaks.Add($dependency.relative)){throw 'Unsafe or duplicate bootstrap PAK dependency.'}
    $pak=Resolve-IW7BasePath $stock $dependency.relative
    if (!(Test-Path -LiteralPath $pak -PathType Leaf)) { throw ('Missing observed bootstrap prerequisite '+$dependency.relative) }
    $file=Get-Item -LiteralPath $pak
    if ($file.Attributes -band [IO.FileAttributes]::ReadOnly) { throw 'Read-only shared PAK cannot be safely unlinked with this transaction.' }
    $inputs+=[pscustomobject]@{Relative=$dependency.relative;Source=$pak;Bytes=$file.Length;ModifiedUtc=$file.LastWriteTimeUtc.ToString('o');Mode='HardLink'}
    }
    foreach ($name in @('iw7_ship.exe','amd_ags_x64.dll','bink2w64.dll','d3dcompiler_46.dll','steam_api.dll','steam_api64.dll','Steam.dll','tlsdll.dll')) {
        $path=Resolve-IW7BasePath $stock $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $file=Get-Item -LiteralPath $path
            $inputs+=[pscustomobject]@{Relative=$name;Source=$path;Bytes=$file.Length;ModifiedUtc=$file.LastWriteTimeUtc.ToString('o');Mode='Copy'}
        } elseif ($name -in @('iw7_ship.exe','bink2w64.dll','steam_api64.dll')) { throw "Missing engine prerequisite $name" }
    }
    # Retail filesystem bootstrap uses this sentinel before tool commands run.
    # Copy it, like the existing Doom recipe; never share mutable cache files.
    $sentinel=Resolve-IW7BasePath $stock 'main/fileSysCheck.cfg'
    if (!(Test-Path -LiteralPath $sentinel -PathType Leaf)) { throw 'Missing filesystem bootstrap sentinel main/fileSysCheck.cfg' }
    $file=Get-Item -LiteralPath $sentinel
    $inputs+=[pscustomobject]@{Relative='main/fileSysCheck.cfg';Source=$sentinel;Bytes=$file.Length;ModifiedUtc=$file.LastWriteTimeUtc.ToString('o');Mode='Copy'}
    if (!@($inputs | Where-Object Relative -eq 'main/code_pre_gfx.ff').Count -or !@($inputs | Where-Object Relative -eq 'main/cp_zmb.ff').Count) { throw 'Bootstrap and Spaceland recipient FF prerequisites missing.' }
    $work=Join-Path $RunRoot 'work'
    [IO.Directory]::CreateDirectory($work) | Out-Null
    $mutable=@($inputs.Relative)+@('zonetool.exe','zone_source/paris_lab_hud.csv',
        'zonetool/paris_lab_hud/ui_scripts/paris_lab_hud/__init__.lua','zone/paris_lab_hud.ff','paris_lab_hud.assets.csv')
    $plan=[pscustomobject]@{GameRoot=$work;MutableFiles=$mutable;ProfileDirectory='hud-unused-profile';ProfileDirectories=@()}
    $transaction=Save-IW7BaseTransaction -Plan $plan -BackupRoot (Join-Path $RunRoot 'backup')
    $state=[ordered]@{Schema='iw7.hud-build/1';RunRoot=$RunRoot;Work=$work;StockToolRoot=$stock;Inputs=$inputs;
        Status='Preparing';VerificationContext=$VerificationContext;RecipientOfflineLinked=$false;StockCopied=$false;EnginePrerequisitesCopied=$true;FullGameClone=$false;OwnerAcceptance=$false;Restored=$false;Transaction=$transaction}
    $statePath=Join-Path $RunRoot 'state.local.json'
    Write-HudJson $state $statePath
    try {
        foreach ($entry in $inputs) {
            $entry | Add-Member NoteProperty SourceId ([IW7HudFileIdentity]::Read($entry.Source))
            $entry | Add-Member NoteProperty SourceAttributes ([int](Get-Item -LiteralPath $entry.Source).Attributes)
            $target=Resolve-IW7BasePath $work $entry.Relative
            [IO.Directory]::CreateDirectory((Split-Path $target)) | Out-Null
            if ($entry.Mode -eq 'HardLink') { New-Item -ItemType HardLink -Path $target -Target $entry.Source | Out-Null }
            else { Copy-Item -LiteralPath $entry.Source -Destination $target }
            $entry | Add-Member NoteProperty TargetId ([IW7HudFileIdentity]::Read($target))
            if ($entry.Mode -eq 'HardLink' -and $entry.SourceId -ne $entry.TargetId) { throw 'Stock link identity mismatch.' }
        }
        $sourceStage=Join-Path $RunRoot 'source'
        & python "$PSScriptRoot/prepare.py" --output $sourceStage > (Join-Path $RunRoot 'source-stage.json')
        if ($LASTEXITCODE) { throw 'Original HUD source staging failed.' }
        foreach ($relative in @('zone_source/paris_lab_hud.csv','zonetool/paris_lab_hud/ui_scripts/paris_lab_hud/__init__.lua')) {
            $target=Resolve-IW7BasePath $work $relative
            [IO.Directory]::CreateDirectory((Split-Path $target)) | Out-Null
            Copy-Item -LiteralPath (Join-Path $sourceStage $relative) -Destination $target
        }
        $state.Status='Prepared'
    } catch {
        $state.Status='PrepareFailed';$state.Error=$_.Exception.Message
        Assert-HudWorkVacant $work
        Restore-IW7BaseTransaction $transaction
        $state.Restored=$true
        throw
    } finally { Write-HudJson $state $statePath }
    Write-Output "HUD source and minimal hardlinked inputs prepared: $RunRoot"
    return
}
if (!$RunRoot) { throw 'Prepared RunRoot required.' }
$RunRoot=Assert-IW7LabPath ((Resolve-Path -LiteralPath $RunRoot).Path) (Join-Path $repo 'runtime')
$statePath=Join-Path $RunRoot 'state.local.json'
$state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$work=Assert-IW7LabPath $state.Work $RunRoot
if ($state.Schema -ne 'iw7.hud-build/1' -or $state.RunRoot -ne $RunRoot -or
    $work -ne (Join-Path $RunRoot 'work') -or
    $state.Transaction.GameRoot -ne $work -or $state.Transaction.BackupRoot -ne (Join-Path $RunRoot 'backup')) { throw 'HUD transaction identity mismatch.' }
Assert-HudWorkVacant $work
if ($Action -eq 'Restore') {
    if ($state.Restored -and $state.Transaction.Restored) { Write-Output 'HUD transaction is already restored.';return }
    $lease=Enter-IW7ResourceLease -Scope $work -Kind Analysis -PhysicalBytes 1MB -CommitBytes 1MB -Owner 'HUD input restoration'
    Complete-HudRestore $state $statePath $lease.Token
    $state.Status='Restored';Write-HudJson $state $statePath
    return
}
if ($state.Status -ne 'Prepared' -or !$ToolProvenance) { throw 'Prepared run and exact tool build provenance required.' }
if($state.VerificationContext -cne $VerificationContext){throw 'Prepared verification context mismatch; refuse unrecorded gate change.'}
$ToolProvenance=(Resolve-Path -LiteralPath $ToolProvenance).Path
$provenance=Get-Content -LiteralPath $ToolProvenance -Raw | ConvertFrom-Json
$pin=Get-Content -LiteralPath "$ops/enemy-ports/lab-enemy-toolchain.json" -Raw | ConvertFrom-Json
$tool=Join-Path (Split-Path $ToolProvenance -Parent) 'zonetool.exe'
if ($provenance.SourceCommit -ne $pin.SourceCommit -or $provenance.Repository -ne $pin.Repository -or
    $provenance.Status -notin @('TestsPassedReviewedBinary','TestsPassedReviewRequired') -or
    @($provenance.Tests | Where-Object {$_.Passed -ne $true}).Count -or
    @($provenance.Tests | Where-Object {$_.Name -notin @('filesystem_ownership_tests','sound_bank_subset_tests')}).Count -or
    @($provenance.Tests.Name | Select-Object -Unique).Count -ne 2 -or
    @($provenance.Tests).Count -ne 2 -or (Get-FileHash -LiteralPath $tool).Hash -ne $provenance.BinarySHA256) { throw 'Tool source/tests/hash provenance mismatch.' }
Assert-HudInputsUnchanged $state.Inputs $work
. "$ops/Lab-AssetProcess.ps1"
. "$ops/Agent-LabCrash.Core.ps1"
. "$PSScriptRoot/Hud-Process.ps1"
$package=Get-AppxPackage Microsoft.WinDbg
$cdb=Join-Path $package.InstallLocation 'amd64/cdb.exe'
if ($package.Version -ne '1.2606.22001.0' -or (Get-FileHash -LiteralPath $cdb).Hash -ne '5F54ABAFCA3AE5638BBF807D402FABB350A64575C1DFA9FBFC7F5732DF5BEE67') { throw 'Pinned offline CDB prerequisite unavailable; refuse launch without stall diagnostics.' }
$lease=Enter-IW7ResourceLease -Scope $work -Kind Extract -PhysicalBytes 8GB -CommitBytes 11GB -Owner 'Original HUD FF build, bounded bootstrap diagnostics and offline load'
$cleanup=[pscustomobject]@{Confirmed=$true}
$state | Add-Member NoteProperty RetainedLeaseToken $lease.Token -Force
try {
    Assert-HudWorkVacant $work
    Copy-Item -LiteralPath $tool -Destination (Join-Path $work 'zonetool.exe')
    $state | Add-Member NoteProperty ToolSource $provenance.SourceCommit -Force
    $state | Add-Member NoteProperty ToolSHA256 $provenance.BinarySHA256 -Force
    $state | Add-Member NoteProperty ToolAccepted ($provenance.BinarySHA256 -in $pin.AcceptedBinarySHA256) -Force
    $state.Status='Building';Write-HudJson $state $statePath
    $built=Invoke-HudBuildProcess -Work $work -RunRoot $RunRoot -LeaseToken $lease.Token -CleanupState $cleanup -Cdb $cdb -Symbols (Split-Path $ToolProvenance -Parent)
    if ($built.ExitCode) { throw 'HUD FF build failed; preserve build logs.' }
    $ff=Resolve-IW7BasePath $work 'zone/paris_lab_hud.ff'
    if (!(Test-Path -LiteralPath $ff -PathType Leaf) -or !(Get-Item -LiteralPath $ff).Length) { throw 'No nonempty FF output.' }
    # Preserve measured output before later gates; a generic HUD build emits no
    # enemy-only .assets.csv. Its actual inventory comes from verify callbacks.
    Copy-Item -LiteralPath $ff -Destination (Join-Path $RunRoot 'mod.ff')
    $state | Add-Member NoteProperty FF ([ordered]@{Path='mod.ff';Bytes=(Get-Item -LiteralPath $ff).Length;SHA256=(Get-FileHash -LiteralPath $ff).Hash;InventoryVerified=$false}) -Force
    $state | Add-Member NoteProperty Build $built -Force
    Write-HudJson $state $statePath
    $contextArguments=if($VerificationContext -eq 'Spaceland'){@('-loadzone','cp_zmb')}else{@()}
    $verified=Invoke-HudBuildProcess -Work $work -RunRoot $RunRoot -LeaseToken $lease.Token -CleanupState $cleanup -Cdb $cdb -Symbols (Split-Path $ToolProvenance -Parent) -Phase hud-offline -ToolArguments (@('-headless','-unbuffered-io')+$contextArguments+@('-verifyzone','paris_lab_hud'))
    if ($verified.ExitCode) { throw 'HUD Spaceland-context offline load failed.' }
    $offlineLog=Get-Content -LiteralPath $verified.Stdout -Raw
    $rows=@(Get-HudVerifiedInventory $offlineLog -BootstrapOnly:($VerificationContext -eq 'Bootstrap'))
    [IO.File]::WriteAllLines((Join-Path $RunRoot 'assets.csv'),[string[]]$rows,[Text.UTF8Encoding]::new($false))
    $state.FF.InventoryVerified=$true
    $roundtrip=Invoke-HudBuildProcess -Work $work -RunRoot $RunRoot -LeaseToken $lease.Token -CleanupState $cleanup -Cdb $cdb -Symbols (Split-Path $ToolProvenance -Parent) -Phase hud-roundtrip -ToolArguments (@('-headless','-unbuffered-io')+$contextArguments+@('-dumpzone','paris_lab_hud'))
    if ($roundtrip.ExitCode) { throw 'HUD LuaFile roundtrip failed.' }
    $extracted=Resolve-IW7BasePath $work 'dump/paris_lab_hud/ui_scripts/paris_lab_hud/__init__.lua'
    $original=Resolve-IW7BasePath $work 'zonetool/paris_lab_hud/ui_scripts/paris_lab_hud/__init__.lua'
    if ((Get-FileHash -LiteralPath $extracted).Hash -ne (Get-FileHash -LiteralPath $original).Hash) { throw 'Loaded FF Lua buffer differs from original source.' }
    Copy-Item -LiteralPath $extracted -Destination (Join-Path $RunRoot 'roundtrip.lua')
    $state.Status='OfflineLoaded'
    $state.RecipientOfflineLinked=$VerificationContext -eq 'Spaceland'
    $state | Add-Member NoteProperty FF ([ordered]@{Path='mod.ff';Bytes=(Get-Item -LiteralPath $ff).Length;SHA256=(Get-FileHash -LiteralPath $ff).Hash;InventoryVerified=$true}) -Force
    $state | Add-Member NoteProperty Build $built -Force
    $state | Add-Member NoteProperty OfflineLoad $verified -Force
    $state | Add-Member NoteProperty Roundtrip $roundtrip -Force
} catch { $state.Status='Failed';$state | Add-Member NoteProperty Failure $_.Exception.Message -Force;throw }
finally {
    if ($cleanup.Confirmed) {
        Complete-HudRestore $state $statePath $lease.Token
    } else { Write-HudJson $state $statePath;Write-Warning 'HUD child exit unconfirmed; inputs and resource lease retained.' }
}
Write-Output "HUD FF retained: $RunRoot/mod.ff; offline load only, render/download pending."
