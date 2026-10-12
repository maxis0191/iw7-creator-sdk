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
$python=(Get-Command python -ErrorAction Stop).Source
$inputData=[ordered]@{project=$Project;action=$Action;adapter=$Adapter;build_parameters=$BuildParameters;
    active_projects=@($ActiveProject);client_source=$ClientSource;server_source=$ServerSource;protocol=$Protocol;
    target=$Target;tools_root=$ToolsRoot;finalize_root=$FinalizeRoot;output=$Output;
    recipient_proof=$RecipientProof;recipient_root=$RecipientRoot}
$driver=@'
import hashlib, importlib.util, json, os, sys
from pathlib import Path

args = json.loads(sys.argv[1])
report = {"action": args["action"], "adapter": args["adapter"], "steps": [],
          "plan_valid": False, "build_executed": False, "materialized": False,
          "packaged": False, "runtime_ready": False, "owner_accepted": False,
          "errors": [], "pending": []}

def step(name, status, details):
    report["steps"].append({"name": name, "status": status, "details": details})

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
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
            parameters = packager.read_manifest(args["build_parameters"])
            allowed = {"SourceRoot", "SourceReceiptSHA256", "StockRoot", "StockReceipt", "StockReceiptSHA256",
                       "CandidateRoot", "CandidateArtifactSHA256", "ReaderRoot", "RunRoot", "OpsRoot", "JobSource", "JobSourceSHA256"}
            if not isinstance(parameters, dict) or set(parameters) - allowed:
                raise ValueError("BuildParameters contains unknown fields; Run and arbitrary commands are prohibited")
            required = {"SourceRoot", "SourceReceiptSHA256", "StockRoot", "StockReceipt", "StockReceiptSHA256",
                        "CandidateRoot", "ReaderRoot", "RunRoot", "OpsRoot", "JobSource"}
            if required - set(parameters):
                raise ValueError("BuildParameters missing required fields: " + ", ".join(sorted(required - set(parameters))))
            if any(not isinstance(value, str) or not value for value in parameters.values()):
                raise ValueError("BuildParameters values must be nonempty strings")
            if Path(parameters.get("SourceRoot", "")).resolve(strict=True) != project:
                raise ValueError("BuildParameters SourceRoot must equal Project")
            if Path(parameters.get("OpsRoot", "")).resolve(strict=True) != root / "ops":
                raise ValueError("BuildParameters OpsRoot must use this reviewed ToolsRoot")
            report["adapter_plan_requested"] = True
            report["build_parameters_sha256"] = hashlib.sha256(Path(args["build_parameters"]).read_bytes()).hexdigest()
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
    step("payload-and-closure", "pending" if report["pending"] else "not-run",
         report["pending"] or ["Package file hashes and closure will be checked by the finalizer and package gate"])
    report["plan_valid"] = not report["errors"]
except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
    report["errors"].append(str(error))
    step("preflight", "failed", [str(error)])
print(json.dumps(report, ensure_ascii=True))
'@
$raw=& $python -B -c $driver ($inputData|ConvertTo-Json -Depth 6 -Compress)
if($LASTEXITCODE -ne 0){throw 'Creator validator process failed; no build attempted.'}
$report=($raw -join "`n")|ConvertFrom-Json -AsHashtable
if($report.adapter_plan_requested -and $report.plan_valid){
    try {
        # Rehash after validation. Never permit Run in the caller's parameter object.
        if((Get-FileHash -LiteralPath $BuildParameters).Hash -ine $report.build_parameters_sha256){throw 'BuildParameters changed during planning.'}
        $parameters=Get-Content -LiteralPath $BuildParameters -Raw|ConvertFrom-Json -AsHashtable
        $builder=Join-Path $ToolsRoot 'sdk/modding/Build-BeaconFF.ps1'
        $planText=& $builder @parameters
        $plan=($planText -join "`n")|ConvertFrom-Json -AsHashtable
        if($plan.Schema -cne 'iw7.beacon-ff-plan/1' -or $plan.Ready){throw 'Unexpected beacon adapter plan.'}
        $report.steps+=@{name='adapter-plan';status='passed';details=@('Real Build-BeaconFF read-only plan completed; no native build was run')}
        $report.adapter_plan=$plan
    } catch {
        $report.plan_valid=$false;$report.errors+=@($_.Exception.Message)
        $report.steps+=@{name='adapter-plan';status='failed';details=@($_.Exception.Message)}
    }
}
if($Action -ceq 'Build'){
    # Deliberate pre-mutation gate until the stock binding and finalizer API have
    # been integrated and independently reviewed. Presence of a file is no proof.
    $report.errors+=@('Build chain is not connected: stock binding and Finalize-BeaconProject integration are pending; no lease, staging or build attempted.')
    $report.steps+=@{name='build';status='blocked';details=@($report.errors[-1])}
} else {
    $report.steps+=@{name='build';status='not-run';details=@('Plan does not compile, finalize or package')}
}
$report.steps+=@{name='package';status='not-run';details=@('No ZIP created; static plan validity is not build or runtime acceptance')}
if($Json){$report|ConvertTo-Json -Depth 20}
else {
    foreach($step in $report.steps){Write-Output ('[{0}] {1}' -f $step.status,$step.name);foreach($detail in $step.details){Write-Output ('  '+$detail)}}
    Write-Output ('Plan valid: {0}; build executed: false; packaged: false; runtime accepted: false' -f $report.plan_valid)
}
if($Action -ceq 'Build' -or !$report.plan_valid){exit 1}
