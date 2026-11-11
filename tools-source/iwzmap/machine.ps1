param(
  [Parameter(Mandatory, Position=0)]
  [ValidateSet('Runtime','Products','Server','Components','ZoneToolExe','ZoneToolSource','TemplateDump','GameRoot','BakePython')]
  [string]$Name,
  [Parameter(Position=1)][string]$Child='',
  [switch]$MustExist)
# The one place where the map tools learn where things are on this machine. Prints one path.
#
#   Runtime         $env:IWZ_RUNTIME          else <Documents>\IW7-Runtime          work folders, dumps, runs
#   Products        $env:IWZ_PRODUCTS         else <Documents>\IW7-Products         checkouts of the products
#   Server          $env:IWZ_SERVER           else <Documents>\IW7-Paris-Server     server checkout (local runner)
#   Components      $env:IWZ_COMPONENTS       else <Products>\iw7-mod-components    resource scheduler
#   ZoneToolExe     $env:IWZ_ZONETOOL_EXE     else <Products>\worktrees\<Child>\build\bin\x64\Release\zonetool.exe
#   ZoneToolSource  $env:IWZ_ZONETOOL_SOURCE  else <Products>\worktrees\<Child>
#   TemplateDump    $env:IWZ_TEMPLATE_DUMP    else <Runtime>\iwz-map-ref-a\dump     stock dumps (cp_zmb, techsets_*)
#   GameRoot        $env:IWZ_GAME_ROOT        no default: name a bench root, never the owner's game folder
#   BakePython      $env:IWZ_BAKE_VENV        else <Runtime>\iwzmap-bake-venv     the light baker's Python environment (bake\New-BakeEnv.ps1)
#
# <Child> is appended to the location, except for ZoneToolExe and ZoneToolSource where it names the default
# worktree and a set variable wins as it is. A script parameter passed by the caller never reaches this file.
# -MustExist throws, naming the variable, when the resulting path is absent.
$ErrorActionPreference='Stop'
function Pick([string]$Variable,[string]$Default){
  $value=[Environment]::GetEnvironmentVariable($Variable)
  if($value){ $value } else { $Default }
}
$documents=[Environment]::GetFolderPath('MyDocuments')
$runtime=Pick 'IWZ_RUNTIME' (Join-Path $documents 'IW7-Runtime')
$products=Pick 'IWZ_PRODUCTS' (Join-Path $documents 'IW7-Products')
$variable=@{Runtime='IWZ_RUNTIME';Products='IWZ_PRODUCTS';Server='IWZ_SERVER';Components='IWZ_COMPONENTS';
  ZoneToolExe='IWZ_ZONETOOL_EXE';ZoneToolSource='IWZ_ZONETOOL_SOURCE';TemplateDump='IWZ_TEMPLATE_DUMP';GameRoot='IWZ_GAME_ROOT';BakePython='IWZ_BAKE_VENV'}[$Name]
switch($Name){
  'Runtime'        { $path=$runtime }
  'Products'       { $path=$products }
  'Server'         { $path=Pick $variable (Join-Path $documents 'IW7-Paris-Server') }
  'BakePython'     { $path=Pick $variable (Join-Path $runtime 'iwzmap-bake-venv') }
  'Components'     { $path=Pick $variable (Join-Path $products 'iw7-mod-components') }
  'TemplateDump'   { $path=Pick $variable (Join-Path $runtime 'iwz-map-ref-a\dump') }
  'ZoneToolExe'    { $path=Pick $variable (Join-Path $products "worktrees\$Child\build\bin\x64\Release\zonetool.exe"); $Child='' }
  'ZoneToolSource' { $path=Pick $variable (Join-Path $products "worktrees\$Child"); $Child='' }
  'GameRoot'       {
    $path=Pick $variable ''
    if(!$path){ throw "Set `$env:IWZ_GAME_ROOT to a bench root (scripts that have a game folder parameter also accept it there). No default: tests never run in the owner's game folder." }
  }
}
if($Child){ $path=Join-Path $path $Child }
if($MustExist -and !(Test-Path -LiteralPath $path)){ throw "Not found: $path. Set `$env:$variable to the right location." }
$path
