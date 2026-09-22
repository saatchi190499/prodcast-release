# 05. Worker 01 — PC-WORKER-01 / 192.0.2.21

Предварительно: App мигрирован, DB шаг 8 выполнен, Redis ACL пользователя `prodcast_worker_01_scheduler` создан, HTTPS App доступен. Служба использует Windows AppContainer для исполняемого Python. Docker и Linux Worker на этом сервере не устанавливаются.

Все действия — интерактивная PowerShell **Run as administrator**. Для автоматического входа службы требуется локальная учётная запись без административных прав.

## 1. Проверить сервер и защитить входящие файлы

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

Во всех трёх сетевых тестах `TcpTestSucceeded=True`. В inbox находятся `secrets.json`, `prodcast-db-ca.crt`, `prodcast-app-ca.crt` именно для **01**. Fingerprint CA сверить с главой 01. Не открывать входящие порты для Redis/PostgreSQL/Celery на Windows: Worker подключается наружу.

## 2. Получить готовый Windows-пакет

Из полного v0.2 передать в `C:\Install\worker-release` файл `prodcast-worker-v0.2-windows-amd64.zip`, общий `SHA256SUMS` и `release-manifest.json`. Это неизменённый пакет исходного Worker v2026.9.17-rc.1 / commit `3fb03104f8ac39d31a0d338910a504364cfaff2c`.

ZIP включает payload, offline wheelhouse, requirements.lock, WinSW, Python 3.14.7 x64 installer и runtime-скрипты. Git, исходники, сборочные инструменты и доступ к PyPI на целевом сервере не нужны. На Worker 02 передаётся этот же ZIP. Сначала проверить и распаковать его, затем установить включённый Python.

## 3. Проверить и распаковать пакет

```powershell
Set-Location 'C:\Install\worker-release'
$zip = 'prodcast-worker-v0.2-windows-amd64.zip'
$line = Get-Content .\SHA256SUMS | Where-Object { ($_ -split '\s+',2)[1] -eq $zip }
if (@($line).Count -ne 1) { throw 'Нет однозначного checksum ZIP' }
$expected = ($line -split '\s+',2)[0]
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $expected) { throw 'ZIP checksum mismatch' }
$package = 'C:\Install\worker-v2026.9.17-rc.1'
if (Test-Path -LiteralPath $package) { throw 'Распаковывать только в новый каталог' }
Expand-Archive -LiteralPath $zip -DestinationPath $package
Get-ChildItem -LiteralPath $package -Name
```

Должны присутствовать `payload`, `wheelhouse`, `requirements.lock`, `runtime`, `WinSW-x64.exe`, `python-3.14.7-amd64.exe`. Сравнить checksum с доверенной страницей релиза, а не только с файлом из того же непроверенного канала. Репозиторий на целевой машине больше не нужен.

## 3.1. Установить Python 3.14.7 x64

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


## 4. Создать отдельного пользователя службы

```powershell
$svcPassword = Read-Host 'Новый пароль локального prodcast-svc' -AsSecureString
New-LocalUser -Name 'prodcast-svc' -Password $svcPassword -Description 'ProdCast Worker service' -UserMayNotChangePassword
$svcPassword.Dispose()
$account = $env:COMPUTERNAME + '\prodcast-svc'
Get-LocalUser -Name prodcast-svc
Get-LocalGroupMember -SID 'S-1-5-32-544'
```

Сохранить пароль учётной записи в хранилище. Убедиться, что пользователь включён и **не** входит в Administrators. Политику истечения пароля/ротации согласовать с обслуживанием службы: истёкший пароль останавливает её вход.

В `secpol.msc` открыть **Local Policies → User Rights Assignment**:

1. В **Log on as a service** добавить `PC-WORKER-01\prodcast-svc`.
2. Проверить, что пользователь/его группы не входят в **Deny log on as a service**.
3. Добавить пользователя в **Deny log on locally** и **Deny log on through Remote Desktop Services**.
4. Если права задаёт доменная GPO, внести их в соответствующую GPO, применить и проверить результирующую политику.

## 5. Установить службу, пока без запуска

```powershell
$package = 'C:\Install\worker-v2026.9.17-rc.1'
$installDir = 'C:\ProdCast\Worker\v2026.9.17-rc.1'
$python = 'C:\ProdCast\Python314\python.exe'
$account = $env:COMPUTERNAME + '\prodcast-svc'
$cred = Get-Credential -UserName $account -Message 'Пароль созданной учётной записи службы'
& "$package\runtime\Install-Worker.ps1" -InstallDir $installDir -PythonPath $python -WorkerNumber '01' -ServiceCredential $cred
$cred = $null
Get-Service ProdCastWorker01
```

Ожидается `Stopped`, startup Manual. Installer отказывается перезаписывать существующую установку или службу. Он создаёт offline venv с проверкой хешей, защищает каталог, разрешает службе запись только в `logs/jobs/recovery`, настраивает чтение Python/venv из AppContainer и low integrity для jobs. Не заменять эти ACL общим Full Control для Users.

## 6. Заполнить site.json, установить CA и DPAPI-секреты

```powershell
$site = [ordered]@{
    worker_number = '01'
    postgres_host = 'prodcast-db-01.example.internal'
    postgres_port = 5432
    postgres_db = 'prodcast2'
    postgres_user = 'prodcast_worker_01'
    redis_host = 'prodcast-db-01.example.internal'
    redis_port = 6380
    redis_user = 'prodcast_worker_01_scheduler'
    main_server_url = 'https://prodcast-app-01.example.internal'
}
$site | ConvertTo-Json | Set-Content -LiteralPath "$installDir\site.json" -Encoding UTF8
Copy-Item -LiteralPath 'C:\Install\prodcast-inbox\prodcast-db-ca.crt' -Destination "$installDir\prodcast-db-ca.crt"
Copy-Item -LiteralPath 'C:\Install\prodcast-inbox\prodcast-app-ca.crt' -Destination "$installDir\prodcast-app-ca.crt"
& "$package\runtime\Protect-Secrets.ps1" -InstallDir $installDir
& icacls.exe $installDir
& icacls.exe "$installDir\scheduler.machine.dpapi"
```

В четыре защищённых запроса `Protect-Secrets.ps1` ввести:

| Запрос | Значение из хранилища/защищённого комплекта Worker 01 |
|---|---|
| `postgres_password` | `PW_W01` |
| `redis_password` | `REDIS_W01` |
| `media_key` | общий `MEDIA_KEY` App |
| `signing_key` | общий `SIGNING_KEY` App |

Пароль локального `prodcast-svc` сюда **не** вводится. Итоговый `scheduler.machine.dpapi` связан с этой Windows-машиной; его нельзя просто скопировать на Worker 02 или на переустановленный сервер. Его читают только SYSTEM, Administrators и service account; AppContainer не должен читать credentials или payload службы. После сохранения значений в хранилище удалить временный `C:\Install\prodcast-inbox\secrets.json` (точно этот файл) и очистить clipboard, если использовался. Публичные CA оставить.

## 7. Запустить и проверить

```powershell
& "$package\runtime\Start-Worker.ps1" -InstallDir $installDir -WorkerNumber '01'
Get-Service ProdCastWorker01
Get-Content -LiteralPath "$installDir\logs\scheduler-service-ready.json"
Get-CimInstance Win32_Service -Filter "Name='ProdCastWorker01'" | Select-Object Name,State,StartMode,StartName,PathName
Get-ChildItem -LiteralPath "$installDir\logs" | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime,Length
& sc.exe qfailure ProdCastWorker01
```

Ожидается Running под `PC-WORKER-01\prodcast-svc`, свежий marker с `mode=windows-appcontainer`, `postgres_tls=true`, очередями `workflows/workflows_data/scenarios`. Скрипт ждёт проверку AppContainer и PostgreSQL, затем включает delayed automatic start и recovery. Если запуск не прошёл, он останавливает службу и оставляет Manual — исправить причину в защищённых логах, не обходить проверку.

Marker создаётся до окончательной проверки потребления очередей: на App выполнить `celery inspect ping` и `active_queues` из главы 04. Затем провести отдельное выполнение задания с Worker 01 по главе 07.

## 8. Проверка после перезагрузки

В согласованное окно перезагрузить Worker 01. После входа администратора повторить `Get-Service`, проверить свежесть marker/logs, ответ Celery с App и простое задание. Не включать обычные production-расписания до завершения проверки обоих Workers.

**Для акта:** hostname/IP, ZIP SHA256, commit, Python 3.14.7 x64, имя служебного пользователя (без пароля), TLS/AppContainer marker, Celery nodename, ID успешного тестового задания, результат reboot. Далее — Worker 02.
