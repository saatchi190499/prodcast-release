# 07. Приёмка, обслуживание, обновление и откат

## 1. Обязательная функциональная приёмка

Проверки выполнять на тестовых объектах внутри установленного production до допуска обычных пользователей/расписаний. Записать ID объектов и удалить только собственные тестовые данные после проверки.

| Проверка | Действие администратора | Ожидаемый результат |
|---|---|---|
| TLS | открыть App с клиентского ПК; проверить сертификат и срок | доверенная цепочка, правильное DNS-имя, нет исключений браузера |
| Ограничение admin | открыть admin с `.225`, затем с другого клиентского IP | разрешённый компьютер получает форму входа; другой не получает admin UI |
| Вход | войти под администратором, выйти, войти обычным тестовым пользователем | сессия создаётся, роли ограничивают доступ |
| License | проверить decision API и допустимые сессии для согласованных лимитов | active, правильный tenant/лимиты, отказ сверх лимита по логике лицензии |
| Справочники | открыть единицы, типы объектов, источники, встроенные плагины | данные и регистрации присутствуют |
| AI chat | задать короткий вопрос через UI | непустой ответ, без раскрытия service keys в браузере |
| AI notebook | запросить черновик `print(42)` | осмысленный Python, успешный UI-запрос, код не исполняется сам по себе |
| Worker 01 | выполнить отдельное простое серверное Python-задание | SUCCESS, результат/логи, исполнитель Worker 01 |
| Worker 02 | выполнить такое же отдельное задание | SUCCESS, исполнитель Worker 02 |
| Запись результата | тестовый workflow со входными данными и сохранением результата | читается источник, результат доступен в App, нет DB permission denied |
| Scenario | создать простой Python-сценарий с тестовым компонентом и запустить | корректный статус/время/результат, без зависшего RUNNING |
| Расписание | одно тестовое расписание, затем отключить | один запуск за интервал, нет дублей от второго beat |
| Media/подпись | workflow, получающий подготовленный артефакт через App | загрузка по HTTPS, подпись проверена, результат доступен пользователю |
| Reboot | по очереди перезагрузить Workers, AI, App, DB в окно установки | службы вернулись, TLS/очереди/простой workflow работают |
| Backup/restore | восстановить копию в изолированной проверочной среде без внешнего доступа | восстановлены данные и media, повторные задания не отправляются в production |

Для доказательства каждого Worker: при остановленных обычных расписаниях дождаться пустых active/reserved queues, временно остановить **вторую** Windows-службу, выполнить одно тестовое задание, записать hostname исполнителя, вернуть службу. Затем повторить наоборот. Не делать это при реальных выполняющихся заданиях. Два Workers читают общие очереди: два произвольных запуска при обоих включённых не гарантируют, что оба сервера проверены.

Базовый Python-тест: `print("PRODCAST_WORKER_SMOKE_OK")`; в редакторе выбрать серверное Python-выполнение и минимальную корректную конфигурацию входов/выходов. Для проверки записи данных отдельно создать тестовый dataset и конфигурацию результата: один `print` не проверяет SQL INSERT/UPDATE, артефакты и media. Worker-профиль Windows обслуживает Python workflows/scenarios; наличие плагина в каталоге не означает установку PETEX/COM или иных внешних инженерных программ на сервере. Для таких интеграций отдельно установить и лицензировать требуемое ПО и проверить соответствующий workflow.

Проверить отрицательные случаи: запрос AI notebook без X-API-Key → 401; обращение к DB с неразрешённого IP не проходит; Redis без TLS не слушает; неподписанный/повреждённый workflow-артефакт отвергается; service account Workers не администратор. Секреты не включать в протокол.

## 2. Команды диагностики по серверам

### DB

```bash
cd /opt/prodcast/db
dcdb() { docker compose --env-file images.env -f compose.yaml "$@"; }
dcdb ps
dcdb logs --tail=100 postgres redis
dcdb exec -T --user postgres postgres psql -d postgres -c \
 'SELECT a.usename,a.datname,a.client_addr,s.ssl FROM pg_stat_activity a JOIN pg_stat_ssl s USING(pid) WHERE a.client_addr IS NOT NULL;'
dcdb exec redis redis-cli --tls --cacert /etc/prodcast-certs/ca.crt \
 -h 127.0.0.1 -p 6380 --user db_admin --askpass ACL LOG 10
df -h /opt/prodcast/db
```

В `--askpass` используется REDIS_ADMIN. ACL LOG может содержать имена объектов/ключей: хранить вывод в закрытом журнале. Ошибка PostgreSQL `permission denied for table` → проверить DB шаг 8; `no pg_hba.conf entry` → IP/роль/база/TLS; certificate verify failed → CA/SAN/срок, не отключать verify-full.

### AI

```bash
cd /opt/prodcast/ai
docker compose ps
docker compose logs --tail=100 api
systemctl --no-pager status prodcast-ollama
journalctl -u prodcast-ollama -n 100 --no-pager
nvidia-smi
OLLAMA_HOST=127.0.0.1:11434 /opt/ollama/0.34.0/bin/ollama ps
```

AI 401 chat → Basic username/password и scrypt verifier; 401 notebook → общий AI_KEY; 422 → схема запроса и correlation ID; 429 → уже выполняется notebook-запрос; 503 `/readyz` → модель/runtime; 502/504 → ответ/таймаут модели. Увеличение таймаута App выше предела валидатора не исправляет неподходящую модель.

### App и License

```bash
cd /opt/prodcast/app/v0.2/runtime
dc() { docker compose --env-file ../packages.site.env --env-file site.env -f compose.yaml -f site.compose.yaml "$@"; }
dc ps -a
dc logs --tail=100 gateway identity-service integration-service celery-worker celery-beat
dc exec -T celery-worker celery -A mainapp inspect ping --timeout=10
dc exec -T celery-worker celery -A mainapp inspect active --timeout=10
dc exec -T celery-worker celery -A mainapp inspect reserved --timeout=10
dc exec -T celery-worker celery -A mainapp inspect active_queues --timeout=10
docker stats --no-stream
cd /opt/prodcast/license/v2026.9.17-rc.1/runtime
dcl() { docker compose --env-file packages.site.env -f compose.yaml -f site.compose.yaml "$@"; }
dcl ps -a
dcl logs --tail=100 api license-proxy
```

Gateway 502 → состояние конкретного API и upstream; login 403/license denied → tenant, client token и License decision; CSRF failure → точный origin/HTTPS; администратору 403 на admin → фактический клиентский IP и bridge gateway. Если запрос выходит через NAT/VPN, `.225` может не быть IP, видимым nginx; проверить access log и указать действительный разрешённый адрес.

### Каждый Worker

На Worker 01 задать `$workerNumber='01'`, на Worker 02 — `'02'`:

```powershell
$workerNumber = '01'
$name = 'ProdCastWorker' + $workerNumber
$installDir = 'C:\ProdCast\Worker\v2026.9.17-rc.1'
Get-Service -Name $name
Get-CimInstance Win32_Service -Filter "Name='$name'" | Select-Object State,StartName,PathName,ExitCode
Get-Content -LiteralPath "$installDir\logs\scheduler-service-ready.json"
Get-ChildItem -LiteralPath "$installDir\logs" | Sort-Object LastWriteTime -Descending | Select-Object -First 10
Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Service Control Manager';StartTime=(Get-Date).AddHours(-1)} -MaxEvents 30
```

1069/service logon failure → пароль, включённость аккаунта, Log on as a service/GPO; DPAPI decrypt → файл от другой машины или повреждён; AppContainer startup failure → ACL Python/venv/jobs, low integrity, политика ОС; Redis NOPERM → ACL LOG на DB; подпись/скачивание артефакта → MEDIA_KEY, SIGNING_KEY, App CA и URL. При чтении логов не раскрывать credentials в отчёте.

## 3. Резервная копия перед обновлением

Резервирование должно включать **согласованный набор**: три PostgreSQL DB, Redis, media, приватные env/ключи/CA, лицензии и токены, Worker config/recovery, точные образы/ZIP, Ollama runtime и модель. Docker image или snapshot одной VM без DB/media не является полной резервной копией.

### 3.1. Остановить запись и зафиксировать окно

1. Объявить техническое окно и закрыть пользовательский вход на сетевом уровне.
2. На App остановить `celery-beat`, отключить тестовые/обычные расписания.
3. Проверить `active`, `reserved`, `scheduled` через Celery inspect; дождаться завершения реальных заданий. Не убивать процессы для ускорения: Windows runner использует раннее подтверждение и не обещает автоматический повтор частично выполненного задания.
4. После остановки поступления задач проверить очереди Redis; при наличии заданий либо корректно дождаться обработки, либо зафиксировать отдельный план их сохранения/возобновления. Не использовать `FLUSHALL`.
5. Остановить App и License, затем обе Windows-службы и AI API. PostgreSQL остаётся запущенным для dump.

Команды на App из соответствующих runtime-каталогов:

```bash
dc stop celery-beat
dc exec -T celery-worker celery -A mainapp inspect scheduled --timeout=10
# После завершения заданий и ограничения пользовательского доступа:
dc stop
```

Отдельно в License runtime: `dcl stop`. На Workers: `Stop-Service ProdCastWorker01` / `Stop-Service ProdCastWorker02`. На AI: `cd /opt/prodcast/ai` и `docker compose stop`.

### 3.2. DB — создать dumps и копию Redis

```bash
sudo -i
set -euo pipefail
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup=/var/backups/prodcast/$stamp
install -d -m 0700 "$backup"
cd /opt/prodcast/db
dcdb() { docker compose --env-file images.env -f compose.yaml "$@"; }
for db in prodcast2 license_db prodcast_ai; do
  dcdb exec -T --user postgres postgres pg_dump -Fc -d "$db" > "$backup/$db.dump"
  test -s "$backup/$db.dump"
  dcdb exec -T --user postgres postgres pg_restore --list < "$backup/$db.dump" > "$backup/$db.contents.txt"
done
dcdb exec -T --user postgres postgres pg_dumpall --globals-only > "$backup/globals.sql"
dcdb stop redis
tar --numeric-owner -czf "$backup/redis-data.tar.gz" -C /opt/prodcast/db/data redis
tar --numeric-owner -czf "$backup/db-config-private.tar.gz" -C /opt/prodcast/db config certs compose.yaml images.env
cd "$backup"
sha256sum *.dump *.sql *.tar.gz > SHA256SUMS
```

`globals.sql` содержит hashes паролей, config archive — приватные ключи. Хранить encrypted/off-host, права 0600/0700. `pg_restore --list` проверяет читаемость dump, но не заменяет тест восстановления. Пока копируются остальные серверы, запись не возобновлять.

### 3.3. App — media, конфигурации и License

```bash
sudo -i
set -euo pipefail
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup=/var/backups/prodcast/$stamp
install -d -m 0700 "$backup"
source /opt/prodcast/app/v0.2/packages.site.env
docker run --rm --network none --user 0 --entrypoint tar \
  -v prodcast-app-media-data:/data:ro -v "$backup:/backup" \
  "$PRODCAST_BACKEND_IMAGE" -czf /backup/app-media.tar.gz -C /data .
tar -czf "$backup/app-license-private.tar.gz" -C /opt/prodcast app license
cp /root/prodcast-platform-versions.txt "$backup/"
```

Сохранить также исходные App-архивы и поставляемый License image. Статика пересобирается collectstatic из того же backend image; media содержит пользовательские данные и должна восстанавливаться синхронно с DB.

### 3.4. AI

Остановить `prodcast-ollama`, архивировать `/opt/prodcast/ai`, `/etc/systemd/system/prodcast-ollama.service`, `/var/lib/prodcast-ai/models`; сохранить Ollama `.tar.zst`, image AI `.tar.gz`, model digest и версии драйвера. Модельные blobs могут быть большими; обеспечить место и checksum. При обычном резервировании без изменения модели допустимо хранить одну подтверждённую неизменяемую копию blobs с manifest и ссылкой на неё в акте.

### 3.5. Каждый Worker

При остановленной службе сделать защищённую резервную копию текущего install directory, включая `site.json`, `scheduler.machine.dpapi`, `logs`, `recovery`, XML WinSW, публичные CA и package manifest; сохранить сведения `sc.exe qc` и `sc.exe qfailure`. Для восстановления на другой Windows-машине нужны исходные секреты из хранилища и новая генерация DPAPI. Копия одного `scheduler.machine.dpapi` переносимость не обеспечивает.

### 3.6. Завершение

Связать копии общим номером окна/версией и временем остановки записи. Передать в зашифрованное внешнее хранилище, проверить контрольные суммы и тестовое восстановление. Если обновление не проводится, включить DB Redis → License → AI/Ollama → App без beat → Workers → проверки → единственный beat → пользовательский доступ.

## 4. Обновление по серверам

**Для обновления v0.2 поверх существующей установки** сначала инвентаризировать старые образы, схему БД, secrets и services. Шаги «создать роли», «генерировать секреты», `init_data`, `load_units`, создание License company/token не выполняются повторно. Новые версии компонентов выбирать как совместимый комплект, не по отдельному названию `latest`.

### DB

Обновление приложения само по себе не требует обновлять PostgreSQL/Redis. Сначала сохранить текущие pinned images, проверить свободное место и backup. PostgreSQL minor/major upgrade проводить по процедуре PostgreSQL; для major нельзя просто подключить существующий data directory к новому major image. В этом руководстве сервер остаётся на зафиксированной инфраструктурной версии.

### AI

Получить и проверить image нового согласованного релиза, сохранить архив/hash, скопировать текущие приватные настройки в новую версию runtime, изменить только согласованные параметры. Сохранить прежние image и модель. Если меняется Ollama — распаковать в новый `/opt/ollama/<version>`, изменить ExecStart, выполнить daemon-reload; не перезаписывать старый binary directory. Проверить GPU, readiness, chat, notebook и ограничения времени до переключения App.

### License и App

1. Проверить новые архивы, распаковать в новые version directories.
2. Перенести **существующие** env, TLS и ключи; сверить новые обязательные параметры с release templates. Сохранить LICENSE_SALT, client token, Django/Fernet/media/signing keys.
3. В новом App `packages.site.env` указать новые проверенные образы, сохранить одинаковые именованные volumes и external network.
4. В окно из раздела 3 выполнить License/App migrations **один раз**. При ошибке остановиться, не запускать разные версии API с частично изменённой схемой.
5. Поднять License и App без beat, проверить readiness, UI и данные.
6. При изменении Worker schema requirements выдать только необходимые новые права DB после проверки миграций.
7. Обновить Workers, проверить функциональность, включить единственный beat и пользовательский доступ.

### Windows Worker — на каждом сервере отдельно

Установщик исходного релиза не имеет режима in-place upgrade и отказывается работать при существующей службе. Безопасный ручной порядок после завершения заданий:

1. Сохранить старый install directory, данные, параметры службы и пароль service account.
2. Распаковать новый проверенный ZIP в новый package directory, подготовить требуемую им точную Python-версию в отдельном каталоге.
3. Остановить службу и удалить **только регистрацию службы**, сохранив старые файлы. Для Worker 01: `Stop-Service ProdCastWorker01`, затем `sc.exe delete ProdCastWorker01`; для Worker 02 — соответствующее имя. Закрыть Services.msc и проверить исчезновение службы; иногда требуется дождаться освобождения открытого handle.
4. Запустить `Install-Worker.ps1` нового пакета с новым `-InstallDir`, соответствующим `-WorkerNumber` и тем же non-admin аккаунтом.
5. Перенести `site.json`, публичные CA; на той же Windows-машине допустимо перенести DPAPI-файл, сохранив ограниченные ACL. На новой машине — создать его заново из хранилища.
6. Данные `recovery` переносить только согласно совместимости новой версии, не копировать старый venv/payload поверх нового. Сохранить их резервную копию до завершения приёмки.
7. Запустить `Start-Worker.ps1` нового пакета, проверить AppContainer, DB TLS, очереди, отдельное задание, затем второй сервер.

Не удалять старые каталоги/образы до окончания согласованного срока отката. При невозможности обновлять Workers последовательно использовать полное техническое окно; не допускать несовместимые consumer и App к общим очередям.

## 5. Откат

### Если схема и данные не изменены

Остановить beat и поступление задач, дождаться завершения активных. Остановить новые App/AI/License/Worker, вернуть прежние `packages.site.env`, runtime/config и службы. Поднять старый совместимый комплект по порядку запуска. Проверить DB/Redis/TLS, UI, каждый Worker, затем beat. Не делать одновременно `up` из двух каталогов одного Compose project с разными конфигурациями.

Для Windows после удаления регистрации новой службы восстановить старую из повышенной PowerShell; пример Worker 01:

```powershell
$name = 'ProdCastWorker01'
$oldDir = 'C:\ProdCast\Worker\v2026.9.17-rc.1'
$cred = Get-Credential -UserName ($env:COMPUTERNAME+'\prodcast-svc') -Message 'Восстановление старой службы'
New-Service -Name $name -BinaryPathName ('"'+(Join-Path $oldDir ($name+'.exe'))+'"') -StartupType Manual -Credential $cred -DependsOn @('Tcpip','Eventlog')
$cred = $null
& 'C:\Install\worker-v2026.9.17-rc.1\runtime\Start-Worker.ps1' -InstallDir $oldDir -WorkerNumber '01'
```

На Worker 02 использовать имя/номер 02. Старый XML должен указывать на существующий прежний Python/venv. Эта команда рассчитана на отсутствие зарегистрированной службы с тем же именем.

### Если были миграции или записи нового формата

Простого переключения image недостаточно. Нужен согласованный snapshot/dump **до обновления** и восстановление согласованных DB + media + конфигурации + состояния очередей. Записи после точки восстановления будут потеряны: выбрать точку восстановления и зафиксировать это до действий.

1. Полностью остановить запись: beat, App, License, Workers, AI; ограничить пользовательский доступ.
2. Сделать отдельную копию состояния после сбоя для анализа. Проверить SHA256 выбранного backup.
3. На DB восстановить каждую БД в очищенную базу с правильным владельцем. Пример ниже **удаляет текущую prodcast2**; применять только в согласованном откате, с проверенным backup и остановленными клиентами:

```bash
cd /opt/prodcast/db
dcdb() { docker compose --env-file images.env -f compose.yaml "$@"; }
# Указать реальный каталог выбранной резервной копии:
backup=/var/backups/prodcast/REPLACE_WITH_BACKUP_TIMESTAMP
test -s "$backup/prodcast2.dump"
dcdb exec -T --user postgres postgres dropdb prodcast2
dcdb exec -T --user postgres postgres createdb -O prodcast_app prodcast2
dcdb exec -T --user postgres postgres pg_restore --exit-on-error -d prodcast2 < "$backup/prodcast2.dump"
dcdb exec -T --user postgres postgres psql -v ON_ERROR_STOP=1 -d postgres <<'SQL'
REVOKE ALL ON DATABASE prodcast2 FROM PUBLIC;
GRANT CONNECT ON DATABASE prodcast2 TO prodcast_app,prodcast_worker_01,prodcast_worker_02;
SQL
```

Восстановить `license_db` с owner `license_app`, `prodcast_ai` с owner `prodcast_ai` тем же порядком drop/create/restore при необходимости согласованного отката. Сохранённые роли/пароли должны совпадать с восстановленными env. Dump содержит object grants; дополнительно проверить DB шаг 8. Если `dropdb` сообщает активные подключения — найти неостановленный клиент, не добавлять FORCE без проверки.

4. На чистом PostgreSQL-хосте сначала восстановить необходимые роли из `globals.sql` с проверкой конфликтов уже существующих системных ролей; не проигрывать его вслепую поверх действующего кластера. Затем базы/dumps и их CONNECT ACL.
5. На App вернуть media из соответствующего `app-media.tar.gz` в отдельный пустой volume, проверить содержимое и владельцев, переключить `media_data.name` в site override на этот восстановленный volume. Не распаковывать поверх нового media с удалёнными/изменёнными файлами: получится смесь состояний.
6. Redis: при остановленном Redis сохранить текущий data directory отдельно, восстановить **весь** `redis-data.tar.gz` в новый пустой каталог с прежним владельцем, переключить bind mount. AOF multipart требует manifest и все относящиеся файлы. До запуска consumer проверить, что очередь из точки backup не приведёт к повтору уже выполненных внешних действий. Если очереди были пустыми по протоколу окна, зафиксировать это.
7. Вернуть старые App/License/AI images, env/ключи, модель, Worker службы и подходящие recovery data.
8. Поднять PostgreSQL/Redis → License → Ollama/AI → App без beat → Workers. Проверить UI, данные, media, каждое тестовое задание. Только затем beat и доступ пользователей.

Все команды restore сначала отработать на отдельной изолированной машине с копией данных; это проверка резервной копии, а не создание второго работающего production-контура. Не подключать проверочное восстановление к production Redis/лицензиям/внешним системам.

## 6. Регулярное обслуживание

Назначить владельца backup и проверить автоматическое расписание резервирования отдельной задачей: эта инструкция не создаёт scheduler для backups. Установить сроки хранения по требованиям площадки; отслеживать свободное место DB/media/models/logs, возраст успешной копии, истечение TLS за 30 дней, доступность License/AI/Workers, возраст очередей и ошибки заданий. Пересматривать ресурсы после измерения нагрузки.

TLS renewal: выпустить leaf с теми же SAN, проверить `openssl verify`, заменить `.crt/.key` с прежними владельцами/правами, перезапустить только соответствующий сервис в окно; при смене CA сначала распространить доверие клиентам, потом менять leaf. Не перегенерировать все secrets ради смены сертификата.

Ротация signing/media/DB/Redis keys требует согласованной смены соответствующих сторон из таблицы главы 01. У Worker штатный `Protect-Secrets.ps1` не перезаписывает существующий файл: при остановленной службе сохранить старый DPAPI-файл под другим именем в закрытом backup, создать новый, запустить и проверить; старый удалить после приёмки ротации. Смена LICENSE_SALT и Fernet key — не обычная ротация пароля, может потребовать миграции существующих токенов/данных.

## 7. Шаблон журнала администратора

Заполнить на каждый сервер отдельно и приложить к акту:

```text
Номер изменения / окно:
Администратор:
Дата и время UTC начала / окончания:
Сервер / IP / роль:
ОС / версия Docker+Compose либо Python:
Компонент / tag / commit / image ID / SHA256 архива:
Для AI: Ollama / GPU driver / model tag + digest:
Конфигурации и каталоги (без секретных значений):
Имена учётных записей и идентификатор записи в хранилище секретов:
TLS: issuer / SAN / fingerprint / notAfter:
Выполненные шаги документа:
Миграции / результат / время:
Health/readiness / TLS-проверка:
Тестовый workflow/scenario ID / исполнитель / результат:
Проверка перезагрузки:
Backup ID / checksum / место хранения / дата тестового restore:
Версия и порядок отката:
Отклонения и оставшиеся замечания:
Решение о допуске в эксплуатацию / ответственный:
```

Приёмка считается завершённой после успешных функциональных проверок, подтверждённого восстановления backup и заполнения журнала. Одного `docker compose ps` или Running у Windows-службы недостаточно.
