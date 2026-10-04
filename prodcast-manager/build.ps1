param([string]$Python='python',[string]$Output=(Join-Path $PSScriptRoot 'dist'),[switch]$SkipTests,[switch]$SkipSmoke)
$ErrorActionPreference='Stop'
$build=Join-Path $PSScriptRoot '.build'
if(-not $SkipTests){
    & $Python -m pytest (Join-Path $PSScriptRoot 'tests') -q
    if($LASTEXITCODE){throw 'Tests failed'}
}
$bundles=Join-Path $build 'portable-bundles'
& $Python -m PyInstaller --noconfirm --clean --onefile --icon (Join-Path $PSScriptRoot "prodcast_manager/resources/prodcast-manager.ico") --name ProdCast-Manager --distpath $bundles --workpath (Join-Path $build 'gui') --specpath $build --windowed --paths $PSScriptRoot --add-data ((Join-Path $PSScriptRoot 'prodcast_manager\resources')+';prodcast_manager/resources') (Join-Path $PSScriptRoot 'manager.py')
if($LASTEXITCODE){throw 'GUI build failed'}
& $Python -m PyInstaller --noconfirm --clean --onefile --icon (Join-Path $PSScriptRoot "prodcast_manager/resources/prodcast-manager.ico") --name prodcast-manager-cli --distpath $bundles --workpath (Join-Path $build 'cli') --specpath $build --console --paths $PSScriptRoot --add-data ((Join-Path $PSScriptRoot 'prodcast_manager\resources')+';prodcast_manager/resources') (Join-Path $PSScriptRoot 'manager.py')
if($LASTEXITCODE){throw 'CLI build failed'}
New-Item -ItemType Directory -Path $Output -Force | Out-Null
foreach($name in @('ProdCast-Manager','prodcast-manager-cli')) {
    Copy-Item -LiteralPath (Join-Path $bundles ($name+'.exe')) -Destination $Output -Force
}
if(-not $SkipSmoke){
    & (Join-Path $Output 'prodcast-manager-cli.exe') self-test --gui-smoke
    if($LASTEXITCODE){throw 'Packaged resource smoke failed'}
}
