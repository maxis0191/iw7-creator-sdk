param(
    [Parameter(Mandatory)][string]$BuildPlanPath,
    [Parameter(Mandatory)][string]$BuildPlanSHA256,
    [Parameter(Mandatory)][string]$BuildReceiptPath,
    [Parameter(Mandatory)][string]$BuildReceiptSHA256,
    [Parameter(Mandatory)][string]$OutputPath
)
# Metadata-only: no payload copy/hash, package-stage validation or game action.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot)))
. "$repo/ops/Base-Client.Core.ps1"
. "$repo/ops/Agent-Scenario.Core.ps1"
. "$repo/ops/modding/Agent-Sound.Package.ps1"
$template=Join-Path $PSScriptRoot 'manifest.json'
$manifest=Read-IW7SoundMetadata $template (Get-FileHash -LiteralPath $template).Hash
$state=Read-IW7SoundMetadata $BuildReceiptPath $BuildReceiptSHA256
$plan=Read-IW7SoundMetadata $BuildPlanPath $BuildPlanSHA256
if($state.Artifacts -isnot [array] -or $state.Artifacts.Count -ne 3){throw 'Completed three-artifact StandardMod metadata required.'}
$names=@('mod.ff','mod.sabl','mod.sabs');$caps=@(1600,131072,4096)
for($i=0;$i -lt 3;$i++){
    $artifact=$state.Artifacts[$i];$destination='mods/sdk_original_sound_v1/'+$names[$i]
    $entries=@($manifest.package.files|Where-Object {$_.role -ceq 'client' -and $_.destination -ceq $destination})
    if($entries.Count -ne 1 -or $artifact.Relative -cne ('zone/'+$names[$i])){throw 'Exact standard artifact/destination mapping required.'}
    # These are producer assertions, not measurements made by this adapter.
    $entries[0].bytes=$artifact.Bytes;$entries[0].sha256=$artifact.SHA256
}
$sound=@{BuildPlanPath=$BuildPlanPath;BuildPlanSHA256=$BuildPlanSHA256;BuildReceiptPath=$BuildReceiptPath;
    BuildReceiptSHA256=$BuildReceiptSHA256;Files=$manifest.package.files}
$proof=Read-IW7SoundProducerEvidence $sound $repo
if(!$proof.MetadataVerified -or $proof.PayloadMeasured -or $proof.Ready -or $proof.PlaybackVerified){throw 'Producer metadata scope differs.'}
for($i=0;$i -lt 3;$i++){
    try{Assert-IW7ScenarioInteger $state.Artifacts[$i].Bytes 1 $caps[$i]}
    catch{throw ('Sound HTTP cap exceeded or invalid size: '+$names[$i]+' must be 1..'+$caps[$i]+' bytes.')}
}
if(![IO.Path]::IsPathFullyQualified($OutputPath)){throw 'Absolute fresh output manifest path required.'}
$output=[IO.Path]::GetFullPath($OutputPath)
$output=Resolve-IW7BasePath (Split-Path $output) (Split-Path $output -Leaf)
if($plan.RunRoot -isnot [string] -or ![IO.Path]::IsPathFullyQualified($plan.RunRoot)){throw 'Absolute producer run required.'}
$producer=[IO.Path]::GetFullPath($plan.RunRoot).TrimEnd('\','/')
if($output -ieq $producer -or $output.StartsWith($producer+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){
    throw 'Output must remain outside the closed producer run.'
}
if(Test-Path -LiteralPath $output){throw 'Output exists; never overwrite a materialized plan.'}
if(!(Test-Path -LiteralPath (Split-Path $output) -PathType Container)){throw 'Create an explicit owned output directory first.'}
$raw=[Text.UTF8Encoding]::new($false).GetBytes(($manifest|ConvertTo-Json -Depth 25)+[Environment]::NewLine)
if($raw.Length -gt 256KB){throw 'Materialized metadata exceeds 256 KiB.'}
$stream=$null;$created=$false
try{
    $stream=[IO.File]::Open($output,'CreateNew','Write','None');$created=$true
    $stream.Write($raw,0,$raw.Length);$stream.Dispose();$stream=$null
    # The authoritative SDK is the only plan validator; no payload root is passed.
    $result=@(& python -B "$repo/sdk/modding/manifest.py" $output --stage plan --target native)
    if($LASTEXITCODE){throw ('SDK plan validation refused: '+($result -join "`n"))}
    $validation=($result -join "`n")|ConvertFrom-Json -AsHashtable
    if(!$validation.valid -or $validation.ready -or $validation.runtime_ready -or $validation.owner_accepted -or $validation.checked.Count){throw 'SDK plan validation overclaims qualification.'}
    [ordered]@{OutputPath=$output;ManifestSHA256=(Get-FileHash -LiteralPath $output).Hash;
        ProducerPlanSHA256=$BuildPlanSHA256;ProducerStateSHA256=$BuildReceiptSHA256;ProducerMetadataVerified=$true;
        ClientMeasurementsCopiedFromReceipt=3;PayloadMeasured=$false;PackageReady=$false;RuntimeReady=$false;OwnerAccepted=$false;
        Pending=$validation.pending}|ConvertTo-Json -Depth 6
}catch{
    if($stream){$stream.Dispose()}
    # Only the file created above belongs to this operation. No directory deletion.
    if($created -and (Test-Path -LiteralPath $output)){Remove-Item -LiteralPath $output}
    throw
}
