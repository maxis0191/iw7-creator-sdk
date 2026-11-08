@echo off
for /f "usebackq delims=" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath`) do set VS=%%i
call "%VS%\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /O2 /LD /MT /Imh\include error_journal.c mh\src\buffer.c mh\src\hook.c mh\src\trampoline.c mh\src\hde\hde64.c /Fe:iw7_error_journal.dll /link user32.lib dbghelp.lib
cl /nologo /O2 /LD /MT /Imh\include iw7_fxperf.c mh\srcuffer.c mh\src\hook.c mh\src	rampoline.c mh\src\hde\hde64.c /Fe:iw7_fxperf.dll /link user32.lib dbghelp.lib d3d11.lib dxgi.lib dxguid.lib
