"""Every Python and PowerShell source under tools-source/ and sdk/modding/ parses.

usage (from the repository root or a composed workspace): python -B tools-source/compile_check.py

Python files are compiled with compile() (no import, nothing executed, no .pyc written). PowerShell files are
parsed with the language parser (nothing executed). This is the only guard over the scripts no test loads; it
says that a file is syntactically valid, nothing about what it does. Exit 1 lists every file that does not parse; finding no file of
either kind (wrong folder) is also a failure.
"""
import os
import subprocess
import sys

ROOTS = ('tools-source', 'sdk/modding')
PARSE = r'''
$bad = 0
foreach ($path in [Console]::In.ReadToEnd() -split "`n" | Where-Object { $_.Trim() }) {
    $tokens = $null; $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($path.Trim(), [ref]$tokens, [ref]$errors)
    foreach ($e in $errors) { $bad++; "{0}:{1}: {2}" -f $path.Trim(), $e.Extent.StartLineNumber, $e.Message }
}
exit [Math]::Min($bad, 1)
'''


def sources(extension):
    for root in ROOTS:
        for folder, names, files in os.walk(root):
            names[:] = sorted(n for n in names if n not in ('__pycache__', 'runtime', 'node_modules'))
            for name in sorted(files):
                if name.endswith(extension):
                    yield os.path.join(folder, name)


def main():
    failures = []
    python = list(sources('.py'))
    for path in python:
        try:
            with open(path, 'rb') as handle:
                compile(handle.read(), path, 'exec', dont_inherit=True)
        except (SyntaxError, ValueError) as error:
            failures.append('%s: %s' % (path, error))
    powershell = [os.path.abspath(p) for p in sources('.ps1')]
    if powershell:
        run = subprocess.run(['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', PARSE],
                             input='\n'.join(powershell), capture_output=True, text=True)
        if run.returncode:
            lines = [line for line in (run.stdout + run.stderr).splitlines() if line.strip()]
            failures.extend(lines or ['pwsh exit %d with no output' % run.returncode])
    if not python or not powershell:
        failures.append('found %d Python and %d PowerShell files: run from the repository root or a composed workspace'
                        % (len(python), len(powershell)))
    print('compile_check: %d Python files, %d PowerShell files, %d failures' % (len(python), len(powershell), len(failures)))
    for line in failures:
        print('FAIL ' + line)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
