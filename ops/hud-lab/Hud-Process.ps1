# Caller owns one Extract lease including bounded diagnostics. No live debugger attach.
function Invoke-HudBuildProcess([string]$Work,[string]$RunRoot,[string]$LeaseToken,$CleanupState,[string]$Cdb,[string]$Symbols,[ValidateSet('hud-build','hud-offline','hud-roundtrip')][string]$Phase='hud-build',[string[]]$ToolArguments=@('-headless','-unbuffered-io','-buildzone','paris_lab_hud')) {
    $exe=Join-Path $Work 'zonetool.exe'
    $sha=(Get-FileHash -LiteralPath $exe).Hash
    $desktop='IW7ParisLab_'+[guid]::NewGuid().ToString('N')
    $quoted=@(foreach($argument in $ToolArguments){if(!$argument -or $argument -match '["\x00-\x1f]' -or $argument.EndsWith('\')){throw 'Unsupported HUD tool argument.'};'"'+$argument+'"'})
    $stem=Join-Path $RunRoot ($Phase+'-'+[datetime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N'))
    $stdout=$stem+'.stdout.log';$stderr=$stem+'.stderr.log'
    $owned=$null;$clock=[Diagnostics.Stopwatch]::StartNew();$identity=$null;$nextDialogCheck=0
    try {
        $owned=[IW7LabProcess]::StartOwned($exe,($quoted -join ' '),$Work,$stdout,$stderr,$desktop,$false)
        $CleanupState.Confirmed=$false
        if (!$owned.HasExited) {
            Add-IW7ResourceProcess -Token $LeaseToken -ProcessId $owned.Id
            $p=Get-CimInstance Win32_Process -Filter "ProcessId=$($owned.Id)"
            if (!$p -or $p.ExecutablePath -ine $exe) { throw 'HUD child identity unavailable; refuse diagnostics.' }
            $identity=[pscustomobject]@{PID=$owned.Id;Image=$exe;CreatedUtc=$p.CreationDate.ToUniversalTime().ToString('o');SHA256=$sha;DesktopName=$desktop}
        }
        while (!$owned.HasExited) {
            if ($clock.Elapsed.TotalSeconds -ge 240) { throw 'HUD build exceeded 240 seconds after completed bootstrap.' }
            $fatal=$false;$dialog='';$dialogError=$null
            if ($clock.Elapsed.TotalSeconds -ge $nextDialogCheck) {
                $nextDialogCheck=$clock.Elapsed.TotalSeconds+1
                try{$dialog=Read-IW7AgentFatalDialog $identity;$fatal=$dialog -match '(?m)^Fatal Error\r?$'}catch{$dialogError=$_.Exception.Message}
            }
            if (($clock.Elapsed.TotalSeconds -ge 45 -and !([string](Get-Content -LiteralPath $stdout -Raw)).Contains('ZoneTool initialization complete!')) -or $fatal) {
                $report=[ordered]@{Schema='iw7.hud-stall/1';Identity=$identity;TriggerSeconds=45;Dump=$stem+'.dmp';Dialog=$stem+'.dialog.txt';Stack=$stem+'.stack.txt';SymbolsVerified=$false;Limits='Live snapshot, not fatal crash proof; no debugger attaches to a live PID. Requested symbol directory is not PDB GUID/age matching proof; raw stacks remain unverified.'}
                $report.Phase=$Phase;$report.FatalDialogObserved=$fatal;$report.TriggerSeconds=$clock.Elapsed.TotalSeconds
                try { if(!$dialog){$dialog=Read-IW7AgentFatalDialog $identity};[IO.File]::WriteAllText($report.Dialog,$dialog) }
                catch { $report.DialogError=$_.Exception.Message }
                $diagnosticCleanup=[pscustomobject]@{Confirmed=$true}
                try {
                    if ($owned.HasExited) { throw 'HUD process exited before snapshot.' }
                    $python=(Get-Command python).Source
                    $capture=Invoke-IW7LabAssetProcess -Executable $python -ToolArguments @((Join-Path $ops 'iw7_capture.py'),'--pid',"$($owned.Id)",'--image',$exe,'--created',$identity.CreatedUtc,'--sha256',$sha,'--snapshot','--scenario','hud-bootstrap-stall','--output',$report.Dump) -WorkingDirectory $Work -LogDirectory $RunRoot -Phase hud-snapshot -LeaseToken $LeaseToken -CleanupState $diagnosticCleanup -TimeoutSeconds 30
                    $report.Capture=$capture
                    if ($capture.ExitCode) { throw 'HUD snapshot helper failed.' }
                    $stack=Invoke-IW7LabAssetProcess -Executable $Cdb -ToolArguments @('-z',$report.Dump,'-y',$Symbols,'-c','~* kP; lmv; .time; q') -WorkingDirectory $Work -LogDirectory $RunRoot -Phase hud-stack -LeaseToken $LeaseToken -CleanupState $diagnosticCleanup -TimeoutSeconds 30
                    $report.StackResult=$stack
                    Copy-Item -LiteralPath $stack.Stdout -Destination $report.Stack
                    if ($stack.ExitCode) { throw 'Offline CDB failed; raw analysis retained, symbols unverified.' }
                } catch { $report.DiagnosticError=$_.Exception.Message }
                finally {
                    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($stem+'.stall.json') -Encoding utf8
                    if (!$diagnosticCleanup.Confirmed) { $CleanupState | Add-Member NoteProperty DiagnosticExitUnconfirmed $true -Force }
                }
                throw 'HUD bootstrap absent or owned fatal dialog observed; bounded diagnostics retained before termination.'
            }
            $null=$owned.WaitForExit(500)
        }
        [pscustomobject]@{Phase=$Phase;ExitCode=$owned.ExitCode;ProcessId=$owned.Id;Stdout=$stdout;Stderr=$stderr}
    } finally {
        if ($owned) {
            try {
                if (!$owned.HasExited) { $owned.Terminate(3758096387) }
                if (!$owned.WaitForExit(5000)) { throw 'HUD exit unconfirmed; retain reservation and staging.' }
                $CleanupState.Confirmed=!$CleanupState.PSObject.Properties['DiagnosticExitUnconfirmed']
            } finally { $owned.Dispose() }
        }
        $clock.Stop()
    }
}
