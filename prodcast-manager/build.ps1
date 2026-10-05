param([string]$Python='python',[string]$Output=(Join-Path $PSScriptRoot 'dist'),[switch]$SkipTests,[switch]$SkipSmoke)
$ErrorActionPreference='Stop'
$build=Join-Path $PSScriptRoot '.build'
if(-not $SkipTests){
    & $Python -m pytest (Join-Path $PSScriptRoot 'tests') -q
    if($LASTEXITCODE){
        Write-Warning 'Test run failed; retrying only failed tests once to tolerate transient Windows GUI initialization errors.'
        & $Python -m pytest (Join-Path $PSScriptRoot 'tests') -q --last-failed --last-failed-no-failures none
        if($LASTEXITCODE){throw 'Tests failed after one targeted retry'}
    }
}
$bundles=Join-Path $build 'onefile'
& $Python -m PyInstaller --noconfirm --clean --onefile --icon (Join-Path $PSScriptRoot "prodcast_manager/resources/prodcast-manager.ico") --name ProdCast-Manager --distpath $bundles --workpath (Join-Path $build 'gui') --specpath $build --windowed --paths $PSScriptRoot --add-data ((Join-Path $PSScriptRoot 'prodcast_manager\resources')+';prodcast_manager/resources') (Join-Path $PSScriptRoot 'manager.py')
if($LASTEXITCODE){throw 'GUI build failed'}
New-Item -ItemType Directory -Path $Output -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $bundles 'ProdCast-Manager.exe') -Destination (Join-Path $Output 'ProdCast-Manager.exe') -Force
New-Item -ItemType Directory -Path (Join-Path $Output 'prodcast-data\logs'),(Join-Path $Output 'prodcast-data\sites') -Force | Out-Null
if(-not $SkipSmoke){
    & (Join-Path $Output 'ProdCast-Manager.exe') self-test --gui-smoke
    if($LASTEXITCODE){throw 'Packaged resource smoke failed'}
}
