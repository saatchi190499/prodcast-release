# 06. Worker 02 — PC-WORKER-02 / 192.0.2.85

Это отдельная установка на втором Windows-сервере. Нужен готовый ZIP из v0.2, исходный commit `3fb03104f8ac39d31a0d338910a504364cfaff2c`. На Worker 02 исходники не нужны. Все команды ниже — повышенная интерактивная PowerShell.

Не копировать рабочий каталог Worker 01: у Worker 02 свои PostgreSQL/Redis credentials, service name, nodename и машинное DPAPI-хранилище. Общие только версия пакета, публичные CA, media/signing keys App.

## 1. Проверить доступ и входящие файлы

```powershell
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion -lt [version]'7.4' -or ![Environment]::Is64BitProcess) { throw 'Откройте PowerShell 7.4+ x64' }
hostname
Get-Date
Resolve-DnsName prodcast-db-01.example.internal
Resolve-DnsName prodcast-app-01.example.internal
Test-NetConnection prodcast-db-01.example.internal -Port 5432
Test-NetConnection prodcast-db-01.example.internal -Port 6380
Test-NetConnection prodcast-app-01.example.internal -Port 443
$inbox = 'C:\Install\prodcast-inbox'
& icacls.exe $inbox /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)(F)' '*S-1-5-32-544:(OI)(CI)(F)'
if ($LASTEXITCODE) { throw 'Не удалось защитить inbox' }
Get-ChildItem -LiteralPath $inbox -Name
```

Проверить hostname `PC-WORKER-02`, адрес `.85`, True у трёх TCP-тестов, наличие комплекта **out/worker02**: `secrets.json` и два публичных CA. На DB должны существовать роль `prodcast_worker_02`, её HBA для `.85`, права из DB шага 8 и Redis ACL `prodcast_worker_02_scheduler`.

## 2. Проверить и распаковать ZIP

Перенести ZIP, SHA256SUMS и release-manifest в `C:\Install\worker-release` из того же релиза v0.2, что для Worker 01:

```powershell
Set-Location 'C:\Install\worker-release'
$zip = 'prodcast-worker-v0.2-windows-amd64.zip'
$line = Get-Content .\SHA256SUMS | Where-Object { ($_ -split '\s+',2)[1] -eq $zip }
if (@($line).Count -ne 1) { throw 'Нет однозначного checksum ZIP' }
$expected = ($line -split '\s+',2)[0]
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $expected) { throw 'ZIP checksum mismatch' }
$package = 'C:\Install\worker-v2026.9.17-rc.1'
if (Test-Path -LiteralPath $package) { throw 'Нужен новый каталог пакета' }
Expand-Archive -LiteralPath $zip -DestinationPath $package
Get-ChildItem -LiteralPath $package -Name
```

Сверить хеш также с доверенной страницей релиза/актом Worker 01. В ZIP должны быть payload, wheelhouse, requirements.lock, runtime, WinSW и Python installer.

## 3. Установить Python 3.14.7 x64

```powershell
$installer = Join-Path $package 'python-3.14.7-amd64.exe'
$sig = Get-AuthenticodeSignature -LiteralPath $installer
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
    throw 'Не подтверждена подпись Python'
}
$result = Start-Process -FilePath $installer -Wait -PassThru -WindowStyle Hidden -ArgumentList @(
    '/quiet','InstallAllUsers=1','TargetDir=C:\ProdCast\Python314','PrependPath=0','Include_test=0'
)
if ($result.ExitCode -notin @(0,3010)) { throw 'Python installer failed' }
if ($result.ExitCode -eq 3010) { throw 'Сначала перезагрузить сервер и продолжить с проверки версии' }
$python = 'C:\ProdCast\Python314\python.exe'
& $python -c "import platform,struct; assert platform.python_version()=='3.14.7'; assert struct.calcsize('P')==8; print(platform.python_version())"
if ($LASTEXITCODE) { throw 'Нужен CPython 3.14.7 x64' }
```

Python 3.13, другая patch-версия или 32-bit не подходят: runtime содержит `.pyc` и installer проверяет точную версию. На целевом сервере pip не должен скачивать зависимости: они уже в wheelhouse.

## 4. Создать пользователя и права службы

```powershell
$svcPassword = Read-Host 'Новый пароль локального prodcast-svc на Worker 02' -AsSecureString
New-LocalUser -Name 'prodcast-svc' -Password $svcPassword -Description 'ProdCast Worker service' -UserMayNotChangePassword
$svcPassword.Dispose()
$account = $env:COMPUTERNAME + '\prodcast-svc'
Get-LocalUser -Name prodcast-svc
Get-LocalGroupMember -SID 'S-1-5-32-544'
```

Пользователь включён и не состоит в Administrators. Сохранить отдельный пароль в хранилище. В `secpol.msc` → Local Policies → User Rights Assignment:

1. Добавить `PC-WORKER-02\prodcast-svc` в **Log on as a service**.
2. Проверить отсутствие запрещающего **Deny log on as a service**.
3. Добавить его в **Deny log on locally** и **Deny log on through Remote Desktop Services**.
4. При управлении через GPO закрепить права в GPO; учесть срок действия пароля в обслуживании службы.

## 5. Установить службу Worker 02

```powershell
$package = 'C:\Install\worker-v2026.9.17-rc.1'
$installDir = 'C:\ProdCast\Worker\v2026.9.17-rc.1'
$python = 'C:\ProdCast\Python314\python.exe'
$cred = Get-Credential -UserName ($env:COMPUTERNAME+'\prodcast-svc') -Message 'Пароль службы Worker 02'
& "$package\runtime\Install-Worker.ps1" -InstallDir $installDir -PythonPath $python -WorkerNumber '02' -ServiceCredential $cred
$cred = $null
Get-Service ProdCastWorker02
```

Ожидается Stopped/Manual. Установщик создаёт venv offline, проверяет хеши и зависимости, настраивает WinSW, AppContainer runtime ACL и writable jobs/logs/recovery. Путь может совпадать с Worker 01, поскольку это другой сервер.

## 6. Настроить site.json, CA и секреты

```powershell
$site = [ordered]@{
    worker_number = '02'
    postgres_host = 'prodcast-db-01.example.internal'
    postgres_port = 5432
    postgres_db = 'prodcast2'
    postgres_user = 'prodcast_worker_02'
    redis_host = 'prodcast-db-01.example.internal'
    redis_port = 6380
    redis_user = 'prodcast_worker_02_scheduler'
    main_server_url = 'https://prodcast-app-01.example.internal'
}
$site | ConvertTo-Json | Set-Content -LiteralPath "$installDir\site.json" -Encoding UTF8
Copy-Item -LiteralPath 'C:\Install\prodcast-inbox\prodcast-db-ca.crt' -Destination "$installDir\prodcast-db-ca.crt"
Copy-Item -LiteralPath 'C:\Install\prodcast-inbox\prodcast-app-ca.crt' -Destination "$installDir\prodcast-app-ca.crt"
& "$package\runtime\Protect-Secrets.ps1" -InstallDir $installDir
& icacls.exe $installDir
& icacls.exe "$installDir\scheduler.machine.dpapi"
```

Ввести `postgres_password` = **PW_W02**, `redis_password` = **REDIS_W02**, `media_key` = **MEDIA_KEY**, `signing_key` = **SIGNING_KEY**. Пароли с суффиксом W01 не использовать. Приватный DPAPI-файл создаётся локально на Worker 02 и доступен SYSTEM/Administrators/service account. Удалить временный `C:\Install\prodcast-inbox\secrets.json` после сохранения секретов в хранилище, очистить clipboard.

## 7. Запустить и проверить Worker 02

```powershell
& "$package\runtime\Start-Worker.ps1" -InstallDir $installDir -WorkerNumber '02'
Get-Service ProdCastWorker02
Get-Content -LiteralPath "$installDir\logs\scheduler-service-ready.json"
Get-CimInstance Win32_Service -Filter "Name='ProdCastWorker02'" | Select-Object Name,State,StartMode,StartName,PathName
Get-ChildItem -LiteralPath "$installDir\logs" | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime,Length
& sc.exe qfailure ProdCastWorker02
```

Ожидается Running под `PC-WORKER-02\prodcast-svc`, свежие `windows-appcontainer`, `postgres_tls=true` и три рабочие очереди в marker. На App проверить отдельный nodename `prodcast-worker-02@...` через Celery inspect; нельзя считать наличие Worker 01 подтверждением второго сервера.

## 8. Перезагрузка и отдельное задание

Перезагрузить Worker 02 в окно установки, проверить автоматический запуск, свежий marker и подключение к Celery. Выполнить отдельный тест на Worker 02 по главе 07. Зафиксировать ID задания и hostname исполнителя. После успешной проверки обоих серверов вернуться в App шаг 10 и включить единственный beat.

**Для акта:** hostname/IP, тот же ZIP SHA256, Python 3.14.7 x64, локальный пользователь без admin, отдельные DB/Redis identities, marker, Celery nodename, тест задания, reboot. Затем завершить общую приёмку.
