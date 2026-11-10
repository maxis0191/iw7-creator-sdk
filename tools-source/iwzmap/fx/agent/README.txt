FX agent run scripts (Station Zero stage 2): build-fx.ps1 (g24 + fx module + imports), run-proof.ps1 (leased proof run + fx_proof), run-fx.ps1 (leased runner wrapper, waits for other agents, stops on the owner game), zt-retry.ps1, import_dry.py, fxprobe2.gsc (probe fixture: N effects at a station, off/on frames), probe_sheet.py / probe_analyze.py.

What each file is (2026-11-10):
- Tool, cited by ../../README.md: vfx_lit.py (lists the lighting class of every material of an effect).
- Run scripts of one agent, November 2026: build-fx.ps1, run-proof.ps1, run-fx.ps1, zt-retry.ps1, build-dfx.ps1, run-dproof.ps1, import_dry.py. run-proof.ps1 and run-dproof.ps1 call run-fx.ps1 from a tools folder of the run directory, not from here.
- Probes and their analysis: fxprobe2.gsc, fxprobe8.gsc, fxprobe9.gsc, fxprobe10.gsc, probe_analyze.py, probe6_analyze.py, probe_sheet.py.
Since 2026-11-10 the run scripts take their machine locations from ../../machine.ps1 (see ../../README.md, "Machine locations") and use the tools of this checkout; the folder names of the stage are still those of the original runs. Nothing else in the repository references the run scripts or the probes. They are kept because the Station Zero stage 2 work is paused, not abandoned; whoever resumes it decides whether they are spent.
