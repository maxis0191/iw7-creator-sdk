# Pure path/contract/inventory helpers. No native load or process on import.
function Read-BeaconJson([string]$Path,[long]$MaxBytes=1MB) {
    $file=Get-Item -LiteralPath $Path
    if($file.PSIsContainer -or $file.Length -lt 1 -or $file.Length -gt $MaxBytes){throw 'Bounded regular JSON required.'}
    [IO.File]::ReadAllText($file.FullName)|ConvertFrom-Json
}
function Assert-BeaconHash([string]$Path,[string]$Expected) {
    if($Expected -cnotmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected){throw "Pinned input changed: $Path"}
}
function Get-BeaconJobIdentity($Owner,[string]$ExpectedImage,[string]$Phase) {
    $id=$Owner.PID;$image=$Owner.Image;$created=$Owner.CreatedUtc;$priority=$Owner.Priority
    $timestamp=[datetimeoffset]::MinValue
    if(($id -isnot [uint32] -and $id -isnot [int] -and $id -isnot [long]) -or $id -lt 1 -or $id -gt [uint32]::MaxValue -or
       $image -isnot [string] -or !$image -or ![IO.Path]::IsPathFullyQualified($image) -or
       [IO.Path]::GetFullPath($image) -ine [IO.Path]::GetFullPath($ExpectedImage) -or
       $created -isnot [string] -or !$created -or
       ![datetimeoffset]::TryParseExact($created,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$timestamp) -or
       $timestamp.Offset -ne [timespan]::Zero -or $timestamp.Year -lt 2000 -or $priority -ne 0x4000){throw 'Complete original-handle Python identity and BelowNormal priority required before Resume.'}
    [ordered]@{Phase=$Phase;PID=$id;Image=$image;CreatedUtc=$created;Priority=$priority;JobActiveAtClose=$null;ExitCode=$null}
}
function Measure-BeaconOutputFiles($Files,[string]$Work,$InputRelatives) {
    $bytes=0L
    foreach($file in $Files){
        $relative=[IO.Path]::GetRelativePath($Work,$file.FullName).Replace('\','/')
        if($relative -notin $InputRelatives){$bytes+=$file.Length}
    }
    $bytes
}
function Assert-BeaconOutputBudget([long]$Bytes) {
    if($Bytes -lt 0 -or $Bytes -gt 64MB){throw 'Beacon generated output exceeded 64 MiB stop threshold.'}
}
function Get-BeaconInventory([string]$Log) {
    if(!$Log.Contains('Loading zone "sdk_beacon"') -or $Log -match 'could not be found|Could not find referenced|\[ ERROR \]|\[ FATAL \]'){throw 'Beacon inventory missing or unresolved.'}
    $expected=@('material,,mopw/character_park_clown_zombie_shoes','xmodelsurfs,paris_model_probe_lod0','xmodel,paris_model_probe','netconststrings,ncs_mdl_paris_model_probe','rawfile,sdk_beacon')
    $rows=@(foreach($line in $Log -split '\r?\n' | Where-Object {$_ -match 'Loading asset '}){
        if($line -cnotmatch 'Loading asset "([^"\r\n]+)" of type ([a-z0-9]+)\.$'){throw 'Malformed inventory line.'}
        $Matches[2]+','+$Matches[1]
    })
    if($rows.Count -ne 5 -or @($rows|Sort-Object -Unique).Count -ne 5 -or @($expected|Where-Object {$_ -cnotin $rows}).Count){throw 'Exact five-asset beacon inventory required.'}
    $rows
}
function Assert-BeaconPatchSet($Patches) {
    $expected=[ordered]@{
        'zonetool-fab9358-h1-xsurface.patch'='e50c7f18b9e3b8904b441ddf10bb32a3315442d22afec7d174bda699f9db26a0'
        'strict-content-sources.patch'='4d7049216f24474e077ab704dac625c7f335c8264434b7de525e56a96a988d08'
        'zonetool-fab9358-h1-map-layout.patch'='75c26c4eb9d2260dc71a722d4e54aaa49fea03a4e8c0e8554f3643231d0e3cd7'
    }
    if($Patches -isnot [pscustomobject] -or @($Patches.PSObject.Properties).Count -ne 3){throw 'Exact three-patch object required.'}
    foreach($name in $expected.Keys){
        if($name -cnotin $Patches.PSObject.Properties.Name -or $Patches.$name -isnot [string] -or $Patches.$name -ine $expected[$name]){throw 'Pinned H1, strict-material or map-layout patch differs.'}
    }
}
function Assert-BeaconPreparation($Preparation) {
    $prep=$Preparation
    if($prep.schema -cne 'iw7.zonetool-isolated-overlay/1' -or $prep.source_pin -cne 'fab935826c898806855376662a8a03317b3ad8f1' -or
       $prep.feature_macro -cne 'EXPERIMENTAL_IW7' -or $prep.compile_units -ne 413 -or $prep.patched_units -ne 5 -or
       $prep.dependency_libraries -ne 18){throw 'Pinned source preparation with five patched CPPs, 413 units and 18 libraries required.'}
    foreach($field in @('compile_units','patched_units','dependency_libraries')){
        if($prep.$field -isnot [int] -and $prep.$field -isnot [long]){throw 'Integer source preparation counts required.'}
    }
    Assert-BeaconPatchSet $prep.patches
    $cpp=@('src/zonetool/zonetool/h1/converter/iw7/assets/xsurface.cpp','src/zonetool/zonetool/iw7/assets/material.cpp',
        'src/zonetool/zonetool/iw7/assets/techset.cpp','src/zonetool/zonetool/iw7/assets/gfximage.cpp','src/zonetool/zonetool/h1/converter/iw7/assets/clipmap.cpp')
    if($prep.source -isnot [string] -or ![IO.Path]::IsPathFullyQualified($prep.source)){throw 'Absolute retained source required.'}
    $actual=@($prep.readonly_inputs | Where-Object {[IO.Path]::GetExtension($_.path) -ieq '.cpp'} | ForEach-Object {[IO.Path]::GetFullPath($_.path)})
    $expected=@($cpp | ForEach-Object {[IO.Path]::GetFullPath((Join-Path $prep.source $_))})
    if($actual.Count -ne 5 -or @($expected | Where-Object {$_ -notin $actual}).Count){throw 'Exact five retained CPP identities required.'}
    $unvalidated=@($prep.experimental_unvalidated_capabilities)
    if($unvalidated.Count -ne 1 -or $unvalidated[0] -cne 'h1_clipmap_and_mapents_conversion'){throw 'Explicit unvalidated map conversion capability required.'}
}
function Assert-BeaconCandidate([string]$Root,[string]$ArtifactSHA256) {
    $path=Join-Path $Root 'build-artifact.local.json';Assert-BeaconHash $path $ArtifactSHA256
    $artifact=Read-BeaconJson $path
    # Final producer schema is intentionally required, not inferred from an EXE
    # or a successful compiler exit. Shape is coordinated with the H1 owner.
    if($artifact.schema -cne 'iw7.zonetool-community-candidate/1' -or $artifact.macro_compiled -isnot [bool] -or $artifact.macro_compiled -ne $true){throw 'Final macro-qualified candidate receipt required.'}
    Assert-BeaconHash (Join-Path $Root 'preparation.local.json') $artifact.preparation_sha256
    Assert-BeaconHash (Join-Path $Root 'result.local.json') $artifact.result_sha256
    $prep=Read-BeaconJson (Join-Path $Root 'preparation.local.json')
    $result=Read-BeaconJson (Join-Path $Root 'result.local.json')
    Assert-BeaconPreparation $prep
    if($artifact.source_pin -cne $prep.source_pin -or $artifact.compile_units_verified -ne 413){throw 'Final artifact source pin or verified compile count differs.'}
    Assert-BeaconPatchSet $artifact.patch_sha256
    if($result.Schema -cne 'iw7.zonetool-full-build/1' -or $result.Failure -or !$result.ReadOnlyInputsUnchanged -or
       !$result.JobClosureVerified -or !$result.LeaseReleased -or !@($result.Attempts).Count -or
       $result.Attempts[-1].ExitCode -ne 0 -or $result.Attempts[-1].JobActiveAtClose -ne 0){throw 'Final closed successful build evidence required.'}
    $exe=Resolve-IW7BasePath $Root 'bin/zonetool-community.exe'
    if($artifact.executable.path -ine $exe -or (Get-Item -LiteralPath $exe).Length -ne $artifact.executable.bytes){throw 'Candidate EXE path/size differs.'}
    Assert-BeaconHash $exe $artifact.executable.sha256
    $commands=Resolve-IW7BasePath $Root ([IO.Path]::GetRelativePath($Root,$artifact.commands_tlog.path))
    if((Get-Item -LiteralPath $commands).Length -ne $artifact.commands_tlog.bytes -or $artifact.commands_tlog.bytes -gt 16MB){throw 'Bounded real compiler command evidence required.'}
    Assert-BeaconHash $commands $artifact.commands_tlog.sha256
    if(![IO.File]::ReadAllText($commands).Contains('EXPERIMENTAL_IW7')){throw 'Actual compiler command macro evidence missing.'}
    [pscustomobject]@{Path=$exe;SHA256=$artifact.executable.sha256;ArtifactSHA256=$ArtifactSHA256}
}
