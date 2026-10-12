param(
    [Parameter(Mandatory)][string]$Project,
    [ValidateSet('Plan','Build')][string]$Action='Plan',
    [ValidateSet('None','BeaconV1','AnimationProbe','MaterialV2')][string]$Adapter='None',
    [string]$BuildParameters,
    [string[]]$ActiveProject=@(),
    [string]$ClientSource,
    [string]$ServerSource,
    [Nullable[int]]$Protocol,
    [ValidateSet('stock','native')][string]$Target='stock',
    [string]$FinalizeRoot,
    [string]$Output,
    [string]$RecipientProof,
    [string]$RecipientRoot,
    [string]$ToolsRoot=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$Json
)
# Local orchestration only. Project manifests never supply executable commands.
# Plan imports the reviewed Python validators and never writes files or loads native code.
$ErrorActionPreference='Stop'
$Action=@('Plan','Build')|Where-Object {$_ -ieq $Action}
$Adapter=@('None','BeaconV1','AnimationProbe','MaterialV2')|Where-Object {$_ -ieq $Adapter}
$Target=$Target.ToLowerInvariant()
$python=(Get-Command python -ErrorAction Stop).Source
$inputData=[ordered]@{project=$Project;action=$Action;adapter=$Adapter;build_parameters=$BuildParameters;
    active_projects=@($ActiveProject);client_source=$ClientSource;server_source=$ServerSource;protocol=$Protocol;
    target=$Target;tools_root=$ToolsRoot;finalize_root=$FinalizeRoot;output=$Output;
    recipient_proof=$RecipientProof;recipient_root=$RecipientRoot}
function Assert-CreatorBuildParameters($Parameters) {
    # This is a caller-side allowlist, not the builder's broader parameter set.
    # In particular, Run is never allowed in a JSON-provided splat.
    $allowed=@('SourceRoot','SourceReceiptSHA256','StockRoot','StockReceipt','StockReceiptSHA256',
        'CandidateRoot','CandidateArtifactSHA256','ReaderRoot','RunRoot','OpsRoot','JobSource','JobSourceSHA256',
        'StockBindingReceipt','StockBindingReceiptSHA256','ReviewedStockManifest','ReviewedStockManifestSHA256')
    if($Parameters -isnot [Collections.IDictionary]){throw 'BuildParameters must be an object.'}
    foreach($key in $Parameters.Keys){
        if($key -cnotin $allowed){throw 'BuildParameters contains unknown fields; Run and arbitrary commands are prohibited.'}
        if($Parameters[$key] -isnot [string] -or !$Parameters[$key]){throw 'BuildParameters values must be nonempty strings.'}
    }
    $required=@('SourceRoot','SourceReceiptSHA256','StockRoot','StockReceipt','StockReceiptSHA256','CandidateRoot','ReaderRoot','RunRoot','OpsRoot','JobSource')
    $binding=@('StockBindingReceipt','StockBindingReceiptSHA256','ReviewedStockManifest','ReviewedStockManifestSHA256')
    if($Action -ceq 'Build' -or @($binding|Where-Object {$_ -cin $Parameters.Keys}).Count){$required+=$binding}
    if($Action -ceq 'Build'){$required+=@('CandidateArtifactSHA256','JobSourceSHA256')}
    foreach($key in $required){if($key -cnotin $Parameters.Keys){throw "BuildParameters missing required field: $key"}}
}
function Read-CreatorBuildParameters([string]$Path,[string]$ExpectedSHA256) {
    # One bounded byte snapshot is both hashed and parsed. A later file rewrite
    # cannot change this object or introduce parameters after its hash check.
    $buffer=[byte[]]::new(1MB+1);$length=0
    $stream=[IO.File]::Open($Path,'Open','Read','Read')
    try {
        while($length -lt $buffer.Length){
            $count=$stream.Read($buffer,$length,$buffer.Length-$length)
            if(!$count){break};$length+=$count
        }
    } finally {$stream.Dispose()}
    if($length -gt 1MB){throw 'BuildParameters exceeds 1 MiB.'}
    $memory=[IO.MemoryStream]::new($buffer,0,$length,$false)
    try {$digest=(Get-FileHash -InputStream $memory -Algorithm SHA256).Hash}
    finally {$memory.Dispose()}
    if($ExpectedSHA256 -cnotmatch '^[a-f0-9]{64}$' -or $digest -ine $ExpectedSHA256){throw 'BuildParameters changed during planning.'}
    $text=[Text.UTF8Encoding]::new($false,$true).GetString($buffer,0,$length).TrimStart([char]0xFEFF)
    $parameters=$text|ConvertFrom-Json -AsHashtable
    Assert-CreatorBuildParameters $parameters
    return $parameters
}
$driver=@'
import hashlib, importlib.util, json, os, sys
from pathlib import Path

args = json.loads(sys.argv[1])
report = {"action": args["action"], "adapter": args["adapter"], "steps": [],
          "plan_valid": False, "build_executed": False, "build_verified": False, "materialized": False,
          "packaged": False, "runtime_ready": False, "owner_accepted": False,
          "errors": [], "pending": []}

def step(name, status, details):
    report["steps"].append({"name": name, "status": status, "details": details})

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def unique_parameters(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate BuildParameters key: " + key)
        result[key] = value
    return result

try:
    root = Path(args["tools_root"]).resolve(strict=True)
    sdk = module(root / "sdk/modding/manifest.py", "creator_sdk")
    packager = module(root / "ops/modding/Package-CommunityMod.py", "creator_packager")
    if len(args["active_projects"]) > 64:
        raise ValueError("At most 64 active projects can be inspected")
    project = packager.no_redirects(args["project"])
    if not project.is_dir():
        raise ValueError("Project must be a directory containing manifest.json")
    report["project"] = str(project)
    projects = [project, *(packager.no_redirects(p) for p in args["active_projects"])]
    manifests = []
    for index, directory in enumerate(projects):
        path = packager.payload_path(directory, "manifest.json")
        data = sdk.load_manifest(path)
        manifests.append(data)
        result = sdk.validate(data, stage="plan", target=args["target"],
                              client_source=args["client_source"], server_source=args["server_source"])
        label = "project-contract" if index == 0 else "active-contract:" + str(directory)
        step(label, "passed" if result["valid"] else "failed", result["errors"] or ["Declared SDK plan is valid"])
        report["errors"].extend(label + ": " + text for text in result["errors"])
        report["pending"].extend(label + ": " + text for text in result.get("pending", []))
    if report["errors"]:
        raise ValueError("Fix invalid project contracts before compatibility or adapter checks")
    errors = packager.compat.check_environment(manifests, client_source=args["client_source"],
        server_source=args["server_source"], protocol=args["protocol"], mode="cp")
    step("dependencies-and-target", "passed" if not errors else "blocked", errors or
         ["Exact versions, conflicts, asset/destination collisions and declared source/protocol checked",
          "Supplied source pins are assertions; no installed binary or server was inspected"])
    report["errors"].extend(errors)
    if not args["client_source"] or not args["server_source"] or args["protocol"] is None:
        report["pending"].append("Supply ClientSource, ServerSource and Protocol for a complete compatibility plan")
    data = manifests[0]
    if args["adapter"] == "BeaconV1":
        package = data["package"]
        if data["namespace"] != "sdk_beacon" or package["id"] != "sdk_beacon" or package["maps"] != ["cp_zmb"]:
            raise ValueError("BeaconV1 accepts only the fixed sdk_beacon original-template identity on cp_zmb")
        template = (root / "sdk/modding/examples/beacon/sdk_beacon.gsc").read_bytes()
        source = packager.payload_path(project, "sdk_beacon.gsc")
        if source.stat().st_size != len(template) or source.read_bytes() != template:
            raise ValueError("BeaconV1 requires the exact reviewed template GSC; it is not a universal compiler")
        report["beacon_gsc_sha256"] = hashlib.sha256(template).hexdigest()
        step("adapter-identity", "passed", ["Fixed BeaconV1 template GSC, namespace and map match"])
        if args["build_parameters"]:
            with Path(args["build_parameters"]).open("rb") as stream:
                parameter_bytes = stream.read(1024 * 1024 + 1)
            if len(parameter_bytes) > 1024 * 1024:
                raise ValueError("BuildParameters exceeds 1 MiB")
            parameters = json.loads(parameter_bytes.decode("utf-8-sig"), object_pairs_hook=unique_parameters,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Invalid JSON constant: " + value)))
            allowed = {"SourceRoot", "SourceReceiptSHA256", "StockRoot", "StockReceipt", "StockReceiptSHA256",
                       "CandidateRoot", "CandidateArtifactSHA256", "ReaderRoot", "RunRoot", "OpsRoot", "JobSource", "JobSourceSHA256",
                       "StockBindingReceipt", "StockBindingReceiptSHA256", "ReviewedStockManifest", "ReviewedStockManifestSHA256"}
            if not isinstance(parameters, dict) or set(parameters) - allowed:
                raise ValueError("BuildParameters contains unknown fields; Run and arbitrary commands are prohibited")
            required = {"SourceRoot", "SourceReceiptSHA256", "StockRoot", "StockReceipt", "StockReceiptSHA256",
                        "CandidateRoot", "ReaderRoot", "RunRoot", "OpsRoot", "JobSource"}
            binding = {"StockBindingReceipt", "StockBindingReceiptSHA256", "ReviewedStockManifest", "ReviewedStockManifestSHA256"}
            if binding & set(parameters):
                required |= binding
            if args["action"] == "Build":
                required |= binding | {"CandidateArtifactSHA256", "JobSourceSHA256"}
            if required - set(parameters):
                raise ValueError("BuildParameters missing required fields: " + ", ".join(sorted(required - set(parameters))))
            if any(not isinstance(value, str) or not value for value in parameters.values()):
                raise ValueError("BuildParameters values must be nonempty strings")
            if Path(parameters.get("SourceRoot", "")).resolve(strict=True) != project:
                raise ValueError("BuildParameters SourceRoot must equal Project")
            if Path(parameters.get("OpsRoot", "")).resolve(strict=True) != root / "ops":
                raise ValueError("BuildParameters OpsRoot must use this reviewed ToolsRoot")
            report["adapter_plan_requested"] = True
            report["build_parameters_sha256"] = hashlib.sha256(parameter_bytes).hexdigest()
        else:
            step("adapter-plan", "pending", ["BuildParameters is required for stock/tool/receipt checks; no native build was run"])
    elif args["adapter"] != "None":
        message = args["adapter"] + " adapter is named but not connected or qualified in Creator"
        step("adapter-plan", "blocked", [message])
        report["errors"].append(message)
    elif args["build_parameters"]:
        raise ValueError("BuildParameters requires an explicit supported adapter")
    else:
        step("adapter-plan", "not-requested", ["Contract planning only; no build adapter selected"])
    if args["action"] == "Build":
        if args["adapter"] != "BeaconV1" or not args["build_parameters"]:
            raise ValueError("Build requires BeaconV1 and complete BuildParameters; no build attempted")
        if not args["finalize_root"] or not args["output"]:
            raise ValueError("Build requires fresh FinalizeRoot and Output paths")
        if bool(args["recipient_proof"]) != bool(args["recipient_root"]):
            raise ValueError("RecipientProof and RecipientRoot must be supplied together")
        if args["recipient_proof"]:
            if not packager.no_redirects(args["recipient_proof"]).is_file() or not packager.no_redirects(args["recipient_root"]).is_dir():
                raise ValueError("Recipient proof file and root must exist without redirects")
        fresh = [Path(os.path.abspath(value)) for value in (parameters["RunRoot"], args["finalize_root"], args["output"])]
        for path in fresh:
            packager.no_redirects(path.parent)
            if path.exists() or path.is_symlink():
                raise ValueError("Fresh output path required: " + str(path))
        for index, first in enumerate(fresh):
            for second in fresh[index + 1:]:
                if first == second or first in second.parents or second in first.parents:
                    raise ValueError("RunRoot, FinalizeRoot and Output must be separate, non-nested paths")
        for directory in projects:
            if any(path == directory or path in directory.parents or directory in path.parents for path in fresh):
                raise ValueError("Build outputs must be outside all input projects")
        finalizer = root / "sdk/modding/Finalize-BeaconProject.py"
        if not finalizer.is_file():
            raise ValueError("Reviewed Finalize-BeaconProject.py is missing from ToolsRoot")
        report.update(build_root=str(fresh[0]), finalize_root=str(fresh[1]), output=str(fresh[2]))
        step("build-preflight", "passed", ["Explicit build pins and separate fresh output paths supplied; no build attempted yet"])
    step("payload-and-closure", "pending" if report["pending"] else "not-run",
         report["pending"] or ["Package file hashes and closure will be checked by the finalizer and package gate"])
    report["plan_valid"] = not report["errors"]
except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, ImportError) as error:
    report["errors"].append(str(error))
    step("preflight", "failed", [str(error)])
print(json.dumps(report, ensure_ascii=True))
'@
$raw=& $python -B -c $driver ($inputData|ConvertTo-Json -Depth 6 -Compress)
if($LASTEXITCODE -ne 0){throw 'Creator validator process failed; no build attempted.'}
$report=($raw -join "`n")|ConvertFrom-Json -AsHashtable
if($report.adapter_plan_requested -and $report.plan_valid){
    try {
        $parameters=Read-CreatorBuildParameters $BuildParameters $report.build_parameters_sha256
        $builder=Join-Path $ToolsRoot 'sdk/modding/Build-BeaconFF.ps1'
        $supported=(Get-Command $builder -ErrorAction Stop).Parameters
        foreach($key in $parameters.Keys){if(!$supported.ContainsKey($key)){throw "Beacon builder does not support parameter $key; stock binding integration may be pending."}}
        Assert-CreatorBuildParameters $parameters
        $planText=& $builder @parameters
        $plan=($planText -join "`n")|ConvertFrom-Json -AsHashtable
        if($plan.Schema -cne 'iw7.beacon-ff-plan/1' -or $plan.Ready -cne $false -or $plan.CandidatePending -isnot [bool]){throw 'Unexpected beacon adapter plan.'}
        $report.steps+=@{name='adapter-plan';status='passed';details=@('Real Build-BeaconFF read-only plan completed; no native build was run')}
        $report.adapter_plan=$plan
    } catch {
        $report.plan_valid=$false;$report.errors+=@($_.Exception.Message)
        $report.steps+=@{name='adapter-plan';status='failed';details=@($_.Exception.Message)}
    }
}
if($Action -ceq 'Build'){
    if($report.plan_valid -and $report.adapter_plan){
        $phase='build'
        try {
            $parameters=Read-CreatorBuildParameters $BuildParameters $report.build_parameters_sha256
            if($report.adapter_plan.CandidatePending){throw 'Beacon candidate is not pinned and verified.'}
            # Native admission, process ownership, time/byte budgets and restore
            # belong to the reviewed builder. Do not create another reservation.
            Assert-CreatorBuildParameters $parameters
            $report.build_executed=$true
            $null=& $builder @parameters -Run
            $report.steps+=@{name='build';status='completed';details=@('Builder returned; finalizer must still verify its persisted evidence')}
            $phase='finalize'
            $finalizer=Join-Path $ToolsRoot 'sdk/modding/Finalize-BeaconProject.py'
            $finalArgs=@('-B',$finalizer,'--project',$Project,'--build-root',$report.build_root,'--output-root',$report.finalize_root,
                '--client-source',$ClientSource,'--server-source',$ServerSource)
            if($RecipientProof){$finalArgs+=@('--recipient-proof',$RecipientProof,'--recipient-root',$RecipientRoot)}
            $finalText=& $python @finalArgs
            $finalExit=$LASTEXITCODE
            $final=($finalText -join "`n")|ConvertFrom-Json -AsHashtable
            $report.finalization=$final
            if($finalExit -ne 0 -or $final.api -cne 'beacon-finalize/1' -or $final.materialized -cne $true -or $final.runtime_ready -cne $false){throw 'Finalizer refused or returned an unexpected evidence contract.'}
            if([IO.Path]::GetFullPath($final.candidate_root) -ine $report.finalize_root -or [IO.Path]::GetFullPath($final.manifest_path) -ine (Join-Path $report.finalize_root 'manifest.json')){throw 'Finalizer returned unexpected output paths.'}
            $report.build_verified=$true;$report.materialized=$true
            $report.steps+=@{name='finalize';status='passed';details=@('Measured candidate created from verified build evidence; runtime acceptance remains false')}
            $phase='package'
            if($final.closure_complete -cne $true -or $final.package_ready -cne $true){
                $report.pending+=@($final.blockers)
                throw ('Candidate materialized; package blocked by incomplete closure or static qualification: '+($final.blockers -join '; '))
            }
            $packager=Join-Path $ToolsRoot 'ops/modding/Package-CommunityMod.py'
            $packageArgs=@('-B',$packager,$final.manifest_path,'--root',$final.candidate_root,'--output',$report.output,
                '--sdk-root',(Join-Path $ToolsRoot 'sdk/modding'),'--client-source',$ClientSource,'--server-source',$ServerSource,
                '--protocol',[string]$Protocol,'--target',$Target)
            foreach($active in $ActiveProject){$packageArgs+=@('--active',(Join-Path $active 'manifest.json'),$active)}
            $packageText=& $python @packageArgs
            $packageExit=$LASTEXITCODE
            $package=($packageText -join "`n")|ConvertFrom-Json -AsHashtable
            $report.package_result=$package
            if($packageExit -ne 0 -or $package.valid -cne $true -or $package.packaged -cne $true){throw ('Package gate refused: '+($package.errors -join '; '))}
            if([IO.Path]::GetFullPath($package.archive) -ine $report.output -or (Get-FileHash -LiteralPath $report.output).Hash -ine $package.archive_sha256 -or (Get-Item -LiteralPath $report.output).Length -ne $package.archive_bytes){throw 'Published archive does not match package receipt.'}
            $report.packaged=$true
            $report.steps+=@{name='package';status='passed';details=@('Existing ZIP writer rechecked payloads and compatibility; archive hash measured')}
        } catch {
            $report.errors+=@($_.Exception.Message)
            $report.steps+=@{name=$phase;status='blocked';details=@($_.Exception.Message)}
        }
    } else {
        $report.steps+=@{name='build';status='blocked';details=@('Preflight failed; no native builder invoked')}
    }
} else {
    $report.steps+=@{name='build';status='not-run';details=@('Plan does not compile, finalize or package')}
}
if(!@($report.steps|Where-Object name -EQ 'package').Count){$report.steps+=@{name='package';status='not-run';details=@('No ZIP created; static plan validity is not build or runtime acceptance')}}
if($Json){$report|ConvertTo-Json -Depth 20}
else {
    foreach($step in $report.steps){Write-Output ('[{0}] {1}' -f $step.status,$step.name);foreach($detail in $step.details){Write-Output ('  '+$detail)}}
    Write-Output ('Plan valid: {0}; build executed: {1}; build verified: {2}; materialized: {3}; packaged: {4}; runtime accepted: false' -f $report.plan_valid,$report.build_executed,$report.build_verified,$report.materialized,$report.packaged)
}
if(!$report.plan_valid -or $report.errors.Count -or ($Action -ceq 'Build' -and !$report.packaged)){exit 1}
