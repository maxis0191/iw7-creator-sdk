param(
    [Parameter(Mandatory)][ValidatePattern('^cp_[a-z0-9_]+$')][string]$Map,   # stock map whose zone holds the models
    [Parameter(Mandatory)][string[]]$Models,
    [Parameter(Mandatory)][string]$Cam,                                         # "x,y,z,yaw,pitch[,rel]|..."
    [Parameter(Mandatory)][string]$OutputRoot,                                  # fresh directory per run
    [string]$Runner=(& "$PSScriptRoot\..\machine.ps1" Server 'ops\iwzmap\Test-IWZMapLocal.ps1'),
    [Parameter(Mandatory)][string]$SourcePackage,                               # prepared server inputs (bootstrap.ps1 output of the server repository)
    [string]$GameRoot=(& "$PSScriptRoot\..\machine.ps1" GameRoot),
    [string]$UsermapDir='-',                                                    # '-' = stock map; else a usermap dir
    [double]$Fill=0.30,
    [string]$ExtraArgs='',
    [int]$MaxWaitMin=180,
    [int]$MinSeconds=300,                                                       # map load + intro before the booth starts
    [string]$InjectDll=''                                                       # optional Com_Error journal DLL
)
# Engine preview of stock models through the local private runner (sv_lanOnly, random password, loopback,
# private desktop, staged files restored) with the iwzmap_preview.gsc fixture. Waits 60 s and retries with a
# new output directory while the machine-wide resource lease is busy.
$ErrorActionPreference='Stop'
$fixture=Join-Path $PSScriptRoot 'iwzmap_preview.gsc'
$chunks=@(); $cur=''
foreach($m in $Models){ if($m -notmatch '^[A-Za-z0-9_/.:-]+$'){throw "bad model name $m"}; if(($cur.Length+$m.Length+1) -gt 900){$chunks+=$cur;$cur=''}; $cur=if($cur){"$cur,$m"}else{$m} }
if($cur){$chunks+=$cur}
if($chunks.Count -gt 10){throw 'at most 10 dvar chunks (about 300 models)'}
$dv=''; for($i=0;$i -lt $chunks.Count;$i++){ $dv+=" +set paris_iwz_pv$i `"$($chunks[$i])`"" }
$camCount=($Cam.Split('|')).Count
$seconds=[Math]::Min(600,[Math]::Max($MinSeconds,[int](120+$camCount*($Models.Count*2.2+8))))
$args0="+set paris_iwz_cam `"$Cam`" +set paris_iwz_fill $Fill$dv $ExtraArgs"
$inject=@{}; if($InjectDll){$inject.InjectDll=$InjectDll}
$deadline=[datetime]::UtcNow.AddMinutes($MaxWaitMin); $try=0
while($true){
    $out=if($try){"$OutputRoot-r$try"}else{$OutputRoot}
    $err=''
    try{ & $Runner -SourcePackage $SourcePackage -GameRoot $GameRoot -OutputRoot $out -UsermapDir $UsermapDir -Map $Map -Fixture $fixture -ExtraArgs $args0 -Seconds $seconds @inject }
    catch{ $err=$_.Exception.Message }
    $res=Join-Path $out 'result.local.json'
    if(!$err -and (Test-Path $res)){ $err=(Get-Content $res -Raw|ConvertFrom-Json).Error }
    if($err -and ($err -match 'Resource busy|Heavy job already reserved|Base game occupied|Resource lease not found') -and [datetime]::UtcNow -lt $deadline){ "busy ($err); retry in 60 s"; Start-Sleep 60; $try++; continue }
    "RUN DIR $out"
    break
}
