param([Parameter(Mandatory)][string[]]$ZtArgs,[string]$Work='C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\fx\ztwork',[string]$Owner='IWZ FX agent zonetool',[int]$TimeoutSec=1800,[int]$Tries=200)
# zonetool under the machine-wide Build lease (zt.ps1), retried every 60 s while another owner holds the heavy slot
$zt='C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-fx\tools-source\iwzmap\zt.ps1'
for($k=0;$k -lt $Tries;$k++){
  try { return (& $zt -Work $Work -ZtArgs $ZtArgs -Owner $Owner -TimeoutSec $TimeoutSec) }
  catch { if($_.Exception.Message -match 'Resource busy|Heavy job already reserved|wait before heavy admission|wait for its owner'){ Start-Sleep 60; continue }; throw }
}
throw 'resource lease not obtained'
