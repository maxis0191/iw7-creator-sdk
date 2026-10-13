# Mocked integration only: no binary reads, native types, processes or admission.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot '../asset-bridge/h1-fixture/H1Native.Core.ps1')
. (Join-Path $PSScriptRoot 'SpawnTip.Profile.ps1')
$passed=0
function Check([bool]$Value,[string]$Reason){if(!$Value){throw $Reason};$script:passed++}
$root=Join-Path ([IO.Path]::GetTempPath()) ('spawn-tip-source-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root)|Out-Null
$script:SpawnTipPins=@{
    Python=[pscustomobject]@{Path='C:\synthetic\python.exe';SHA256=('a'*64)};
    JobAssembly=[pscustomobject]@{Path='C:\synthetic\job.dll'};
    Phase=[pscustomobject]@{Path='C:\synthetic\phase.py'}}
$script:SpawnTipPlanPath='C:\synthetic\plan.json'
function Enter-IW7ResourceLease($Scope,$Kind,$PhysicalBytes,$CommitBytes,$Owner) {
    $script:events.Add('admission')
    Check ($Kind -ceq 'Build' -and $PhysicalBytes -eq 4GB -and $CommitBytes -eq 6GB) 'Admission budget reduced.'
    if($script:scenario -ceq 'busy'){throw 'synthetic occupied lease'}
    [pscustomobject]@{Token=('d'*32);Scope=$Scope;Kind=$Kind}
}
function Exit-IW7ResourceLease($Token){$script:events.Add('release');if($script:scenario -ceq 'release-failure'){throw 'synthetic release failure'}}
function Get-H1Clock {$script:clock}
function Open-H1Pin($Pin){$script:events.Add('guard');if($script:scenario -ceq 'pin-failure'){throw 'synthetic mismatched pin'};return [IO.MemoryStream]::new()}
function Initialize-SpawnTipOwner($Path){$script:events.Add('load');if($script:scenario -ceq 'load-failure'){throw 'synthetic load failure'}}
function Test-H1Budget($Plan,$State){$script:events.Add('budget');if($script:scenario -ceq 'output-cap'){throw 'synthetic output cap'}}
function Read-H1SmallJson($Path,$Limit){[pscustomobject]@{Schema='synthetic only'}}
function Assert-SpawnTipChild($Report,$Plan,$Hash,$State,$Context){$script:events.Add('validate');if($script:scenario -ceq 'child-failure'){throw 'synthetic invalid witness'}}
function Write-H1Receipt($Plan,$State,$StageRoot){$script:events.Add('receipt');if($script:scenario -ceq 'receipt-failure'){throw 'synthetic receipt cap'}}
function Invoke-H1OwnedStage($Plan,$State,$Context,$Start,$Hash,$StageRoot,$Started) {
    $script:events.Add('start')
    Check ($State.Stage -ceq 'GscAudit' -and $State.DeadlineSeconds -eq 180) 'Must not enter native compiler telemetry profile.'
    Check ($Start.ArgumentList[0] -ceq '-I' -and $Start.ArgumentList[1] -ceq '-B' -and $Start.CreateNoWindow) 'Python launch isolation differs.'
    $Context.Closed=$false
    $Context.Owner=[pscustomobject]@{Closed=$false;ExitCode=0;Stops=0;StopFails=($script:scenario -ceq 'unknown-closure')}
    $Context.Owner|Add-Member ScriptMethod StopAndConfirm {param($ms)
        $this.Stops++;if($ms -ne 5000){throw 'wrong cleanup deadline'}
        if($this.StopFails){throw 'synthetic unknown job membership'};$this.Closed=$true;$this.ExitCode=19
    }
    if($script:scenario -cin @('phase-failure','unknown-closure')){throw 'synthetic child failed'}
    $Context.Closed=$true;$Context.Owner.Closed=$true;$State.ExitCode=0
    [IO.File]::WriteAllText((Join-Path $StageRoot 'child.json'),'{}')
    if($script:scenario -ceq 'late'){$script:clock=180001}
}
try {
    foreach($scenario in 'success','busy','pin-failure','load-failure','phase-failure','unknown-closure','child-failure','output-cap','late','release-failure','receipt-failure') {
        $script:scenario=$scenario;$script:clock=0;$script:events=[Collections.Generic.List[string]]::new()
        $plan=[pscustomobject]@{RunRoot=(Join-Path $root $scenario);Bindings=@([pscustomobject]@{IsText=$false})}
        $guards=[Collections.Generic.List[object]]::new();$guard=[IO.MemoryStream]::new();$guards.Add($guard)
        $result=Invoke-SpawnTipRun $plan ('c'*64) $guards
        Check (!$result.State.RuntimeValidated -and !$result.State.PackageReady -and !$result.State.OwnerAccepted) 'Offline run overclaims runtime/package.'
        Check ($events[0] -ceq 'admission') 'Binary reads preceded admission.'
        if($scenario -ceq 'success') {
            Check ($result.State.Status -ceq 'OfflineReferencesQualified' -and $result.State.EncodedReferenceAbsence) 'Successful synthetic flow failed.'
            Check (($events.IndexOf('validate') -lt $events.IndexOf('release')) -and ($events.IndexOf('release') -lt $events.IndexOf('receipt'))) 'Validation/release/publication ordering differs.'
            Check ($result.State.TreeClosureConfirmed -and $result.State.LeaseReleased -and !$guard.CanRead) 'Closed success retained guards/lease.'
        }elseif($scenario -cin @('unknown-closure','release-failure')) {
            Check ($result.State.Quarantined -and !$result.State.LeaseReleased -and $guard.CanRead) 'Uncertain closure/admission lost guards.'
            Check ([object]::ReferenceEquals([AppDomain]::CurrentDomain.GetData('IW7.SpawnTip.Active'),$result.Context)) 'Original quarantine context became unreachable.'
            if($scenario -ceq 'unknown-closure'){Check (!$events.Contains('release') -and $result.Context.Owner.Stops -eq 1) 'Unknown job incorrectly released.'}
            # Dispose only this fake context; no real lease or native handle exists.
            foreach($g in $guards){$g.Dispose()};$guards.Clear()
            [AppDomain]::CurrentDomain.SetData(('IW7.H1.Quarantine.'+$result.State.LeaseToken),$null)
            [AppDomain]::CurrentDomain.SetData('IW7.SpawnTip.Active',$null)
        }else {
            Check ($result.State.Status -ceq 'Failed' -and $result.Failure) 'Failure promoted to success.'
            Check (!$guard.CanRead) 'Confirmed no-job/closed-job failure retained guards.'
            if($scenario -ceq 'busy'){Check (!$events.Contains('guard') -and !$events.Contains('start') -and !(Test-Path -LiteralPath $plan.RunRoot)) 'Admission refusal read binaries or wrote output.'}
            else {Check $result.State.LeaseReleased 'Closed failure did not release admission.'}
            if($scenario -ceq 'phase-failure'){Check ($result.Context.Owner.Stops -eq 1 -and $result.State.TerminationRequested -and !$result.State.EncodedReferenceAbsence) 'Owned cleanup rewrote failed execution.'}
        }
    }
    [ordered]@{Schema='iw7.spawn-tip-source-tests/1';Assertions=$passed;NativeTypesLoaded=$false;BinaryInputsRead=$false;LeaseAcquired=$false}|ConvertTo-Json
}finally {
    $resolved=[IO.Path]::GetFullPath($root)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($resolved) -notlike 'spawn-tip-source-*'){throw 'Unsafe synthetic cleanup path'}
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
