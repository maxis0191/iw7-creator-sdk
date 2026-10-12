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

`reconstruction-validation.json` records only the local source reconstruction
check. Passing it does not establish executable correctness, complete GSC import
analysis, asset closure, runtime readiness or owner gameplay acceptance.
