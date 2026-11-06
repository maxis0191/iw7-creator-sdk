$ErrorActionPreference='Stop'
$msb = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
. 'C:\Users\ezvalo\Documents\IW7-Products\iw7-mod-components\ops\Resource-Scheduler.Core.ps1'
$W='C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-iwz-map'
$lease=Enter-IW7ResourceLease -Scope $W -Kind Build -PhysicalBytes 8GB -CommitBytes 12GB -Owner 'IWZ map compiler zonetool build'
try {
  & $msb "$W\build\x64-zt.sln" /t:zonetool /m /nodeReuse:false /p:Configuration=Release /p:Platform=x64 /v:minimal /nologo 2>&1 | Select-String -Pattern 'error|warning C4|zonetool.exe' | Select-Object -First 40
  "exit $LASTEXITCODE"
} finally {
  Exit-IW7ResourceLease -Token $lease.Token | Out-Null
}
