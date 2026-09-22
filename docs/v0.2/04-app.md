# 04. Сервер App — 192.0.2.23

Рабочее место: `prodcast-app-01.example.internal`, root Bash. Выполнены глава 01 и настройка DB; AI уже прошёл проверку. Здесь устанавливается также License, потому что App использует его для контроля доступа.

## 1. Проверить и распаковать App

```bash
sudo -i
set -euo pipefail
umask 077
cd /srv/prodcast-dist/v0.2
sha256sum -c SHA256SUMS
test ! -e /opt/prodcast/app/v0.2
install -d -m 0755 /opt/prodcast/app/v0.2
tar -xzf prodcast-app-v0.2-deployment.tar.gz -C /opt/prodcast/app/v0.2
docker load -i prodcast-backend-v0.2-linux-amd64.tar.gz
docker load -i prodcast-frontend-v0.2-linux-amd64.tar.gz
docker load -i prodcast-gateway-v0.2-linux-amd64.tar.gz
cd /opt/prodcast/app/v0.2
cp packages.offline.env packages.site.env
while IFS='=' read -r key ref; do
  docker image inspect "$ref" --format '{{.Os}}/{{.Architecture}} {{.Id}}'
done < packages.site.env
```

Ожидаются три `linux/amd64` образа с transport tags `v2026.9.19-rc.1`. Это корректно для дистрибутива v0.2. Не менять их на несуществующий registry tag `v0.2`. Основная проверка полученных файлов — SHA256 архивов; registry digest, config digest и `.Id` в разных Docker image stores могут иметь разную семантику. Если сравниваете `images.json.image_id`, сравнивать с SHA256 **config JSON в Docker archive**, а не автоматически с digest manifest/containerd. Несовпадение checksum архива — остановка установки.

При наличии доступа к registry можно вместо `docker load` использовать `packages.env` с digest references и `docker compose pull`; в этой инструкции последовательно используется комплект архивов и `--pull never`.

## 2. Создать общую сеть и подготовить сертификаты

Убедиться по `ip route` и `docker network ls/inspect`, что подсеть `172.30.23.0/24` свободна. На первичной установке:

```bash
docker network create --driver bridge --subnet 172.30.23.0/24 \
  --gateway 172.30.23.1 prodcast-app-default
cd /opt/prodcast/app/v0.2/runtime
install -d -m 0755 certs certs/upstream-ca
install -m 0644 /root/prodcast-inbox/site.crt certs/site.crt
install -m 0600 /root/prodcast-inbox/site.key certs/site.key
install -m 0644 /root/prodcast-inbox/ca.crt certs/db-ca.crt
install -m 0644 /root/prodcast-inbox/ca.crt certs/ai-ca.crt
install -m 0644 /root/prodcast-inbox/ca.crt certs/license-ca.crt
install -m 0644 /root/prodcast-inbox/ca.crt certs/upstream-ca/prodcast-ca.crt
source ../packages.site.env
docker run --rm --network none --entrypoint cat "$PRODCAST_BACKEND_IMAGE" \
  /etc/ssl/certs/ca-certificates.crt > certs/requests-ca-bundle.crt
cat certs/db-ca.crt certs/ai-ca.crt certs/license-ca.crt >> certs/requests-ca-bundle.crt
chmod 0644 certs/requests-ca-bundle.crt
```

Для разных корпоративных CA использовать соответствующие файлы, не копировать один CA вслепую. `site.key` читает root-процесс gateway; backend получает только права чтения публичных CA. Совместный `requests-ca-bundle.crt` сохраняет системные корни для других HTTPS-запросов и добавляет внутренние.

## 3. Загрузить готовый License

```bash
cd /srv/prodcast-dist/v0.2
sha256sum -c SHA256SUMS
docker load -i prodcast-license-v0.2-linux-amd64.tar.gz
test ! -e /opt/prodcast/license/v2026.9.17-rc.1/runtime/compose.yaml
install -d -m 0755 /opt/prodcast/license/v2026.9.17-rc.1
tar -xzf prodcast-license-v0.2-deployment.tar.gz -C /opt/prodcast/license/v2026.9.17-rc.1
docker image inspect ghcr.io/saatchi190499/prodcast-license:v2026.9.17-rc.1 > /root/prodcast-license-image.json
cd /opt/prodcast/license/v2026.9.17-rc.1/runtime
install -d -m 0755 certs
source /root/prodcast-inbox/secrets.env
install -m 0644 /root/prodcast-inbox/ca.crt certs/db-ca.crt
install -m 0644 /root/prodcast-inbox/license.crt certs/license.crt
install -m 0600 /root/prodcast-inbox/license.key certs/license.key
cat > runtime.env <<EOF
DATABASE_URL=postgresql+psycopg://license_app:${PW_LICENSE}@prodcast-db-01.example.internal:5432/license_db?sslmode=verify-full&sslrootcert=/etc/prodcast/certs/db-ca.crt
TOKEN_HASH_SALT=${LICENSE_SALT}
ADMIN_BOOTSTRAP_TOKEN=${LICENSE_BOOTSTRAP}
ADMIN_BOOTSTRAP_TOKEN_NAME=bootstrap-admin
AUTO_MIGRATE=false
ENABLE_API_DOCS=false
JSON_LOGS=true
LOG_DIR=/app/logs
LOG_LEVEL=INFO
EOF
chmod 0600 runtime.env
source /opt/prodcast/app/v0.2/packages.site.env
printf 'PRODCAST_LICENSE_IMAGE=ghcr.io/saatchi190499/prodcast-license:v2026.9.17-rc.1\nPRODCAST_GATEWAY_IMAGE=%s\n' \
  "$PRODCAST_GATEWAY_IMAGE" > packages.site.env
```

Image и зависимости уже внутри поставки. Исходный License tag остаётся `v2026.9.17-rc.1`. Для новой установки используется исходный Compose пакета плюс site override ниже.

## 4. Настроить HTTPS между App и License, выполнить миграции License

Создать два файла на App в `/opt/prodcast/license/v2026.9.17-rc.1/runtime`:

```bash
cat > nginx.conf <<'EOF'
events {}
http {
  server {
    listen 8443 ssl;
    server_name license-proxy;
    ssl_certificate /etc/prodcast/certs/license.crt;
    ssl_certificate_key /etc/prodcast/certs/license.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    location / {
      proxy_pass http://api:8100;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
  }
}
EOF
chmod 0644 nginx.conf
cat > site.compose.yaml <<'EOF'
services:
  license-proxy:
    image: ${PRODCAST_GATEWAY_IMAGE:?}
    entrypoint: [nginx]
    command: [-c, /etc/nginx/nginx.conf, -g, 'daemon off;']
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/prodcast/certs:ro
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
networks:
  default:
    external: true
    name: prodcast-app-default
EOF
dcl() { docker compose --env-file packages.site.env -f compose.yaml -f site.compose.yaml "$@"; }
dcl config --quiet
dcl run --rm --pull never migrate
dcl up -d --pull never --wait --wait-timeout 180 api license-proxy
dcl ps -a
curl --fail http://127.0.0.1:8100/readyz
```

`migrate` завершается кодом 0, `api` healthy. Loopback HTTP нужен для локального администрирования; межсервисный App URL будет `https://license-proxy:8443/v1/decision`. Proxy не публикует порт на хост и использует App gateway image только как установленный nginx.

## 5. Создать запись компании и client token License

До команды записать согласованные `tenant_id`, название, число одновременных пользователей, число сессий и срок действия. Пример ниже использует tenant `prodcast-production`, 5 пользователей, 1 сессию; это **пример параметров**, а не предоставление лицензии. Заменить их утверждёнными значениями; тот же tenant затем указать в App. При ограниченном сроке добавить `expires_at` в ISO 8601 UTC.

```bash
cd /opt/prodcast/license/v2026.9.17-rc.1/runtime
python3 - <<'PY'
import json, pathlib, urllib.request
p = pathlib.Path('runtime.env')
env = dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)
base = 'http://127.0.0.1:8100'
headers = {'Authorization':'Bearer '+env['ADMIN_BOOTSTRAP_TOKEN'],'Content-Type':'application/json'}
company = {'tenant_id':'prodcast-production','company_name':'ProdCast',
 'status':'active','max_concurrent_users':5,'max_sessions_per_user':1}
req = urllib.request.Request(base+'/admin/companies',data=json.dumps(company).encode(),headers=headers)
with urllib.request.urlopen(req,timeout=15) as r:
 print('Company created:',r.status)
body = {'token_name':'production-app','token_type':'client','allowed_tenant_id':company['tenant_id']}
req = urllib.request.Request(base+'/admin/tokens',data=json.dumps(body).encode(),headers=headers)
with urllib.request.urlopen(req,timeout=15) as r:
 result = json.load(r)
target = pathlib.Path('/root/prodcast-inbox/license-client.json')
target.write_text(json.dumps(result,indent=2)+'\n'); target.chmod(0o600)
print('Client token saved to protected file; token ID:',result['meta']['id'])
PY
```

Сохранить token в хранилище секретов. Не повторять этот блок при обновлении: используйте существующую компанию и client token. Если ответ конфликт/ошибка, прочитать существующую запись через `/admin/companies/{tenant_id}` с admin token и разобраться; не создавать новые токены циклом. App получает **client** token, не bootstrap/admin token.

## 6. Создать полную конфигурацию App

```bash
cd /opt/prodcast/app/v0.2/runtime
source /root/prodcast-inbox/secrets.env
cat > site.env <<'EOF'
PRODCAST_PUBLIC_URL=https://prodcast-app-01.example.internal
PRODCAST_ADMIN_CLIENT_IP=192.0.2.225
PRODCAST_ADMIN_DOCKER_GATEWAY_IP=172.30.23.1
MODEL_STORAGE_ENABLED=false
NODEALL_ENABLED=false
NODEALL_BASE_URL=https://disabled.example.invalid
EOF
cat > site.compose.yaml <<'EOF'
networks:
  default:
    external: true
    name: prodcast-app-default
EOF
cat > runtime.env <<EOF
PRODCAST_PUBLIC_URL=https://prodcast-app-01.example.internal
DJANGO_SECRET_KEY=${DJANGO_KEY}
DJANGO_DEBUG=false
DJANGO_TIME_ZONE=UTC
DJANGO_ALLOWED_HOSTS=prodcast-app-01.example.internal,192.0.2.23,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://prodcast-app-01.example.internal
CSRF_TRUSTED_ORIGINS=https://prodcast-app-01.example.internal
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_ALL_ORIGINS=false
PRODCAST_ALLOW_INSECURE_BROWSER_ORIGINS=false
JWT_COOKIE_SECURE=true
JWT_COOKIE_SAMESITE=Lax
CSRF_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SAMESITE=Lax
DJANGO_SECURE_SSL_REDIRECT=true
EXTERNAL_SOURCE_CREDENTIAL_KEY=${FERNET_KEY}
POSTGRES_HOST=prodcast-db-01.example.internal
POSTGRES_PORT=5432
POSTGRES_DB=prodcast2
POSTGRES_USER=prodcast_app
POSTGRES_PASSWORD=${PW_APP}
PGSSLMODE=verify-full
PGSSLROOTCERT=/etc/prodcast/certs/db-ca.crt
DATABASE_URL=postgresql://prodcast_app:${PW_APP}@prodcast-db-01.example.internal:5432/prodcast2?sslmode=verify-full&sslrootcert=/etc/prodcast/certs/db-ca.crt
REDIS_PASSWORD=${REDIS_APP}
REDIS_URL=rediss://prodcast_app:${REDIS_APP}@prodcast-db-01.example.internal:6380/0?ssl_cert_reqs=required&ssl_ca_certs=%2Fetc%2Fprodcast%2Fcerts%2Fdb-ca.crt
CELERY_BROKER_URL=rediss://prodcast_app:${REDIS_APP}@prodcast-db-01.example.internal:6380/0?ssl_cert_reqs=required&ssl_ca_certs=%2Fetc%2Fprodcast%2Fcerts%2Fdb-ca.crt
CELERY_RESULT_BACKEND=rediss://prodcast_app:${REDIS_APP}@prodcast-db-01.example.internal:6380/1?ssl_cert_reqs=required&ssl_ca_certs=%2Fetc%2Fprodcast%2Fcerts%2Fdb-ca.crt
CHANNEL_REDIS_URL=rediss://prodcast_app:${REDIS_APP}@prodcast-db-01.example.internal:6380/0?ssl_cert_reqs=required&ssl_ca_certs=%2Fetc%2Fprodcast%2Fcerts%2Fdb-ca.crt
MODEL_STORAGE_ENABLED=false
MODEL_STORAGE_URL=
MODEL_STORAGE_API_KEY=
NODEALL_ENABLED=false
NODEALL_BASE_URL=https://disabled.example.invalid
NODEALL_API_KEY=
INTEGRATION_MODULE_API_KEY=${MODULE_KEY}
RESOLVE_API_KEY=${RESOLVE_KEY}
MEDIA_DOWNLOAD_API_KEY=${MEDIA_KEY}
WORKFLOW_ARTIFACT_SIGNING_KEY=${SIGNING_KEY}
WORKFLOW_ARTIFACT_SIGNING_REQUIRED=true
MEDIA_ACCEL_REDIRECT_ENABLED=true
MEDIA_ACCEL_REDIRECT_PREFIX=/internal-media/
METRICS_API_KEY=${METRICS_KEY}
PRODCAST_CELERY_MONITORED_QUEUES=default,scenarios,workflows,workflows_data
WORKFLOW_MODEL_QUEUE=workflows
WORKFLOW_DATA_QUEUE=workflows_data
WORKFLOW_QUOTA_ENFORCEMENT_ENABLED=true
WORKFLOW_GLOBAL_ACTIVE_RUN_LIMIT=20
WORKFLOW_USER_ACTIVE_RUN_LIMIT=2
WORKFLOW_SINGLE_WORKFLOW_ACTIVE_RUN_LIMIT=1
WORKFLOW_QUEUE_ACTIVE_RUN_LIMITS=workflows=10,workflows_data=5
DJANGO_JSON_LOGS=true
REQUIRE_TLS_FOR_REMOTE_SERVICES=true
ALLOW_INSECURE_INTERNAL_HTTP=false
ALLOW_INSECURE_TLS_VERIFY=false
REQUESTS_CA_BUNDLE=/etc/prodcast/certs/requests-ca-bundle.crt
PRODCAST_AI_ENABLED=true
PRODCAST_AI_BASE_URL=https://prodcast-ai-01.example.internal:8443
PRODCAST_AI_API_KEY=${AI_KEY}
PRODCAST_AI_BASIC_AUTH_USERNAME=prodcast-app
PRODCAST_AI_BASIC_AUTH_PASSWORD=${AI_BASIC}
PRODCAST_AI_CA_BUNDLE=/etc/prodcast/certs/ai-ca.crt
PRODCAST_AI_TIMEOUT_SECONDS=120
PRODCAST_AI_CHAT_TIMEOUT_SECONDS=120
PRODCAST_AI_CONNECT_TIMEOUT_SECONDS=5
PRODCAST_AI_VERIFY_TLS=true
LICENSE_ENFORCEMENT_ENABLED=true
LICENSE_TENANT_ID=prodcast-production
LICENSE_SERVICE_URL=https://license-proxy:8443/v1/decision
LICENSE_SERVICE_FAIL_OPEN=false
LICENSE_SERVICE_TIMEOUT_SECONDS=5
LICENSE_SERVICE_CACHE_TTL_SECONDS=60
AUTH_MICROSOFT_ENABLED=false
AUTH_LDAP_SERVER_URI=
EXTERNAL_SOURCE_ALLOWED_HOSTS=
PI_WEB_API_BASE_URL=
EOF
python3 - <<'PY'
import json, pathlib
token = json.loads(pathlib.Path('/root/prodcast-inbox/license-client.json').read_text())['token']
assert token and '\n' not in token and '\r' not in token
with pathlib.Path('runtime.env').open('a') as f:
 f.write('LICENSE_SERVICE_TOKEN='+token+'\n')
PY
chmod 0600 runtime.env site.env
dc() { docker compose --env-file ../packages.site.env --env-file site.env -f compose.yaml -f site.compose.yaml "$@"; }
dc config --quiet
```

Если tenant в шаге 5 изменён, изменить `LICENSE_TENANT_ID`. Ключи в URLs созданы hex, дополнительное URL-encoding им не нужно. Для иных паролей экранировать URL-компоненты. `POSTGRES_HOST/PORT` обязательны даже при `DATABASE_URL`: их использует ожидание DB в entrypoint.

Два уровня конфигурации обязательны: `site.env` подставляется в Compose, `runtime.env` передаётся процессам. В частности, `MODEL_STORAGE_ENABLED/NODEALL_ENABLED` должны быть false в обоих, иначе Compose переопределит настройки процесса. Во frontend/`VITE_*` ключи и пароли не добавлять.

## 7. Проверить соединения до миграций

Проверка непосредственно из backend image с теми же mounts, environment и Docker network:

```bash
dc run --rm --no-deps --pull never -T --entrypoint python admin-service - <<'PY'
import os, psycopg2, redis, requests
with psycopg2.connect(os.environ['DATABASE_URL'],connect_timeout=5) as conn:
 with conn.cursor() as cur:
  cur.execute('SELECT current_user,ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
  print('PostgreSQL:',cur.fetchone())
print('Redis:',redis.Redis.from_url(os.environ['CELERY_BROKER_URL']).ping())
license = requests.get(os.environ['LICENSE_SERVICE_URL'],
 params={'tenant_id':os.environ['LICENSE_TENANT_ID']},
 headers={'Authorization':'Bearer '+os.environ['LICENSE_SERVICE_TOKEN']},timeout=10)
license.raise_for_status(); print('License:',license.json())
ai = requests.get(os.environ['PRODCAST_AI_BASE_URL']+'/readyz',
 headers={'X-API-Key':os.environ['PRODCAST_AI_API_KEY']},
 verify=os.environ['PRODCAST_AI_CA_BUNDLE'],timeout=120)
ai.raise_for_status(); print('AI:',ai.json())
PY
```

Ожидается `('prodcast_app', True)`, Redis True, License active с согласованными лимитами, AI ready. Не продолжать при неработающей лицензии/TLS/БД. При License 502 сначала проверить `dcl logs api license-proxy`; при DNS error — разрешение DB/AI и Docker alias `license-proxy`.

## 8. Миграции и первоначальные данные

```bash
dc run --rm --pull never migrate
dc run --rm --no-deps --pull never --entrypoint python admin-service manage.pyc showmigrations --plan
dc run --rm --no-deps --pull never --entrypoint python admin-service manage.pyc init_data
dc run --rm --no-deps --pull never --entrypoint python admin-service manage.pyc load_units
dc run --rm --no-deps --pull never --entrypoint python admin-service manage.pyc sync_integration_plugins --package prodcast-petex-plugins
dc run --rm --no-deps --pull never --entrypoint python admin-service manage.pyc createsuperuser
```

Все команды должны завершиться кодом 0; применённые миграции отмечены `[X]`. `migrate` также собирает статику, а `RUN_BOOTSTRAP_DATA=0` не запускает первичное заполнение автоматически. `init_data`, `load_units` и регистрация пакета выполняются здесь явно **для новой базы**. Проверить состав справочников с владельцем системы. `createsuperuser` запрашивает имя/email/пароль интерактивно; сохранить пароль в хранилище. Не задавать его в командной строке.

Если получена ошибка записи media/static, проверить владельца runtime image и volumes; не выдавать `chmod 777`. Контейнеры должны писать только свои каталоги. Нельзя исправлять ошибку миграций удалением PostgreSQL data или Docker volumes.

## 9. Запустить App без планировщика и проверить

```bash
dc up -d --no-build --pull never --wait --wait-timeout 240 \
  gateway frontend admin-service identity-service catalog-service data-service \
  workflow-service scenario-service analytics-service integration-service celery-worker
dc ps -a
dc logs --tail=80 gateway admin-service integration-service celery-worker
curl --fail --cacert certs/db-ca.crt https://prodcast-app-01.example.internal/healthz
curl --fail --cacert certs/db-ca.crt https://prodcast-app-01.example.internal/readyz
curl -I http://prodcast-app-01.example.internal/
dc exec -T admin-service python manage.pyc check --deploy
```

Ожидается HTTP 200 для health/readiness, HTTP→HTTPS redirect и healthy у сервисов. Замечания `check --deploy` разобрать до приёмки; не менять TLS/security флаги на false для обхода. С административного ПК открыть HTTPS App, войти созданным пользователем, проверить справочники и страницу администрирования. Админ-путь доступен только `PRODCAST_ADMIN_CLIENT_IP`; обычный UI — клиентам площадки.

Проверить chat непосредственно из App:

```bash
dc exec -T integration-service python - <<'PY'
import os,requests
r = requests.post(os.environ['PRODCAST_AI_BASE_URL']+'/api/chat',
 auth=(os.environ['PRODCAST_AI_BASIC_AUTH_USERNAME'],os.environ['PRODCAST_AI_BASIC_AUTH_PASSWORD']),
 verify=os.environ['PRODCAST_AI_CA_BUNDLE'],json={'message':'Reply with OK only.'},timeout=120)
r.raise_for_status(); answer=r.json()
assert answer.get('answer'); print('AI chat passed; response contains answer.')
PY
```

Теперь выполнить DB шаг 8 и обе главы Workers. До этого не включать расписания. Docker-публикации 80/443 не защищаются одним UFW INPUT: публичную доступность ограничивать сетью площадки или правилами Docker forwarding. Gateway уже ограничивает admin IP; проверить это с разрешённого и другого клиентского ПК. Порт App 8443 опубликован только на loopback для административного доступа.

## 10. Запустить единственный планировщик

После успешного запуска Worker 01 и Worker 02:

```bash
cd /opt/prodcast/app/v0.2/runtime
dc() { docker compose --env-file ../packages.site.env --env-file site.env -f compose.yaml -f site.compose.yaml "$@"; }
dc up -d --no-build --pull never --wait --wait-timeout 180 celery-beat
dc exec -T celery-worker celery -A mainapp inspect ping --timeout=10
dc exec -T celery-worker celery -A mainapp inspect active_queues --timeout=10
dc ps -a
```

Должны отвечать локальный Celery worker и `prodcast-worker-01@...`, `prodcast-worker-02@...`. Локальный worker обслуживает `default`, Windows — `workflows`, `workflows_data`, `scenarios`. Beat должен быть ровно один во всей установке. Наличие process/health marker ещё не доказывает выполнение задания — завершить главу 07.

## 11. Agent — только если нужен на клиентском ПК

Установщик `ProdCastAgent-Setup-v0.2.exe` входит в дистрибутив, но устанавливается на компьютер пользователя для локального выполнения, а не как Windows Worker на серверы `.21/.85`. Проверить SHA256 по манифесту, установить интерактивно согласно мастеру под нужным пользователем, указать HTTPS App, проверить доверие CA и вход пользователя с разрешённой ролью. Не переносить на ПК DB/Redis/service keys. Манифест v0.2 указывает отсутствие Authenticode подписи у Agent; не представлять его как подписанный установщик.

**Результат App:** зафиксированы checksum дистрибутива и образы, License active, миграции применены, UI/AI работают, оба Windows consumer видны, один beat запущен. Далее — функциональная приёмка и резервное копирование.
