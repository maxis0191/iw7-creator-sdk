"""Asset-free staging and readiness regressions; no Lua/engine/render acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import subprocess
import uuid
import os
import threading
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load('hud_prepare', 'ops/hud-lab/prepare.py')
validator = load('hud_validator', 'ops/Validate-ModPackage.py')
http = load('hud_http', 'ops/hud-lab/serve.py')


class HudLabTests(unittest.TestCase):
    def run_powershell_fixture(self, source):
        if not shutil.which('pwsh'):
            self.skipTest('PowerShell 7 required')
        # Runtime callers pass canonical installation paths. Hosted Windows TEMP
        # may contain an 8.3 user alias; do not feed that unnormalised alias into
        # fixtures that compare file identities and relative profile paths.
        (ROOT / 'runtime').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'runtime') as temporary:
            folder = str(Path(temporary).resolve())
            script = Path(folder) / 'fixture.ps1'
            script.write_text('param($Repo,$Fixture)\n$ErrorActionPreference="Stop"\n' + source, encoding='utf-8')
            result = subprocess.run(['pwsh', '-NoProfile', '-File', str(script), str(ROOT), folder],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_inprocess_http_exact_bytes_routes_budget_and_blocked_reader_disposal(self):
        self.run_powershell_fixture(r'''
Add-Type -Path (Join-Path $Repo 'ops/hud-lab/HudHttp.cs')
$bytes=[Text.Encoding]::UTF8.GetBytes('synthetic transport fixture; not a fastfile')
$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
$log=Join-Path $Fixture 'gets.jsonl'
foreach($bad in @([byte[]]::new(0),[byte[]]::new(1601))){
    $failed=$false;try{$null=[IW7HudHttp]::new($bad,$sha,$log)}catch{$failed=$true}
    if(!$failed -or (Test-Path $log)){throw 'Invalid size allocated a service/journal'}
}
$service=[IW7HudHttp]::new($bytes,$sha,$log)
$client=[Net.Http.HttpClient]::new()
try {
    $bytes[0]=0 # service owns an immutable clone
    foreach($path in @('/','/mods/paris_lab_hud/mod.ff?x=1','/mods/paris_beta/bank/a','/mods/paris_lab_hud/mod.ff/')){
        $r=$client.GetAsync($service.BaseUrl+$path).GetAwaiter().GetResult()
        try{if([int]$r.StatusCode -ne 404){throw 'Unexpected HTTP route admitted'}}finally{$r.Dispose()}
    }
    $r=$client.GetAsync($service.BaseUrl+[IW7HudHttp]::Route).GetAwaiter().GetResult()
    try{
        $received=$r.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
        if([int]$r.StatusCode -ne 200 -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($received)) -cne $sha){throw 'HTTP immutable bytes differ'}
    }finally{$r.Dispose()}
    $deadline=[datetime]::UtcNow.AddSeconds(2)
    while($service.CompletedGets -lt 1 -and [datetime]::UtcNow -lt $deadline){Start-Sleep -Milliseconds 10}
    $row=Get-Content $log -Raw | ConvertFrom-Json
    if($service.CompletedGets -ne 1 -or $row.path -cne [IW7HudHttp]::Route -or $row.sha256 -cne $sha -or $row.bytes -ne $received.Length){throw 'GET journal mismatch'}
    # Disposal must interrupt an incomplete read, rather than wait for its peer.
    $tcp=[Net.Sockets.TcpClient]::new('127.0.0.1',([uri]$service.BaseUrl).Port)
    $partial=[Text.Encoding]::ASCII.GetBytes('GET ')
    $tcp.GetStream().Write($partial,0,$partial.Length)
    Start-Sleep -Milliseconds 50
    $watch=[Diagnostics.Stopwatch]::StartNew();$service.Dispose()
    $tcp.Dispose()
    if(!$service.Stopped -or $watch.ElapsedMilliseconds -gt 5500 -or $service.Error){throw 'HTTP worker closure unconfirmed'}
}finally{$service.Dispose();$client.Dispose()}
''')

    def test_real_profile_transactions_preserve_cache_shadows_and_refuse_unplanned_content(self):
        self.run_powershell_fixture(r'''
. (Join-Path $Repo 'ops/Base-Client.Core.ps1')
. (Join-Path $Repo 'ops/hud-lab/Hud-Runtime.Core.ps1')
$root=Join-Path $Fixture 'game';[IO.Directory]::CreateDirectory($root)|Out-Null
$original=@{'mods/paris_lab_hud/mod.ff'='old synthetic cache';'iw7-mod/ui_scripts/PARIS_LAB_HUD/__init__.lua'='old shadow';'iw7-mod/lab-appdata/cdata/ui_scripts/paris_lab_hud/__init__.lua'='cdata shadow'}
foreach($key in $original.Keys){$p=Join-Path $root $key;[IO.Directory]::CreateDirectory((Split-Path $p))|Out-Null;[IO.File]::WriteAllText($p,$original[$key])}
$paths=@(Get-IW7HudProfilePaths $root)
if($paths.Count -ne 3 -or 'iw7-mod/ui_scripts/PARIS_LAB_HUD' -cnotin $paths){throw 'Disk shadow casing not inventoried'}
$plan=[pscustomobject]@{GameRoot=$root;MutableFiles=@();ProfileDirectory='unused';ProfileDirectories=$paths}
$txn=Save-IW7BaseTransaction $plan (Join-Path $Fixture 'backup')
# A source race must refuse clearing before deleting any existing cache.
[IO.File]::WriteAllText((Join-Path $root 'mods/paris_lab_hud/mod.ff'),'changed')
$failed=$false;try{Clear-IW7HudProfiles $root $paths $txn}catch{$failed=$true}
if(!$failed -or !(Test-Path (Join-Path $root 'iw7-mod/ui_scripts/PARIS_LAB_HUD/__init__.lua'))){throw 'Changed cache not preserved'}
[IO.File]::WriteAllText((Join-Path $root 'mods/paris_lab_hud/mod.ff'),$original['mods/paris_lab_hud/mod.ff'])
$late='iw7-mod/lab-appdata/cdata/ui_scripts/paris_lab_hud/__init__.lua'
[IO.File]::WriteAllText((Join-Path $root $late),'changed after snapshot')
$failed=$false;try{Clear-IW7HudProfiles $root $paths $txn}catch{$failed=$true}
if(!$failed -or !(Test-Path (Join-Path $root 'mods/paris_lab_hud/mod.ff'))){throw 'Late-scope race deleted earlier cache'}
[IO.File]::WriteAllText((Join-Path $root $late),$original[$late])
Clear-IW7HudProfiles $root $paths $txn
foreach($key in $original.Keys){if(Test-Path (Join-Path $root $key)){throw 'Managed cache/shadow remained'}}
[IO.File]::WriteAllText((Join-Path $root 'mods/paris_lab_hud/mod.ff'),'new synthetic download')
Restore-IW7BaseTransaction $txn
foreach($key in $original.Keys){if([IO.File]::ReadAllText((Join-Path $root $key)) -cne $original[$key]){throw 'Restored profile differs'}}
[IO.File]::WriteAllText((Join-Path $root 'mods/paris_lab_hud/foreign.ff'),'preserve')
$failed=$false;try{$null=Get-IW7HudProfilePaths $root}catch{$failed=$true};if(!$failed){throw 'Unexpected cache assets admitted'}
Remove-Item -LiteralPath (Join-Path $root 'mods/paris_lab_hud/foreign.ff')
[IO.File]::WriteAllBytes((Join-Path $root 'mods/paris_lab_hud/mod.ff'),[byte[]]::new(1601))
$failed=$false;try{$null=Get-IW7HudProfilePaths $root}catch{$failed=$true};if(!$failed){throw 'Oversized cache admitted'}
''')

    def test_hud_build_gate_rejects_missing_changed_or_extra_evidence_and_never_claims_pixels(self):
        self.run_powershell_fixture(r'''
. (Join-Path $Repo 'ops/Base-Client.Core.ps1')
. (Join-Path $Repo 'ops/hud-lab/Hud-Runtime.Core.ps1')
$bytes=[Text.Encoding]::ASCII.GetBytes('synthetic artifact transport contract only; not a fastfile')
$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
[IO.File]::WriteAllBytes((Join-Path $Fixture 'mod.ff'),$bytes)
Copy-Item -LiteralPath (Join-Path $Repo 'ops/hud-lab/ui_scripts/paris_lab_hud/__init__.lua') -Destination (Join-Path $Fixture 'roundtrip.lua')
$rows="luafile,ui_scripts/paris_lab_hud/__init__.lua`nrawfile,paris_lab_hud`n"
[IO.File]::WriteAllText((Join-Path $Fixture 'assets.csv'),$rows)
$log=Join-Path $Fixture 'offline.log'
[IO.File]::WriteAllText($log,"Loading zone `"paris_lab_hud`"`nLoading asset `"ui_scripts/paris_lab_hud/__init__.lua`" of type luafile.`nLoading asset `"paris_lab_hud`" of type rawfile.`n")
$state=@{Schema='iw7.hud-build/1';Status='OfflineLoaded';Restored=$true;StockPreserved=$true;RestorationStatus='Confirmed';RetainedLeaseToken=$null;VerificationContext='Bootstrap';RecipientOfflineLinked=$false;ToolSource='fab935826c898806855376662a8a03317b3ad8f1';FF=@{Path='mod.ff';Bytes=$bytes.Length;SHA256=$sha;InventoryVerified=$true};Build=@{ExitCode=0};OfflineLoad=@{ExitCode=0;Stdout=$log};Roundtrip=@{ExitCode=0}}
function SaveState{$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Fixture 'state.local.json')}
function Refused{$failed=$false;try{$null=Read-IW7HudBuild $Fixture}catch{$failed=$true};if(!$failed){throw 'Invalid HUD evidence admitted'}}
SaveState
$plan=Read-IW7HudBuild $Fixture;if($plan.Ready -or $plan.RecipientOfflineLinked){throw 'Synthetic contract claimed ready/recipient acceptance'}
$state.RecipientOfflineLinked=$true;SaveState;Refused;$state.RecipientOfflineLinked=$false
$state.Roundtrip.ExitCode=1;SaveState;Refused;$state.Roundtrip.ExitCode=0;SaveState
[IO.File]::WriteAllText((Join-Path $Fixture 'assets.csv'),$rows+'xmodel,extra');Refused
[IO.File]::WriteAllText((Join-Path $Fixture 'assets.csv'),$rows)
[IO.File]::AppendAllText($log,"Loading asset `"foreign`" of type rawfile.`n");Refused
$failed=$false;try{Assert-IW7HudNative ([pscustomobject]@{Upstream=('a'*40)})}catch{$failed=$true};if(!$failed){throw 'Unknown native pin admitted'}
Assert-IW7HudNative ([pscustomobject]@{Upstream='77e6d4d24e918ee363b3feee3735c3b889dff7d7'})
''')

    def test_runtime_startup_evidence_is_owned_fresh_and_keeps_pixels_pending(self):
        # Identity/protection calls are injected; no process is launched. Actual
        # helper IO proves that stale GETs/cache and foreign stdout cannot pass.
        self.run_powershell_fixture(r'''
. (Join-Path $Repo 'ops/Base-Client.Core.ps1')
. (Join-Path $Repo 'ops/hud-lab/Hud-Runtime.Core.ps1')
function Update-IW7BaseClient($s){if(!$s.Protected){throw 'unprotected'};[pscustomobject]@{Protected=$true}}
$script:identityChecks=0
function Assert-IW7BaseIdentity($identity){$script:identityChecks++;if($identity.PID -ne 123){throw 'foreign identity'}}
$game=Join-Path $Fixture 'game';$out=Join-Path $Fixture 'launch'
[IO.Directory]::CreateDirectory((Join-Path $game 'mods/paris_lab_hud'))|Out-Null
[IO.Directory]::CreateDirectory($out)|Out-Null
$bytes=[Text.Encoding]::ASCII.GetBytes('synthetic download; not a fastfile')
$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
$started=[datetime]::UtcNow.AddSeconds(-2)
$stdout=Join-Path $out 'client.stdout.log'
[IO.File]::WriteAllText($stdout,"[PARIS_HUD] loaded version=0.1.1; attach pending`n[PARIS_HUD] attached version=0.1.1; render witness pending`n")
$cache=Join-Path $game 'mods/paris_lab_hud/mod.ff';[IO.File]::WriteAllBytes($cache,$bytes)
$journal=Join-Path $out 'hud-http.jsonl'
$row=@{utc=[datetime]::UtcNow.ToString('o');method='GET';path='/mods/paris_lab_hud/mod.ff';bytes=$bytes.Length;sha256=$sha}
function WriteGet{$row | ConvertTo-Json -Compress | Set-Content -LiteralPath $journal}
WriteGet
$session=[pscustomobject]@{Plan=[pscustomobject]@{GameRoot=$game};OutputRoot=$out;Protected=$true;StartedUtc=$started;Identity=[pscustomobject]@{PID=123;CreatedUtc=$started.ToString('o');SHA256=('A'*64);Stdout=$stdout}}
$build=[pscustomobject]@{Bytes=$bytes;SHA256=$sha;RunRoot='synthetic-contract';VerificationContext='Bootstrap'}
$http=[pscustomobject]@{CompletedGets=1;Error=$null}
Wait-IW7HudRuntimeEvidence $session $build $http $out
$e=Get-Content (Join-Path $out 'hud-runtime.local.json') -Raw | ConvertFrom-Json
if(!$e.FreshCacheVerified -or !$e.LuaAttached -or $e.PixelsVerified -or $e.GameplayVerified -or $e.Ready -or $identityChecks -lt 1){throw 'Evidence claims wrong gate/identity'}
# Inject only the historical-pin gate to exercise seeded evidence attribution
# without shipping the real generated FF in asset-free tests. Its rejection
# policy is covered separately with the unmocked function.
function Assert-IW7HudSeed($Build,$Seed){if($Seed.RunRoot -cne 'synthetic-prior-contract'){throw 'wrong injected seed'}}
$seed=[pscustomobject]@{RunRoot='synthetic-prior-contract';SHA256=('C'*64)}
Wait-IW7HudRuntimeEvidence $session $build $http $out $seed
$e=Get-Content (Join-Path $out 'hud-runtime.local.json') -Raw | ConvertFrom-Json
if($e.FreshCacheVerified -or !$e.UpdatedCacheVerified -or $e.CacheMode -cne 'seeded-hash-update' -or $e.SeedFFSHA256 -cne $seed.SHA256 -or $e.PixelsVerified -or $e.Ready){throw 'Seeded update falsely claimed fresh/pixels/ready'}
function Refused{$failed=$false;try{Wait-IW7HudRuntimeEvidence $session $build $http $out}catch{$failed=$true};if(!$failed){throw 'Stale/foreign runtime evidence admitted'}}
$row.utc=$started.AddSeconds(-1).ToString('o');WriteGet;Refused
$row.utc=[datetime]::UtcNow.ToString('o');WriteGet
[IO.File]::SetLastWriteTimeUtc($cache,$started.AddMinutes(-1));Refused
[IO.File]::SetLastWriteTimeUtc($cache,[datetime]::UtcNow)
$session.Identity.Stdout=Join-Path $Fixture 'foreign.log';Refused
$session.Identity.Stdout=$stdout;$session.Identity.PID=456;Refused
''')

    def test_seed_pin_refusals_and_transactional_cache_guard(self):
        self.run_powershell_fixture(r'''
. (Join-Path $Repo 'ops/Base-Client.Core.ps1')
. (Join-Path $Repo 'ops/hud-lab/Hud-Runtime.Core.ps1')
$pin='C6290FDF225C6207B0E6B8BE598FC683603DDF2DA9A114020399224244B096AF'
$build=[pscustomobject]@{SHA256=('B'*64)}
$seed=[pscustomobject]@{Version='0.1.0';Bytes=[byte[]]::new(1356);SHA256=$pin}
function Refused { $failed=$false;try{Assert-IW7HudSeed $build $seed}catch{$failed=$true};if(!$failed){throw 'Unproven prior seed admitted'} }
Refused # exact declared pin with synthetic bytes must fail the recomputed hash
$seed.Version='0.1.1';Refused;$seed.Version='0.1.0'
$seed.Bytes=[byte[]]::new(1357);Refused;$seed.Bytes=[byte[]]::new(1356)
$seed.SHA256=('A'*64);Refused;$seed.SHA256=$pin
$build.SHA256=$pin;Refused;$build.SHA256=('B'*64)
# Exercise the actual file guard and outer restoration using synthetic bytes.
# This cache guard does not certify the historical seed; AssertSeed does that.
$root=Join-Path $Fixture 'game';$cache=Join-Path $root 'mods/paris_lab_hud/mod.ff'
[IO.Directory]::CreateDirectory((Split-Path $cache))|Out-Null
[IO.File]::WriteAllText($cache,'pre-existing owner cache')
$paths=@(Get-IW7HudProfilePaths $root)
$txn=Save-IW7BaseTransaction ([pscustomobject]@{GameRoot=$root;MutableFiles=@();ProfileDirectory='unused';ProfileDirectories=$paths}) (Join-Path $Fixture 'backup')
Clear-IW7HudProfiles $root $paths $txn
$payload=[Text.Encoding]::ASCII.GetBytes('synthetic prior cache; not a fastfile')
$fixtureSeed=[pscustomobject]@{Bytes=$payload;SHA256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($payload))}
[IO.File]::WriteAllBytes($cache,$payload);Assert-IW7HudSeedCache $root $fixtureSeed
[IO.File]::WriteAllText($cache,'changed before launch')
$failed=$false;try{Assert-IW7HudSeedCache $root $fixtureSeed}catch{$failed=$true};if(!$failed){throw 'Changed staged seed admitted'}
[IO.File]::WriteAllText($cache,'synthetic new download')
Restore-IW7BaseTransaction $txn
if([IO.File]::ReadAllText($cache) -cne 'pre-existing owner cache'){throw 'Seed/update erased original cache'}
''')

    def test_http_snapshot_and_exact_endpoint_expose_only_pinned_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            ff = Path(folder) / 'synthetic.ff'
            payload = b'synthetic transport fixture; not a fastfile'
            ff.write_bytes(payload)
            sha = hashlib.sha256(payload).hexdigest()
            with self.assertRaises(ValueError):
                http.snapshot(ff, '0' * 64)
            snap = http.snapshot(ff, sha)
            ff.write_bytes(b'changed after immutable snapshot')
            log = Path(folder) / 'requests.jsonl'
            server = http.endpoint(snap, log)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                base = 'http://127.0.0.1:' + str(server.server_port)
                with urllib.request.urlopen(base + http.URL_PATH, timeout=5) as response:
                    self.assertEqual(response.read(), payload)
                for path in ('/', '/bank', '/mods/paris_lab_hud/mod.ff?anything=1', '/mods/../bank'):
                    with self.assertRaises(urllib.error.HTTPError) as failure:
                        urllib.request.urlopen(base + path, timeout=5)
                    self.assertEqual(failure.exception.code, 404)
                rows = log.read_text().splitlines()
                self.assertEqual(len(rows), 1)
                self.assertEqual(json.loads(rows[0])['sha256'], sha)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())

    def test_stages_only_original_source_with_exact_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'fresh'
            result = prepare.prepare(target)
            self.assertFalse(result['built'])
            self.assertFalse(result['deployed'])
            actual = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
            self.assertEqual(actual, {'package.plan.json', 'source-provenance.json',
                                     'zone_source/paris_lab_hud.csv',
                                     'zonetool/paris_lab_hud/' + prepare.LUA})
            for entry in result['source_files']:
                payload = (target / entry['path']).read_bytes()
                self.assertEqual(entry['bytes'], len(payload))
                self.assertEqual(entry['sha256'], hashlib.sha256(payload).hexdigest())
            self.assertEqual((target / 'zonetool/paris_lab_hud' / prepare.LUA).read_bytes(),
                             (prepare.HERE / prepare.LUA).read_bytes())

    def test_refuses_existing_directory_preserves_all_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            sentinel = Path(folder) / 'bank'
            sentinel.write_bytes(b'preserve')
            with self.assertRaises(ValueError):
                prepare.prepare(folder)
            self.assertEqual(sentinel.read_bytes(), b'preserve')
            self.assertEqual(list(Path(folder).iterdir()), [sentinel])

    def test_no_links_in_output_ancestry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            real = root / 'real'
            real.mkdir()
            link = root / 'link'
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError as error:
                self.skipTest('Windows symlink privilege unavailable: ' + str(error))
            with self.assertRaises(ValueError):
                prepare.prepare(link / 'fresh')
            self.assertEqual(list(real.iterdir()), [])

    def test_stale_source_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source'
            lua = source / prepare.LUA
            lua.parent.mkdir(parents=True)
            lua.write_bytes(b'changed source')
            for name in ('package.plan.json', 'paris_lab_hud.csv'):
                (source / name).write_bytes((prepare.HERE / name).read_bytes())
            target = Path(folder) / 'output'
            with patch.object(prepare, 'HERE', source):
                with self.assertRaisesRegex(ValueError, 'differs'):
                    prepare.prepare(target)
            self.assertFalse(target.exists())

    def test_manifest_never_ready_without_fastfile_and_evidence(self):
        plan = json.loads((prepare.HERE / 'package.plan.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as folder:
            result = validator.validate(plan, Path(folder), 'plan', 'native',
                                        '77e6d4d24e918ee363b3feee3735c3b889dff7d7', None)
            self.assertTrue(result['valid'], result)
            self.assertFalse(result['ready'])
            for stage in ('package', 'delivery'):
                result = validator.validate(plan, Path(folder), stage, 'native',
                                            '77e6d4d24e918ee363b3feee3735c3b889dff7d7', None)
                self.assertFalse(result['ready'])
                self.assertFalse(result['valid'])
        self.assertEqual(plan['closure']['status'], 'incomplete')
        self.assertTrue(plan['closure']['unresolved'])
        self.assertTrue(all(e['status'] == 'pending' for e in plan['evidence']))

    def test_csv_and_exact_loader_identity(self):
        rows = (prepare.HERE / 'paris_lab_hud.csv').read_text().strip().splitlines()
        self.assertEqual(rows, ['luafile,' + prepare.LUA])
        # PR697 only discovers a single folder between these exact boundaries.
        self.assertTrue(prepare.LUA.startswith('ui_scripts/'))
        self.assertTrue(prepare.LUA.endswith('/__init__.lua'))
        self.assertNotIn('/', prepare.LUA[len('ui_scripts/'):-len('/__init__.lua')])

    @unittest.skipUnless(os.name == 'nt' and shutil.which('pwsh'), 'Windows/PowerShell NTFS transaction fixture')
    def test_actual_verify_log_inventory_rejects_missing_extra_duplicate_and_malformed_rows(self):
        valid = '\n'.join(['Loading zone "cp_zmb"',
                           '[ INFO ]: Loading asset "ui_scripts/paris_lab_hud/__init__.lua" of type luafile.',
                           '[ INFO ]: Loading asset "paris_lab_hud" of type rawfile.'])
        cases = [valid, valid + '\nLoading asset "extra" of type xmodel.',
                 valid + '\nLoading asset "paris_lab_hud" of type rawfile.',
                 valid.replace('Loading zone "cp_zmb"', ''),
                 valid.replace(' of type rawfile.', ' broken'), valid + '\n[ ERROR ] failure']
        with tempfile.TemporaryDirectory() as folder:
            for index, log in enumerate(cases):
                source = Path(folder) / (str(index) + '.txt')
                source.write_text(log)
                command = "$ast=[Management.Automation.Language.Parser]::ParseFile('" + str(ROOT / 'ops/hud-lab/Build-Hud.ps1') + "',[ref]$null,[ref]$null);$node=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-HudVerifiedInventory'},$true);. ([scriptblock]::Create($node.Extent.Text));try{@(Get-HudVerifiedInventory (Get-Content -LiteralPath '" + str(source) + "' -Raw))|ConvertTo-Json -Compress}catch{exit 1}"
                checked = subprocess.run(['pwsh', '-NoProfile', '-Command', command], capture_output=True, text=True, timeout=20)
                if index == 0:
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertEqual(json.loads(checked.stdout), ['luafile,' + prepare.LUA, 'rawfile,paris_lab_hud'])
                else:
                    self.assertNotEqual(checked.returncode, 0)

    @unittest.skipUnless(os.name == 'nt' and shutil.which('pwsh'), 'Windows/PowerShell NTFS transaction fixture')
    def test_prepare_and_rollback_preserve_stock_and_exclude_unrelated_assets(self):
        # Synthetic files test staging only: no executable is ever invoked.
        output = ROOT / 'runtime' / ('hud-test-' + uuid.uuid4().hex)
        try:
            # NTFS hardlinks require the same volume as the staged worktree.
            # Hosted runners commonly place TEMP on C: and the checkout on D:.
            (ROOT / 'runtime').mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir=ROOT / 'runtime') as folder:
                stock = Path(folder)
                for name in ('main/code_pre_gfx.ff', 'main/cp_zmb.ff', 'main/fileSysCheck.cfg', 'zone/code_pre_gfx.ff',
                             'zone/custom_foreign.ff', 'zone/imagefile999.pak', 'zone/assetfile1.pak', 'zone/assetfile17.pak', 'zone/assetfile19.pak', 'zone/assetfile999.pak',
                             'iw7_ship.exe', 'bink2w64.dll', 'steam_api64.dll'):
                    target = stock / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(('synthetic: ' + name).encode())
                before = {p.relative_to(stock): p.read_bytes() for p in stock.rglob('*') if p.is_file()}
                bootstrap = json.loads((ROOT / 'ops/hud-lab/bootstrap-dependencies.json').read_text())
                for dependency in bootstrap['dependencies']:
                    target = stock / dependency['relative']
                    if not target.exists():
                        target.write_bytes(('synthetic: ' + dependency['relative']).encode())
                before = {p.relative_to(stock): p.read_bytes() for p in stock.rglob('*') if p.is_file()}
                pak = stock / 'zone/assetfile1.pak'
                pak.unlink()
                missing_pak = subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'ops/hud-lab/Build-Hud.ps1'),
                                             '-Action', 'Prepare', '-StockToolRoot', str(stock), '-RunRoot', str(output)],
                                            capture_output=True, text=True, timeout=30)
                self.assertNotEqual(missing_pak.returncode, 0)
                self.assertIn('Missing observed bootstrap prerequisite', missing_pak.stderr)
                self.assertFalse(output.exists())
                pak.write_bytes(before[Path('zone/assetfile1.pak')])
                sentinel = stock / 'main/fileSysCheck.cfg'
                sentinel.unlink()
                incomplete = subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'ops/hud-lab/Build-Hud.ps1'),
                                             '-Action', 'Prepare', '-StockToolRoot', str(stock), '-RunRoot', str(output)],
                                            capture_output=True, text=True, timeout=30)
                self.assertNotEqual(incomplete.returncode, 0)
                self.assertIn('Missing filesystem bootstrap sentinel', incomplete.stderr)
                self.assertFalse(output.exists())
                sentinel.write_bytes(before[Path('main/fileSysCheck.cfg')])
                staged = subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'ops/hud-lab/Build-Hud.ps1'),
                                         '-Action', 'Prepare', '-StockToolRoot', str(stock), '-RunRoot', str(output)],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(staged.returncode, 0, staged.stdout + staged.stderr)
                state = json.loads((output / 'state.local.json').read_text(encoding='utf-8-sig'))
                self.assertEqual(state['Status'], 'Prepared')
                self.assertFalse((output / 'work/zone/custom_foreign.ff').exists())
                self.assertFalse((output / 'work/zone/imagefile999.pak').exists())
                self.assertFalse((output / 'work/zone/assetfile999.pak').exists())
                self.assertEqual((output / 'work/zone/assetfile17.pak').stat().st_ino, (stock / 'zone/assetfile17.pak').stat().st_ino)
                self.assertEqual((output / 'work/zone/assetfile1.pak').stat().st_ino, pak.stat().st_ino)
                self.assertEqual((output / 'work/main/cp_zmb.ff').stat().st_ino, (stock / 'main/cp_zmb.ff').stat().st_ino)
                self.assertEqual((output / 'work/main/fileSysCheck.cfg').read_bytes(), before[Path('main/fileSysCheck.cfg')])
                self.assertNotEqual((output / 'work/main/fileSysCheck.cfg').stat().st_ino, (stock / 'main/fileSysCheck.cfg').stat().st_ino)
                # Execute the actual input guard without executing Build's main body.
                # Covers PowerShell JSON's automatic UTC DateTime conversion.
                guard_command = ". '" + str(ROOT / 'ops/Base-Client.Core.ps1') + "'; Add-Type -Path '" + str(ROOT / 'ops/hud-lab/HudFileIdentity.cs') + "'; $ast=[Management.Automation.Language.Parser]::ParseFile('" + str(ROOT / 'ops/hud-lab/Build-Hud.ps1') + "',[ref]$null,[ref]$null); $node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-HudInputsUnchanged'},$true); . ([scriptblock]::Create($node.Extent.Text)); $state=Get-Content -LiteralPath '" + str(output / 'state.local.json') + "' -Raw | ConvertFrom-Json; Assert-HudInputsUnchanged $state.Inputs $state.Work"
                guarded = subprocess.run(['pwsh', '-NoProfile', '-Command', guard_command], capture_output=True, text=True, timeout=30)
                self.assertEqual(guarded.returncode, 0, guarded.stdout + guarded.stderr)
                (stock / 'main/cp_zmb.ff').write_bytes(b'changed synthetic stock')
                guarded = subprocess.run(['pwsh', '-NoProfile', '-Command', guard_command], capture_output=True, text=True, timeout=30)
                self.assertNotEqual(guarded.returncode, 0)
                self.assertIn('identity/size/time changed', guarded.stderr)
                self.assertTrue((output / 'work/main/cp_zmb.ff').exists())
                # Real prepared transaction/NTFS inputs, injected ownership inventory
                # and release endpoint only. Both refusal paths must retain the lease.
                for occupied in (False, True):
                    probe = ". '" + str(ROOT / 'ops/Base-Client.Core.ps1') + "'; Add-Type -Path '" + str(ROOT / 'ops/hud-lab/HudFileIdentity.cs') + "'; $ast=[Management.Automation.Language.Parser]::ParseFile('" + str(ROOT / 'ops/hud-lab/Build-Hud.ps1') + "',[ref]$null,[ref]$null); foreach($name in @('Assert-HudInputsUnchanged','Assert-HudWorkVacant','Write-HudJson','Complete-HudRestore')){$node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true); . ([scriptblock]::Create($node.Extent.Text))}; $state=Get-Content -LiteralPath '" + str(output / 'state.local.json') + "' -Raw | ConvertFrom-Json; $script:releases=0; function Exit-IW7ResourceLease {param($Token) $script:releases++}; function Get-CimInstance {param($ClassName) " + ("[pscustomobject]@{Name='zonetool.exe';ExecutablePath=$null}" if occupied else "return @()") + "}; try { Complete-HudRestore $state '" + str(output / ('refused-' + str(occupied) + '.json')) + "' 'synthetic-retained-lease' } catch {}; [pscustomobject]@{Releases=$script:releases;Retained=$state.RetainedLeaseToken;Status=$state.RestorationStatus;Failure=$state.RestorationFailure;Restored=$state.Restored}|ConvertTo-Json -Compress"
                    refused = subprocess.run(['pwsh', '-NoProfile', '-Command', probe], capture_output=True, text=True, timeout=30)
                    self.assertEqual(refused.returncode, 0, refused.stdout + refused.stderr)
                    report = json.loads(refused.stdout)
                    self.assertEqual(report['Releases'], 0)
                    self.assertEqual(report['Retained'], 'synthetic-retained-lease')
                    self.assertEqual(report['Status'], 'Refused')
                    self.assertFalse(report['Restored'])
                    self.assertIn('occupied' if occupied else 'identity/size/time changed', report['Failure'])
                    self.assertTrue((output / 'work/main/cp_zmb.ff').exists())
                (stock / 'main/cp_zmb.ff').write_bytes(before[Path('main/cp_zmb.ff')])
                # Pure existing transaction restore; no reservation or process launch.
                command = ". '" + str(ROOT / 'ops/Base-Client.Core.ps1') + "'; $txn=Get-Content -LiteralPath '" + str(output / 'backup/recovery.local.json') + "' -Raw | ConvertFrom-Json; Restore-IW7BaseTransaction $txn"
                restored = subprocess.run(['pwsh', '-NoProfile', '-Command', command], capture_output=True, text=True, timeout=30)
                self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
                self.assertFalse((output / 'work/main/cp_zmb.ff').exists())
                self.assertFalse((output / 'work/zone/assetfile1.pak').exists())
                self.assertEqual(before, {p.relative_to(stock): p.read_bytes() for p in stock.rglob('*') if p.is_file()})
                recovery = json.loads((output / 'backup/recovery.local.json').read_text(encoding='utf-8-sig'))
                self.assertTrue(recovery['Restored'])
        finally:
            # Delete only this resolved, uniquely owned fixture root.
            if output.exists():
                self.assertEqual(output.resolve().parent, (ROOT / 'runtime').resolve())
                self.assertTrue(output.name.startswith('hud-test-'))
                shutil.rmtree(output)


if __name__ == '__main__':
    unittest.main()
