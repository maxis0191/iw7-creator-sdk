$ErrorActionPreference='Stop'
$sdk=Split-Path $PSScriptRoot -Parent
foreach($name in @('Build-BeaconFF.ps1','BeaconFF.Core.ps1')){
    $tokens=$null;$errors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile((Join-Path $sdk $name),[ref]$tokens,[ref]$errors)
    if($errors.Count){throw ($errors|Out-String)}
}
. "$sdk/BeaconFF.Core.ps1"
$rows=@('material,,mopw/character_park_clown_zombie_shoes','xmodelsurfs,paris_model_probe_lod0','xmodel,paris_model_probe','netconststrings,ncs_mdl_paris_model_probe','rawfile,sdk_beacon')
function MakeLog($Rows){'Loading zone "sdk_beacon"'+"`n"+(@(foreach($row in $Rows){$type,$name=$row -split ',',2;'Loading asset "'+$name+'" of type '+$type+'.'}) -join "`n")}
$log=MakeLog $rows
if(@(Get-BeaconInventory $log).Count -ne 5){throw 'Valid five-asset fixture refused.'}
$bad=@($log.Replace('rawfile.','image.'),$log.Replace('sdk_beacon','paris_model_probe'),(MakeLog $rows[0..3]),($log+"`n"+'[ ERROR ] failed'),($log+"`n"+'Loading asset "extra" of type rawfile.'))
foreach($sample in $bad){$caught=$false;try{$null=Get-BeaconInventory $sample}catch{$caught=$true};if(!$caught){throw 'Invalid inventory accepted.'}}
function ExpectRefusal([scriptblock]$Action){$caught=$false;try{& $Action}catch{$caught=$true};if(!$caught){throw 'Invalid boundary fixture accepted.'}}
$python=Join-Path $sdk 'python-fixture.exe'
$valid=[ordered]@{PID=37;Image=$python;CreatedUtc=([datetime]::new(2026,10,12,1,2,3,[DateTimeKind]::Utc).ToString('o'));Priority=0x4000}
$identity=Get-BeaconJobIdentity ([pscustomobject]$valid) $python 'build'
if($identity.PID -ne 37 -or $identity.Priority -ne 0x4000){throw 'Original identity fields lost.'}
foreach($pair in @(@('PID',0),@('PID',$null),@('Image',$null),@('Image','relative.exe'),@('Image',(Join-Path $sdk 'other.exe')),
    @('CreatedUtc',$null),@('CreatedUtc','invalid'),@('CreatedUtc','2026-10-12T01:02:03.0000000+02:00'),@('Priority',0x20))){
    $invalid=[ordered]@{};foreach($key in $valid.Keys){$invalid[$key]=$valid[$key]};$invalid[$pair[0]]=$pair[1]
    ExpectRefusal {Get-BeaconJobIdentity ([pscustomobject]$invalid) $python 'build'}
}
# End-of-phase accounting includes logs/receipts/artifacts even outside work;
# only explicitly staged inputs are excluded. No files or processes are created.
$run=Join-Path $sdk 'fixture';$work=Join-Path $run 'work'
$files=@([pscustomobject]@{FullName=(Join-Path $work 'stock.ff');Length=900000000L},
    [pscustomobject]@{FullName=(Join-Path $run 'state.local.json');Length=10L},
    [pscustomobject]@{FullName=(Join-Path $run 'mod.ff');Length=20L},
    [pscustomobject]@{FullName=(Join-Path $work 'dump/result');Length=30L})
$bytes=Measure-BeaconOutputFiles $files $work @('stock.ff')
if($bytes -ne 60){throw 'Final output accounting omitted a receipt/artifact or included stock.'}
Assert-BeaconOutputBudget 64MB
ExpectRefusal {Assert-BeaconOutputBudget (64MB+1)}
ExpectRefusal {Assert-BeaconOutputBudget -1}
$source=Join-Path $sdk 'source-fixture'
$prep=[pscustomobject]@{
    schema='iw7.zonetool-isolated-overlay/1';source_pin='fab935826c898806855376662a8a03317b3ad8f1';source=$source
    feature_macro='EXPERIMENTAL_IW7';compile_units=413;patched_units=5;dependency_libraries=18
    patches=[pscustomobject]@{
        'zonetool-fab9358-h1-xsurface.patch'='e50c7f18b9e3b8904b441ddf10bb32a3315442d22afec7d174bda699f9db26a0'
        'strict-content-sources.patch'='4d7049216f24474e077ab704dac625c7f335c8264434b7de525e56a96a988d08'
        'zonetool-fab9358-h1-map-layout.patch'='75c26c4eb9d2260dc71a722d4e54aaa49fea03a4e8c0e8554f3643231d0e3cd7'
    }
    readonly_inputs=@('h1/converter/iw7/assets/xsurface.cpp','iw7/assets/material.cpp','iw7/assets/techset.cpp',
        'iw7/assets/gfximage.cpp','h1/converter/iw7/assets/clipmap.cpp') | ForEach-Object {[pscustomobject]@{path=(Join-Path $source ('src/zonetool/zonetool/'+$_))}}
    experimental_unvalidated_capabilities=@('h1_clipmap_and_mapents_conversion')
}
Assert-BeaconPreparation $prep
$mutations=@(
    {param($p) $p.patches | Add-Member NoteProperty 'extra.patch' ('a'*64)},
    {param($p) $p.patches.PSObject.Properties.Remove('zonetool-fab9358-h1-map-layout.patch')},
    {param($p) $p.patches.'zonetool-fab9358-h1-map-layout.patch'='b'*64},
    {param($p) $p.patches=@($p.patches,$p.patches,$p.patches)},
    {param($p) $p.readonly_inputs[4].path=$p.readonly_inputs[0].path},
    {param($p) $p.readonly_inputs+=,[pscustomobject]@{path=(Join-Path $source 'extra.cpp')}},
    {param($p) $p.patched_units=4},
    {param($p) $p.compile_units='413'},
    {param($p) $p.dependency_libraries=19},
    {param($p) $p.experimental_unvalidated_capabilities=@()},
    {param($p) $p.experimental_unvalidated_capabilities+=,'unknown'},
    {param($p) $p.source_pin='0'*40}
)
foreach($mutation in $mutations){
    $invalid=$prep|ConvertTo-Json -Depth 6|ConvertFrom-Json
    & $mutation $invalid
    ExpectRefusal {Assert-BeaconPreparation $invalid}
}
'PASS: two PowerShell parses; inventory, identity, output bounds and exact source-contract fixtures (12 contract refusals); no Add-Type/native/runtime.'
