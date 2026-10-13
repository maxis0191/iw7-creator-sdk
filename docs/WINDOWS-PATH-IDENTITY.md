# Creator Windows path identity correction - 2026-10-13

Executed server CI exposed SDK Creator failures when Windows supplied an 8.3
temporary directory such as `RUNNER~1` while Python resolved an equivalent long
path. SourceRoot comparison rejected the same project; package receipt comparison
rejected its own successfully written archive. This blocks server PR207/209 and
is the concrete diagnosis for SDK issue2.

Creator now rejects redirected filesystem ancestors first, then resolves the
existing project/active-project paths and each fresh output's existing parent.
Fresh-output, overlap, parameter-byte and receipt checks remain enforced.
No redirect guard is bypassed by resolution and no existing output is overwritten.

Both new real CLI regressions fail against the previous Creator source and pass
with the fix. All 73 Creator tests pass locally, including the Windows alias
tests (not skipped), using the retained source dependency layout. Fixtures use
synthetic text and the real ZIP writer; no native compiler, game or deployment
is invoked. Hosted exact-head source checks remain a separate required gate.

This patch is authored in the canonical Creator SDK repository. Until server
migration PR206 removes the legacy SDK tree, the two changed source/test files
are also integrated into the blocked server branches to validate their current
CI inputs. Do not restore that legacy tree after the migration lands.
