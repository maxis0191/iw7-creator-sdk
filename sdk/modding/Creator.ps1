param(
    [Parameter(Mandatory)][string]$Project,
    [ValidateSet('Plan','Build','Bind','Materialize','Package')][string]$Action='Plan',
    [ValidateSet('None','BeaconV1','BeaconSelfContainedV1','ModelLabV2','OriginalArenaV1','AnimationProbe','MaterialV2')][string]$Adapter='None',
    [string]$BuildParameters,
    [string]$BuildRoot,
    [string]$ModelSourceRoot,
    [string]$ReviewReference,
    [string[]]$ActiveProject=@(),
    [string]$ClientSource,
    [string]$ServerSource,
    [Nullable[int]]$Protocol,
    [ValidateSet('stock','native')][string]$Target='stock',
    [string]$FinalizeRoot,
    [string]$Output,
    [ValidateSet('staging','player')][string]$PackageLayout='staging',
    [ValidateSet('en','fr')][string]$PlayerLanguage='en',
    [string]$RecipientProof,
    [string]$RecipientRoot,
    [string]$GscAuditEvidence,
    [string]$ToolsRoot=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$Json
)
# Local orchestration only. Project manifests never supply executable commands.
# Plan imports the reviewed Python validators and never writes files or loads native code.
$ErrorActionPreference='Stop'
$Action=@('Plan','Build','Bind','Materialize','Package')|Where-Object {$_ -ieq $Action}
$Adapter=@('None','BeaconV1','BeaconSelfContainedV1','ModelLabV2','OriginalArenaV1','AnimationProbe','MaterialV2')|Where-Object {$_ -ieq $Adapter}
$Target=$Target.ToLowerInvariant()
$PackageLayout=$PackageLayout.ToLowerInvariant()
$PlayerLanguage=$PlayerLanguage.ToLowerInvariant()
$python=(Get-Command python -ErrorAction Stop).Source
$inputData=[ordered]@{project=$Project;action=$Action;adapter=$Adapter;build_parameters=$BuildParameters;build_root=$BuildRoot;
    model_source_root=$ModelSourceRoot;review_reference=$ReviewReference;
    active_projects=@($ActiveProject);client_source=$ClientSource;server_source=$ServerSource;protocol=$Protocol;
    target=$Target;tools_root=$ToolsRoot;finalize_root=$FinalizeRoot;output=$Output;
    package_layout=$PackageLayout;player_language=$PlayerLanguage;
    package_options_supplied=($PSBoundParameters.ContainsKey('PackageLayout') -or $PSBoundParameters.ContainsKey('PlayerLanguage'));
    recipient_proof=$RecipientProof;recipient_root=$RecipientRoot;gsc_audit_evidence=$GscAuditEvidence}
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
function Invoke-CreatorPackage([string]$ManifestPath,[string]$CandidateRoot,[Collections.IDictionary]$Report) {
    # Shared with Build: the existing distribution command is the sole ZIP writer.
    $packager=Join-Path $ToolsRoot 'ops/modding/Package-CommunityMod.py'
    $packageArgs=@('-B',$packager,$ManifestPath,'--root',$CandidateRoot,'--output',$Report.output,
        '--sdk-root',(Join-Path $ToolsRoot 'sdk/modding'),'--client-source',$ClientSource,'--server-source',$ServerSource,
        '--protocol',[string]$Protocol,'--target',$Target)
    if($Action -ceq 'Package'){$packageArgs+=@('--layout',$PackageLayout,'--player-language',$PlayerLanguage)}
    foreach($active in $ActiveProject){$packageArgs+=@('--active',(Join-Path $active 'manifest.json'),$active)}
    $packageText=& $python @packageArgs
    $packageExit=$LASTEXITCODE
    $package=($packageText -join "`n")|ConvertFrom-Json -AsHashtable
    $Report.package_result=$package
    if($packageExit -ne 0 -or $package.valid -cne $true -or $package.packaged -cne $true){throw ('Package gate refused: '+($package.errors -join '; '))}
    if([IO.Path]::GetFullPath($package.archive) -ine $Report.output -or (Get-FileHash -LiteralPath $Report.output).Hash -ine $package.archive_sha256 -or (Get-Item -LiteralPath $Report.output).Length -ne $package.archive_bytes){throw 'Published archive does not match package receipt.'}
    $Report.packaged=$true
    $Report.steps+=@{name='package';status='passed';details=@('Existing ZIP writer rechecked payloads and compatibility; archive hash measured')}
}
$driver=@'
import hashlib, importlib.util, json, os, sys
from pathlib import Path

args = json.loads(sys.argv[1])
report = {"action": args["action"], "adapter": args["adapter"], "steps": [],
          "plan_valid": False, "build_executed": False, "build_verified": False, "materialized": False,
          "bindings_written": False, "packaged": False, "runtime_ready": False, "owner_accepted": False,
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
    if args["package_layout"] not in ("staging", "player") or args["player_language"] not in ("en", "fr"):
        raise ValueError("PackageLayout must be staging or player and PlayerLanguage must be en or fr")
    if args["action"] != "Package" and args["package_options_supplied"]:
        raise ValueError("PackageLayout and PlayerLanguage require Action Package")
    if args["package_layout"] != "player" and args["player_language"] != "en":
        raise ValueError("PlayerLanguage fr requires PackageLayout player")
    if args["adapter"] in ("ModelLabV2", "OriginalArenaV1"):
        supported = ("Plan", "Materialize", "Bind") if args["adapter"] == "OriginalArenaV1" else ("Materialize", "Bind")
        if args["action"] not in supported:
            raise ValueError(args["adapter"] + " supports only " + ", ".join(supported) + "; no Build adapter is invoked")
        if args["recipient_proof"] or args["recipient_root"] or args["gsc_audit_evidence"]:
            raise ValueError(args["adapter"] + " uses explicit composition.json source/GSC review bindings; recipient/audit adapters are not supported")
        if not args["client_source"] or not args["server_source"] or args["protocol"] != 2 or args["target"] != "stock":
            raise ValueError(args["adapter"] + " requires explicit ClientSource/ServerSource assertions, Protocol 2 and Target stock")
    if args["action"] == "Bind":
        if (args["adapter"] not in ("ModelLabV2", "OriginalArenaV1") or not args["model_source_root"] or not args["review_reference"] or
                not args["build_root"] or args["build_parameters"] or args["output"] or args["finalize_root"]):
            raise ValueError("Bind requires ModelLabV2 or OriginalArenaV1, ModelSourceRoot, BuildRoot and ReviewReference; no output/build command is accepted")
    elif args["adapter"] == "OriginalArenaV1" and args["action"] == "Plan":
        if not args["model_source_root"] or any(args[key] for key in (
                "review_reference", "build_parameters", "build_root", "output", "finalize_root")):
            raise ValueError("OriginalArenaV1 Plan requires only explicit ModelSourceRoot; build and output inputs are refused")
    elif args["model_source_root"] or args["review_reference"]:
        raise ValueError("ModelSourceRoot and ReviewReference require model Bind, or OriginalArenaV1 Plan with ModelSourceRoot only")
    if args["action"] == "Package":
        if args["adapter"] != "None" or any(args[key] for key in (
                "build_parameters", "build_root", "finalize_root", "recipient_proof", "recipient_root", "gsc_audit_evidence")):
            raise ValueError("Package requires Adapter None and an existing project; build/materialization/evidence-adapter inputs are not accepted")
        if not args["output"] or not args["client_source"] or not args["server_source"] or args["protocol"] is None:
            raise ValueError("Package requires Output, ClientSource, ServerSource and Protocol explicitly; these are operator assertions")
    if args["build_root"] and args["action"] not in ("Materialize", "Bind"):
        raise ValueError("BuildRoot is reserved for explicit Materialize or Bind; Plan and Build are unchanged")
    if args["action"] == "Materialize":
        if args["adapter"] not in ("BeaconV1", "BeaconSelfContainedV1", "ModelLabV2", "OriginalArenaV1") or not args["build_root"] or not args["finalize_root"]:
            raise ValueError("Materialize requires BeaconV1, BeaconSelfContainedV1, ModelLabV2 or OriginalArenaV1, an existing BuildRoot and a fresh FinalizeRoot")
        if args["build_parameters"] or args["output"]:
            raise ValueError("Materialize does not accept BuildParameters or Output; it creates a local candidate only")
    if args["gsc_audit_evidence"] and (args["adapter"] != "BeaconSelfContainedV1" or args["action"] != "Plan"):
        raise ValueError("GscAuditEvidence requires explicit BeaconSelfContainedV1 Plan; it never authorizes Build")
    root = Path(args["tools_root"]).resolve(strict=True)
    sdk = module(root / "sdk/modding/manifest.py", "creator_sdk")
    packager = module(root / "ops/modding/Package-CommunityMod.py", "creator_packager")
    if len(args["active_projects"]) > 64:
        raise ValueError("At most 64 active projects can be inspected")
    # Reject redirects before canonicalizing Windows 8.3 aliases. Otherwise an
    # existing path can compare unequal to itself across Python/PowerShell.
    project = packager.no_redirects(args["project"]).resolve(strict=True)
    if not project.is_dir():
        raise ValueError("Project must be a directory; generic planning requires manifest.json")
    report["project"] = str(project)
    projects = [project, *(packager.no_redirects(p).resolve(strict=True) for p in args["active_projects"])]
    manifests = []
    for index, directory in enumerate(projects):
        if index == 0 and args["adapter"] == "BeaconSelfContainedV1":
            selector = module(root / "sdk/modding/creator_self_contained.py", "creator_self_contained")
            data, selection = selector.select(directory, root, packager)
            if args["action"] == "Materialize":
                composition = module(root / "sdk/modding/creator_composition.py", "creator_composition")
                data = composition.plan_contract(data)
            report["source_selection"] = selection
            report["pending"].extend(selection["pending"])
            step("source-selection", "passed", ["Exact separate source selected; proposed contract remains unbuilt and incomplete"])
        else:
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
    if args["action"] == "Package":
        destination = Path(os.path.abspath(args["output"]))
        destination = packager.no_redirects(destination.parent).resolve(strict=True) / destination.name
        if os.path.lexists(destination):
            raise ValueError("Package requires a fresh Output; existing output is preserved")
        if any(destination == directory or destination in directory.parents or directory in destination.parents for directory in projects):
            raise ValueError("Package Output must be outside all input projects")
        report["output"] = str(destination)
        step("package-preflight", "passed", ["Existing project and fresh archive path selected; package gate must still check bytes and closure"])
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
        if args["action"] == "Materialize":
            step("adapter-plan", "not-run", ["Existing build selected; no builder or native planning command is invoked"])
        elif args["build_parameters"]:
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
    elif args["adapter"] == "BeaconSelfContainedV1":
        if args["build_parameters"] or args["recipient_proof"] or args["recipient_root"] or args["output"] or (args["finalize_root"] and args["action"] == "Plan"):
            if args["action"] == "Materialize":
                raise ValueError("Composition refuses BuildParameters, Output and legacy RecipientProof/Root; evidence belongs in composition.json")
            raise ValueError("BeaconSelfContainedV1 accepts source-only Plan selection; build/output/recipient inputs cannot qualify this adapter")
        if args["action"] == "Build":
            raise ValueError("BeaconSelfContainedV1 Build is not connected or qualified; no builder, compiler, finalizer or package writer was invoked")
        if args["gsc_audit_evidence"]:
            evidence_path = packager.no_redirects(args["gsc_audit_evidence"])
            evidence_bytes = selector.snapshot(evidence_path, packager, 1024 * 1024)
            audit = module(root / "sdk/modding/creator_gsc_audit.py", "creator_gsc_audit")
            report["gsc_audit"] = audit.inspect(project, root, selector.json_snapshot(evidence_bytes), packager)
            if selector.snapshot(evidence_path, packager, 1024 * 1024) != evidence_bytes:
                raise ValueError("GscAuditEvidence changed during inspection")
            report["gsc_audit_evidence_sha256"] = hashlib.sha256(evidence_bytes).hexdigest()
            report["pending"].extend(report["gsc_audit"]["unresolved_qualifications"])
            step("gsc-audit-records", "passed", ["Pinned source/container/witness bytes linked; historical completion status reported separately",
                 "Import absence, variant finalization and recipient closure remain unqualified"])
        if args["action"] == "Materialize":
            step("adapter-plan", "not-run", ["Explicit composition.json joins reviewed source to retained assets; no builder invoked"])
        else:
            step("adapter-plan", "pending", ["Source-only planning contract selected; native adapter and complete evidence remain required"])
    elif args["adapter"] == "ModelLabV2":
        step("adapter-plan", "not-run", ["Retained ModelLab v2 source/build and reviewed GSC declarations only; no builder invoked"])
    elif args["adapter"] == "OriginalArenaV1":
        if args["action"] == "Plan":
            local = module(root / "sdk/modding/creator_model_materialize.py", "creator_model_materialize")
            report["source_selection"] = local.select_arena(args["model_source_root"], root, manifest=data)
            report["pending"].extend(report["source_selection"]["pending"])
            step("source-selection", "passed", ["Exact authored arena source rechecked; no build, FF or stock input read"])
        else:
            step("adapter-plan", "not-run", ["Retained original arena source/build and reviewed GSC declarations only; no builder invoked"])
    elif args["adapter"] != "None":
        message = args["adapter"] + " adapter is named but not connected or qualified in Creator"
        step("adapter-plan", "blocked", [message])
        report["errors"].append(message)
    elif args["build_parameters"]:
        raise ValueError("BuildParameters requires an explicit supported adapter")
    else:
        step("adapter-plan", "not-requested", ["Contract planning only; no build adapter selected"])
    if args["action"] == "Bind" and not report["errors"]:
        local = module(root / "sdk/modding/creator_model_materialize.py", "creator_model_materialize")
        bound = local.bind(project, args["model_source_root"], args["build_root"], root,
                           manifest=data, review_reference=args["review_reference"], adapter=args["adapter"])
        report.update(bindings_written=True, composition_binding=bound)
        report["pending"].extend(bound["pending"])
        step("bind", "passed", ["Stable authored inputs bound in " + bound["composition_path"], *bound["pending"]])
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
        fresh = [packager.no_redirects(path.parent).resolve(strict=True) / path.name for path in fresh]
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
    if args["action"] == "Materialize":
        build_root = packager.no_redirects(args["build_root"])
        if not build_root.is_dir():
            raise ValueError("Materialize BuildRoot must be an existing directory")
        destination = Path(os.path.abspath(args["finalize_root"]))
        packager.no_redirects(destination.parent)
        if os.path.lexists(destination):
            raise ValueError("Materialize requires a fresh destination; existing output is preserved")
        for directory in [*projects, build_root]:
            if destination == directory or destination in directory.parents or directory in destination.parents:
                raise ValueError("Materialize destination must be separate from all projects and the retained build")
        if bool(args["recipient_proof"]) != bool(args["recipient_root"]):
            raise ValueError("RecipientProof and RecipientRoot must be supplied together")
        if args["recipient_proof"]:
            if not packager.no_redirects(args["recipient_proof"]).is_file() or not packager.no_redirects(args["recipient_root"]).is_dir():
                raise ValueError("Recipient proof file and root must exist without redirects")
        report.update(build_root=str(build_root), finalize_root=str(destination))
        if not report["errors"]:
            if args["adapter"] in ("ModelLabV2", "OriginalArenaV1"):
                local = module(root / "sdk/modding/creator_model_materialize.py", "creator_model_materialize")
                final = local.materialize(project, build_root, destination, root, manifest=data,
                    client_source=args["client_source"], server_source=args["server_source"], adapter=args["adapter"])
            elif args["adapter"] == "BeaconSelfContainedV1":
                final = composition.materialize(project, build_root, destination, root,
                    client_source=args["client_source"], server_source=args["server_source"])
            else:
                local = module(root / "sdk/modding/creator_materialize.py", "creator_materialize")
                final = local.materialize(project, build_root, destination, root, client_source=args["client_source"],
                    server_source=args["server_source"], recipient_proof=Path(args["recipient_proof"]) if args["recipient_proof"] else None,
                    recipient_root=Path(args["recipient_root"]) if args["recipient_root"] else None)
            report["finalization"] = final
            report.update(build_verified=True, materialized=True)
            source_pending = selection["pending"] if args["adapter"] == "BeaconSelfContainedV1" else []
            report["source_project_pending"] = [item for item in report["pending"] if item.startswith("project-contract:") or item in source_pending]
            report["pending"] = [item for item in report["pending"] if item not in report["source_project_pending"]] + final["blockers"]
            step("materialize", "passed", ["Local candidate created: " + final["candidate_root"], *final["blockers"]])
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
            Invoke-CreatorPackage $final.manifest_path $final.candidate_root $report
        } catch {
            $report.errors+=@($_.Exception.Message)
            $report.steps+=@{name=$phase;status='blocked';details=@($_.Exception.Message)}
        }
    } else {
        $report.steps+=@{name='build';status='blocked';details=@('Preflight failed; no native builder invoked')}
    }
} else {
    $detail=if($Action -ceq 'Materialize'){'Retained build only; no new build was invoked'}elseif($Action -ceq 'Bind'){'Composition inputs bound only; no build or materialization was invoked'}elseif($Action -ceq 'Package'){'Existing project only; no build or materialization was invoked'}else{'Plan does not compile, finalize or package'}
    $report.steps+=@{name='build';status='not-run';details=@($detail)}
}
if($Action -ceq 'Package'){
    if($report.plan_valid){
        try{Invoke-CreatorPackage (Join-Path $report.project 'manifest.json') $report.project $report}
        catch{$report.errors+=@($_.Exception.Message);$report.steps+=@{name='package';status='blocked';details=@($_.Exception.Message)}}
    }else{$report.steps+=@{name='package';status='blocked';details=@('Project preflight failed; ZIP writer not invoked')}}
}
if(!@($report.steps|Where-Object name -EQ 'package').Count){$report.steps+=@{name='package';status='not-run';details=@('No ZIP created; static plan validity is not build or runtime acceptance')}}
if($Json){$report|ConvertTo-Json -Depth 20}
else {
    foreach($step in $report.steps){Write-Output ('[{0}] {1}' -f $step.status,$step.name);foreach($detail in $step.details){Write-Output ('  '+$detail)}}
    Write-Output ('Plan valid: {0}; build executed: {1}; build verified: {2}; materialized: {3}; packaged: {4}; runtime accepted: false' -f $report.plan_valid,$report.build_executed,$report.build_verified,$report.materialized,$report.packaged)
}
if(!$report.plan_valid -or $report.errors.Count -or ($Action -cin @('Build','Package') -and !$report.packaged) -or ($Action -ceq 'Materialize' -and !$report.materialized) -or ($Action -ceq 'Bind' -and !$report.bindings_written)){exit 1}
