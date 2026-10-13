# Optional module for Agent-Lab; no launch or reservation occurs on import.
function Read-IW7HudBuild([string]$RunRoot,[switch]$PreviousVersion) {
    $root=(Resolve-Path -LiteralPath $RunRoot).Path.TrimEnd('\','/')
    $statePath=Resolve-IW7BasePath $root 'state.local.json'
    if ((Get-Item -LiteralPath $statePath).Length -gt 1MB) { throw 'HUD build state exceeds bound.' }
    $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.Schema -cne 'iw7.hud-build/1' -or $state.Status -cne 'OfflineLoaded' -or !$state.Restored -or
        !$state.StockPreserved -or $state.RestorationStatus -cne 'Confirmed' -or $state.RetainedLeaseToken -or
        !$state.FF.InventoryVerified -or $state.FF.Path -cne 'mod.ff' -or
        $state.FF.SHA256 -cnotmatch '^[A-Fa-f0-9]{64}$' -or $state.FF.Bytes -lt 1 -or $state.FF.Bytes -gt 1600 -or
        $state.Build.ExitCode -ne 0 -or $state.OfflineLoad.ExitCode -ne 0 -or $state.Roundtrip.ExitCode -ne 0 -or
        $state.ToolSource -cne 'fab935826c898806855376662a8a03317b3ad8f1') { throw 'Restored, measured HUD build/inventory/roundtrip required.' }
    $path=Resolve-IW7BasePath $root 'mod.ff'
    $stream=[IO.File]::Open($path,'Open','Read','Read')
    try {
        if ($stream.Length -ne $state.FF.Bytes) { throw 'HUD FF size changed.' }
        $bytes=[byte[]]::new([int]$stream.Length);$stream.ReadExactly($bytes)
    } finally { $stream.Dispose() }
    $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if ($hash -cne $state.FF.SHA256.ToUpperInvariant()) { throw 'HUD FF hash changed.' }
    $inventory=Resolve-IW7BasePath $root 'assets.csv'
    if ((Get-Item -LiteralPath $inventory).Length -gt 256 -or
        ([IO.File]::ReadAllLines($inventory) -join "`n") -cne "luafile,ui_scripts/paris_lab_hud/__init__.lua`nrawfile,paris_lab_hud") { throw 'Exact two-asset HUD inventory required.' }
    if ($state.VerificationContext -cnotin @('Bootstrap','Spaceland') -or
        ($state.VerificationContext -ceq 'Bootstrap' -and $state.RecipientOfflineLinked)) { throw 'HUD verification context contradictory.' }
    $offlinePath=[IO.Path]::GetFullPath($state.OfflineLoad.Stdout)
    if ((Split-Path $offlinePath) -ine $root) { throw 'HUD offline evidence must be inside its retained build run.' }
    $offlinePath=Resolve-IW7BasePath $root (Split-Path $offlinePath -Leaf)
    if ((Get-Item -LiteralPath $offlinePath).Length -gt 1MB) { throw 'HUD offline inventory log exceeds bound.' }
    $offline=[IO.File]::ReadAllText($offlinePath)
    $zone=if ($state.VerificationContext -ceq 'Bootstrap') { 'paris_lab_hud' } else { 'cp_zmb' }
    if (!$offline.Contains('Loading zone "'+$zone+'"') -or $offline -match 'could not be found|\[ ERROR \]|\[ FATAL \]') { throw 'HUD offline context evidence absent/failed.' }
    $rows=@(foreach ($line in @($offline -split '\r?\n' | Where-Object { $_ -match 'Loading asset ' })) {
        if ($line -notmatch 'Loading asset "([^"\r\n]+)" of type ([a-z0-9]+)\.$') { throw 'Malformed retained HUD inventory evidence.' }
        $Matches[2]+','+$Matches[1]
    })
    if ($rows.Count -ne 2 -or @($rows | Sort-Object -Unique).Count -ne 2 -or
        'luafile,ui_scripts/paris_lab_hud/__init__.lua' -cnotin $rows -or 'rawfile,paris_lab_hud' -cnotin $rows) { throw 'Retained tool callback inventory differs from minimal HUD.' }
    $luaHash=if ($PreviousVersion) { 'FFDBD352B4126A2EA8EE0FF484CD37AECB3AD8C9CFE80195B2B10505403169B5' } else { '3834479321CD0F170A452F9877510D85759EAC5622B8CE126CA8D87E794F5992' }
    $luaFiles=@((Resolve-IW7BasePath $root 'roundtrip.lua'))
    if (!$PreviousVersion) { $luaFiles+=Join-Path $PSScriptRoot 'ui_scripts/paris_lab_hud/__init__.lua' }
    if ($PreviousVersion -and ($hash -cne 'C6290FDF225C6207B0E6B8BE598FC683603DDF2DA9A114020399224244B096AF' -or $bytes.Length -ne 1356)) { throw 'Cache seed must be the exact measured 0.1.0 FF.' }
    foreach ($lua in $luaFiles) {
        if ((Get-Item -LiteralPath $lua).Length -ne 1575 -or (Get-FileHash -LiteralPath $lua).Hash -cne $luaHash) { throw 'HUD roundtrip/current original source mismatch.' }
    }
    [pscustomobject]@{RunRoot=$root;Bytes=$bytes;SHA256=$hash;Version=$(if($PreviousVersion){'0.1.0'}else{'0.1.1'});VerificationContext=$state.VerificationContext;RecipientOfflineLinked=[bool]$state.RecipientOfflineLinked;Ready=$false}
}

function Assert-IW7HudSeed($Build,$Seed) {
    if (!$Build -or !$Seed -or $Seed.Version -cne '0.1.0' -or $Seed.Bytes.Length -ne 1356 -or
        $Seed.SHA256 -cne 'C6290FDF225C6207B0E6B8BE598FC683603DDF2DA9A114020399224244B096AF' -or
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Seed.Bytes)) -cne $Seed.SHA256 -or
        $Build.SHA256 -eq $Seed.SHA256) { throw 'Exact prior HUD seed and a different new FF hash required.' }
}

function Assert-IW7HudSeedCache([string]$GameRoot,$Seed) {
    $path=Resolve-IW7BasePath $GameRoot 'mods/paris_lab_hud/mod.ff'
    if ((Get-Item -LiteralPath $path).Length -ne $Seed.Bytes.Length -or (Get-FileHash -LiteralPath $path).Hash -cne $Seed.SHA256) { throw 'Staged prior HUD cache changed before client launch.' }
}

function Assert-IW7HudNative($Manifest) {
    if ($Manifest.Upstream -cne '77e6d4d24e918ee363b3feee3735c3b889dff7d7') { throw 'HUD runtime requires the reviewed native LuaFile pin.' }
}

function Get-IW7HudProfilePaths([string]$Root) {
    $cache='mods/paris_lab_hud'
    $path=Resolve-IW7BasePath $Root $cache
    if (Test-Path -LiteralPath $path) {
        $files=@(Get-IW7BaseFiles $Root $cache)
        $dirs=@(Get-ChildItem -LiteralPath $path -Directory -Recurse -Force)
        if ($dirs.Count -or $files.Count -gt 1 -or ($files.Count -and $files[0] -ine "$cache/mod.ff")) { throw 'HUD cache contains unexpected assets; preserve it.' }
        if ($files.Count -and (Get-Item -LiteralPath (Resolve-IW7BasePath $Root $files[0])).Length -gt 1600) { throw 'Existing HUD cache exceeds 1600-byte module bound.' }
    }
    $paths=@($cache)
    foreach ($parent in @('iw7-mod/ui_scripts','iw7-mod/lab-appdata/cdata/ui_scripts')) {
        $folder=Resolve-IW7BasePath $Root $parent
        $matches=if (Test-Path -LiteralPath $folder) { @(Get-ChildItem -LiteralPath $folder -Force | Where-Object Name -IEQ 'paris_lab_hud') } else { @() }
        if ($matches.Count -gt 1 -or ($matches.Count -and !$matches[0].PSIsContainer)) { throw 'HUD disk shadow identity ambiguous; preserve it.' }
        $relative=if ($matches.Count) { $parent+'/'+$matches[0].Name } else { $parent+'/paris_lab_hud' }
        $files=@(Get-IW7BaseFiles $Root $relative)
        $total=0L;foreach ($file in $files) { $total+=(Get-Item -LiteralPath (Resolve-IW7BasePath $Root $file)).Length }
        if ($total -gt 64KB -or $files.Count -gt 16) { throw 'HUD disk shadow snapshot exceeds bound.' }
        $paths+=$relative
    }
    $paths
}

function Clear-IW7HudProfiles([string]$Root,[string[]]$Paths,$Transaction) {
    $filesToDelete=@()
    foreach ($relative in $Paths) {
        if ($relative -notin $Transaction.ProfileDirectories -or $Transaction.GameRoot -ine $Root) { throw 'HUD mutation absent from verified transaction.' }
        $path=Resolve-IW7BasePath $Root $relative
        foreach ($file in @(Get-IW7BaseFiles $Root $relative)) {
            $entry=@($Transaction.Files | Where-Object Path -IEQ $file)
            if ($entry.Count -ne 1 -or !$entry[0].Existed -or (Get-FileHash -LiteralPath (Resolve-IW7BasePath $Root $file)).Hash -ne $entry[0].SHA256) { throw 'HUD input changed after snapshot.' }
            $filesToDelete+=$file
        }
    }
    # Preflight all scopes before the first deletion. Keep snapshotted empty
    # directories; only remove hash-verified, planned files.
    foreach ($file in $filesToDelete) { Remove-Item -LiteralPath (Resolve-IW7BasePath $Root $file) }
}

function Start-IW7HudHttp($Build,[string]$OutputRoot) {
    if (!('IW7HudHttp' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'HudHttp.cs') }
    [IW7HudHttp]::new($Build.Bytes,$Build.SHA256,(Join-Path $OutputRoot 'hud-http.jsonl'))
}

function Wait-IW7HudRuntimeEvidence($Session,$Build,$Http,[string]$OutputRoot,$Seed=$null) {
    if ($Seed) { Assert-IW7HudSeed $Build $Seed }
    $deadline=[datetime]::UtcNow.AddSeconds(15)
    $loaded='[PARIS_HUD] loaded version=0.1.1; attach pending'
    $attached='[PARIS_HUD] attached version=0.1.1; render witness pending'
    do {
        $null=Update-IW7BaseClient $Session
        Assert-IW7BaseIdentity $Session.Identity
        if (!$Session.Protected -or $Http.Error) { throw 'HUD protection/HTTP continuity unavailable.' }
        $logPath=Resolve-IW7BasePath $Session.OutputRoot 'client.stdout.log'
        if ($logPath -ine $Session.Identity.Stdout -or (Get-Item -LiteralPath $logPath).Length -gt 8MB) { throw 'HUD stdout is not this bounded owned launch.' }
        $text=Read-IW7BaseLog $logPath
        if ($text.Contains($loaded) -and $text.Contains($attached) -and $Http.CompletedGets -gt 0) { break }
        Start-Sleep -Milliseconds 250
    } while ([datetime]::UtcNow -lt $deadline)
    if (!$text.Contains($loaded) -or !$text.Contains($attached) -or $Http.CompletedGets -lt 1) { throw 'Owned HUD Lua startup/attachment and fresh HTTP GET evidence absent.' }
    $cache=Resolve-IW7BasePath $Session.Plan.GameRoot 'mods/paris_lab_hud/mod.ff'
    $cacheInfo=Get-Item -LiteralPath $cache
    if ($cacheInfo.Length -ne $Build.Bytes.Length -or (Get-FileHash -LiteralPath $cache).Hash -ne $Build.SHA256 -or
        $cacheInfo.LastWriteTimeUtc -lt $Session.StartedUtc.AddMilliseconds(-50) -or
        $cacheInfo.LastWriteTimeUtc -gt [datetime]::UtcNow.AddMilliseconds(50)) { throw 'Downloaded client HUD FF is not fresh or its hash/size differs.' }
    $journal=Resolve-IW7BasePath $OutputRoot 'hud-http.jsonl'
    if ((Get-Item -LiteralPath $journal).Length -gt 32KB) { throw 'HUD GET journal exceeds bounded service contract.' }
    $freshGets=@(foreach ($line in [IO.File]::ReadAllLines($journal)) {
        if (!$line) { continue }
        $row=$line | ConvertFrom-Json
        $utc=([datetimeoffset]$row.utc).UtcDateTime
        if ($row.method -cne 'GET' -or $row.path -cne '/mods/paris_lab_hud/mod.ff' -or $row.bytes -ne $Build.Bytes.Length -or
            $row.sha256 -cne $Build.SHA256) { throw 'HUD GET journal route/octet/hash mismatch.' }
        if ($utc -ge $Session.StartedUtc -and $utc -le [datetime]::UtcNow) { $row }
    })
    if (!$freshGets.Count) { throw 'HUD GET did not follow this owned client launch.' }
    [ordered]@{Schema='iw7.hud-runtime/1';PID=$Session.Identity.PID;CreatedUtc=$Session.Identity.CreatedUtc;NativeSHA256=$Session.Identity.SHA256;
        Stdout=$logPath;BuildRun=$Build.RunRoot;FFSHA256=$Build.SHA256;FFBytes=$Build.Bytes.Length;
        CacheMode=$(if($Seed){'seeded-hash-update'}else{'fresh-empty'});FreshCacheVerified=(!$Seed);UpdatedCacheVerified=[bool]$Seed;
        SeedFFSHA256=$(if($Seed){$Seed.SHA256}else{$null});SeedBuildRun=$(if($Seed){$Seed.RunRoot}else{$null});
        CompletedHttpGets=$Http.CompletedGets;GetsAfterClientLaunch=$freshGets.Count;HttpRequesterPID='unmeasured';CacheModifiedUtc=$cacheInfo.LastWriteTimeUtc.ToString('o');
        LuaLoaded=$true;LuaAttached=$true;VerificationContext=$Build.VerificationContext;
        PixelsVerified=$false;GameplayVerified=$false;OwnerAcceptance=$false;Ready=$false} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputRoot 'hud-runtime.local.json')
}
