# Private source archive for the strict IW7 GSC auditor

This directory preserves a text-only `git format-patch` series for the separately
owned gsc-tool source checkout. It belongs in the existing private project
repository. It contains no executable, compiler, generated game script, retail
data, runtime log or credentials. No public fork or upstream PR was created.

`manifest.json` binds the upstream base revision, original candidate revision,
Git tree IDs, ordered patch SHA256 hashes, changed source blob SHA256 hashes and
license notices. Patch history retains the original failed candidates and their
corrections; it is not flattened into an unexplained final diff.

## Reconstruct source without compiling

Use an existing trusted source-only gsc-tool repository containing the base commit,
or obtain that exact base from the upstream URL in the manifest. Do not initialize
submodules for this reconstruction. Choose a fresh destination; these commands
must not be used in an occupied checkout. No build or game operation follows
automatically.

```powershell
$archive = (Resolve-Path 'tools-source/gsc-consumption-tool').Path
$manifest = Get-Content -LiteralPath (Join-Path $archive 'manifest.json') -Raw | ConvertFrom-Json
python -B (Join-Path $archive 'verify_archive.py')
if ($LASTEXITCODE -ne 0) { throw 'Archive verification failed' }
$source = 'PATH_TO_TRUSTED_GSC_TOOL_REPOSITORY'
$work = 'PATH_TO_FRESH_SOURCE_CHECKOUT'
git -c core.autocrlf=false clone --no-hardlinks --no-checkout --no-recurse-submodules -- $source $work
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
git -C $work -c core.autocrlf=false checkout --detach $manifest.base_revision
if ($LASTEXITCODE -ne 0) { throw 'Base checkout failed' }
$patches = @($manifest.patches | ForEach-Object { Join-Path $archive $_.path })
git -C $work -c core.autocrlf=false am -- $patches
if ($LASTEXITCODE -ne 0) { throw 'Patch application failed; retain the failed source checkout' }
python -B (Join-Path $archive 'verify_archive.py') --repository $work
if ($LASTEXITCODE -ne 0) { throw 'Reconstructed Git tree differs' }
```

Git needs the user's normal local committer identity for `git am`. Do not change
global Git configuration. The verifier checks archive bytes before application,
then optionally checks a clean reconstructed repository's base ancestry, final Git
tree and changed blobs. It does not fetch, compile, initialize dependencies or
modify a repository.

An equal Git tree proves identical tracked blob bytes, file modes, paths and
submodule gitlink IDs. Windows working-copy line endings can differ through Git
attributes/configuration; the claim is about Git objects, not every checkout file.
`git am` preserves authorship but can change committer metadata and therefore
commit IDs. The manifest records the original candidate revision as provenance;
the reconstruction is **not** promised to have that same HEAD commit ID.

No binary reproducibility is claimed. A new build must generate an identity for
its actual clean reconstructed commit and materialized pinned zlib, use a new
reviewed Plan and pass the normal full resource admission. Never overwrite the
generated revision with the original candidate's ID just to match old pins.
Dependency gitlinks identify required sources; this archive does not contain
those dependency sources or a compiler/toolchain.

## License and verification limits

The pinned gsc-tool source headers identify GNU GPLv3 and refer to its `LICENSE`.
`licenses/gsc-tool-LICENSE.txt` preserves that complete file unchanged. The pinned
zlib dependency has its own copyright and license notice, preserved unchanged in
`licenses/zlib-LICENSE.txt`; the manifest records its separate source revision.
Original notices and attribution remain in the patch series. This description
records the supplied licenses; it does not relicense the tool, private project,
third-party server scripts or game data.

The native v3 build successfully registered its original job and built zlib/GSC
libraries plus the reader-test executable, then failed in the audit entry point's
Windows/zlib header order. No CTest, native negative test or Beacon consumption
receipt was produced. The later v4 attempt compiled the include-order correction
and passed native tests and both Beacon binder steps, but overall supervision
failed on an unqualified residual descendant. See the reconstructed
`audit/README.md` for earlier failures and the project's
[v4 evidence](../../sdk/modding/gsc-consumption-audit.md) for that later measurement.
The archived tool source remains exactly the revision in the manifest.

The tenth patch adds the reviewed residual-member diagnostic to revision
`f813f9758006e33857339c19ece48a642212ac5f`. The first nine patch files are preserved
byte for byte. This append belongs to the tranche after the nine-patch/v4
checkpoint; it does not revise that earlier history or turn v4 into a success.
The diagnostic reuses the project's pinned read-only original-job observer,
records bounded identity/image-file hash evidence and grants no new acceptance.
The separately admitted v5 diagnostic subsequently identified a residual original-
job `vctip.exe` by image-file hash, creation time, parent PID and membership in
31 ms. All functional native steps passed, but its parent identity was not
captured and global supervision remained failed. See the
[v5 checkpoint](../../sdk/modding/gsc-residual-diagnostic-20261012.json).
Another attempt still requires a fresh reviewed Plan and coordinator GO.

The eleventh patch preserves independently reviewed source revision
`41fdc19fd443bddafb90b9f6664266adb008c494`: an explicit closure contract and pure
identity predicate with 96 additional source checks. The first ten patch files are
unchanged. That revision grants no Stop or acceptance and does not import the
predicate into its launcher. It requires positive original-job membership and
pinned file identity without inventing a compiler ancestry. The subsequent concrete
supervisor integration is preserved separately by patch twelve below.
The existing source-only reconstruction was extended in place; its 22 changed blobs
and tree `5f01dbcc65c7b5a399db0bbeed4074973f8d2b4a` match the archived source.
No new clone, dependency initialization, Plan, native execution or cleanup occurred.

The twelfth patch adds independently reviewed revision
`eabe74ab65d8ce2a943b54d24b15a60749a0cf2a`, which connects the original-job supervisor
to bounded guarded receipt/identity validation. Its 338 PowerShell checks and four
Python preparation tests passed; this is source/mock evidence only. The earlier
eleven patches are unchanged. Schema `/2` build receipts bind a fresh run identity,
root PID, exact plan and lease, ordered successful steps, source/tool/compiler pins
and both input/assembly witnesses. Qualified telemetry cleanup requires two fresh
original-job member queries, retained compiler/vctip read guards, an original-job
Stop and a fresh zero-members/root-zero result within the unchanged drain deadline.
The existing source-only reconstruction was extended in place and all 26 changed
blobs and tree `74143703049b4fbb9ba702d1ea74bc58be5607ac` match the archived revision.
At the archive checkpoint, actual two-second drain timing remained unverified.
No native execution is authorized by this archive itself. v4/v5 remain global failures
and their historical `/1` receipts cannot qualify under the new closure contract.

A subsequent explicit coordinator GO admitted one v6 run from the original source
revision and SDK archive commit `b85b6203a338834487ecc0ae9d69044bb6bd68d5`. All native
steps passed and qualified original-job closure completed in 312 ms of the unchanged
2,000 ms drain. Global supervision passed, the job closed and its lease was released;
the subsequent inventory confirmed Main unchanged and no remaining builder. See the
[v6 evidence](../../sdk/modding/gsc-qualified-closure-20261012.json). This is evidence
for that exact original-source build; no binary reproducibility claim is made for
the different `git am` reconstructed revision, and no package/runtime gate is promoted.

`reconstruction-validation.json` records only the local source reconstruction
check. Passing it does not establish executable correctness, complete GSC import
analysis, asset closure, runtime readiness or owner gameplay acceptance.

## Encoded-reference source tranche

Patches thirteen through fifteen preserve the complete source chain:
`bfa2d4af5e9687bcf30b6a45ad04db403f63538a` adds the exhaustive reference profile,
independent byte reader and separate native mode;
`805f07676bb1bdad9effee5d907a5fe9f4bcfa01` fixes literal diagnostic offsets after
independent review; `42e6c403a789b38ede39fd58ff0cb5f77da7d002` adds the actual
native reference phase to the supervised recipe. The first twelve patches and
license files remain byte-for-byte unchanged. Contract/correction review was
favorable. The recipe subsequently received a favorable independent source review;
the next exact Plan and execution still require review and GO.

The existing retained reconstruction was extended in place to tree
`92a8a96529f8ee5acaa72363c261b97a56b9ebfb`; all 35 changed blobs match. Its checkout
is 30,588,390 bytes under the existing 64 MiB source-only allowance. No new clone,
dependency initialization, native execution or deletion occurred. Git `am` creates
a different commit identity; this is source-tree reconstruction, not executable
reproducibility.

The reference profile also pins actual source-table bytes. The retained baseline
had LF table files whereas the reviewed Windows source has CRLF. Seven existing
table files were materialized as CRLF only after that exact candidate encoding
matched each pinned SHA256; their normalized Git blobs and tree remained unchanged.
The index was refreshed with those identical blobs. No Git configuration changed.
The reconstructed profile now verifies all eight physical source files as well as
the tree. Future reconstructions must check these physical pins too; a matching
Git tree alone does not promise a matching source digest or table byte encoding.

The recipe uses Plan `/2` and receipt `/3`, preserving consumption `/1` and all
earlier native tests. Its eighth phase plans 159 native invocations: 153 opcode
controls (two expected refusals), four unresolved/dynamic cases and two exact
Beacon binaries. It retains four native/bound reference JSONs, the controls
summary, written runtime pins and the pinned reader/profile/harness. Twenty-seven
completion artifacts and thirty residual-closure guards fit the unchanged
32-file/128-MiB/two-second limits with the existing zlib dependency. No new Run or
lease is authorized by this archive.

Source/mock validation passed 367 PowerShell checks and 28 Python tests, including
read-only decoding of the retained Beacon bytes. This does not supply the new
native reference stream. See [the sanitized source checkpoint](../../sdk/modding/gsc-reference-source-20261012.json)
and reconstructed `audit/reference-contract.md` for exact scope and remaining gates.

The subsequently authorized V7 run did produce the new reference witnesses and
passed all eight phases, including 159 reference invocations. Its global
supervision nevertheless failed because the new Plan field indexer received a
`PSCustomObject` instead of the hashtable used by mocks. Owned failure cleanup
closed the original job and released the lease; this does not qualify the failed
Run. The archived source remains `42e6c403` at this checkpoint. See the
[V7 failure record](../../sdk/modding/gsc-reference-v7-failure-20261012.json).
An eventual source correction must be appended separately and cannot rewrite
V7's supervision, previous patch bytes or older native evidence.
