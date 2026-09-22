# 01. Общая подготовка

## 1. Проверить сеть и доступы

Создать DNS A-записи для DB, AI, App и обоих Workers из таблицы README. Настроить DNS и синхронизацию времени на всех машинах. Администратору нужны SSH/sudo на Linux, административный RDP/консоль на Windows, чтение указанных репозиториев и релиза. Подтвердить SSH fingerprints вне текущего подключения.

| Откуда | Куда | TCP | Назначение |
|---|---|---|---|
| App `.23` | DB `.128` | 5432, 6380 | PostgreSQL TLS, Redis TLS |
| AI `.76` | DB `.128` | 5432 | отдельная БД AI |
| Workers `.21`, `.85` | DB `.128` | 5432, 6380 | задания и результаты |
| Workers `.21`, `.85` | App `.23` | 443 | подписанные артефакты и media |
| App `.23` | AI `.76` | 8443 | AI HTTPS |
| Клиентские компьютеры | App `.23` | 443, 80 | HTTPS, HTTP redirect |
| Админ `.225` | Linux / Windows | 22 / 3389 | администрирование |
| Каждый сервер | DNS / NTP площадки | по политике площадки | имена и время |

Ollama `11434` слушает только loopback AI. License HTTP `8100` доступен только loopback App; HTTPS proxy `8443` — внутри Docker. PostgreSQL `5432` и Redis `6380` не публикуются в Интернет. На Windows входящих портов для очереди открывать не нужно. Для получения инфраструктурных зависимостей нужны исходящие HTTPS к доверенным источникам Docker, ОС, драйверов и Ollama. Приложения ProdCast уже собраны: для них не нужны checkout/PyPI/GHCR после загрузки полного комплекта. При изолированной production-сети инфраструктуру и модели подготовить на машине с доступом к Интернету и перенести отдельно.

## 2. Подготовить Linux: повторить на DB, AI, App

На чистой Ubuntu 26.04 amd64:

```bash
sudo -i
set -euo pipefail
umask 077
dpkg --print-architecture
timedatectl status
getent hosts prodcast-db-01.example.internal prodcast-ai-01.example.internal prodcast-app-01.example.internal
apt-get update
apt-get install -y ca-certificates curl git python3 openssl jq zstd iptables iptables-persistent
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod 0644 /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
install -d -m 0700 /root/prodcast-inbox
install -d -m 0755 /opt/prodcast /srv/prodcast-build
dpkg-query -W docker-ce docker-ce-cli containerd.io docker-compose-plugin \
  > /root/prodcast-platform-versions.txt
```

Проверить: amd64, время синхронизировано, все DNS-имена разрешаются в нужные IP, Docker работает. Compose нужен **2.30.0 или новее**: AI использует `env_file.format: raw`, чтобы сохранить `$` в scrypt verifier. Установка из официального APT-репозитория описана в [Docker Ubuntu](https://docs.docker.com/engine/install/ubuntu/), формат переменных — в [Compose services](https://docs.docker.com/reference/compose-file/services/#format). Если Docker уже установлен, сначала проверить происхождение пакетов; не смешивать `docker.io` и `docker-ce`.

Выбранные версии ОС-пакетов записать в журнал и сохранить установочные пакеты в хранилище площадки. Релиз приложения не фиксирует версии APT. Здесь нет автоматического обновления ОС или удаления существующих окружений.

Для обоих Windows-серверов установить **PowerShell 7.4+ x64** из корпоративного пакета либо MSI по [инструкции Microsoft](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows). Открывать повышенный `pwsh.exe`. Проверить `$PSVersionTable.PSVersion` и `[Environment]::Is64BitProcess`. Если используется Winget на Windows Server 2025 Desktop Experience, команда установки MSI: `winget install --id Microsoft.PowerShell --source winget --installer-type wix`; после установки открыть новый терминал. Версию записать в журнал.

## 3. Сгенерировать секреты один раз

На защищённой административной Linux-машине, не на клиентском компьютере пользователя приложения. Подойдёт отдельная VM с Python 3 и OpenSSL. Далее её называем **Admin Linux**. Все значения ниже — новые для чистой установки; при обновлении сохраняются существующие секреты.

```bash
sudo -i
set -euo pipefail
umask 077
test ! -e /root/prodcast-bootstrap
install -d -m 0700 /root/prodcast-bootstrap
cd /root/prodcast-bootstrap
python3 - <<'PY'
import base64, hashlib, json, pathlib, secrets, shlex
p = pathlib.Path('.')
names = ('PG_ADMIN PW_APP PW_LICENSE PW_AI PW_W01 PW_W02 '
         'REDIS_ADMIN REDIS_APP REDIS_W01 REDIS_W02 DJANGO_KEY '
         'MODULE_KEY RESOLVE_KEY MEDIA_KEY SIGNING_KEY METRICS_KEY '
         'AI_KEY AI_BASIC LICENSE_SALT LICENSE_BOOTSTRAP').split()
s = {k: secrets.token_hex(32) for k in names}
s['FERNET_KEY'] = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
salt = secrets.token_bytes(16)
h = hashlib.scrypt(s['AI_BASIC'].encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
b64 = lambda v: base64.urlsafe_b64encode(v).decode().rstrip('=')
s['AI_HASH'] = 'scrypt$16384$8$1$' + b64(salt) + '$' + b64(h)
(p/'master-secrets.json').write_text(json.dumps(s, indent=2)+'\n')
sets = {
 'db': 'PG_ADMIN PW_APP PW_LICENSE PW_AI PW_W01 PW_W02 REDIS_ADMIN REDIS_APP REDIS_W01 REDIS_W02',
 'app': 'PW_APP PW_LICENSE REDIS_APP DJANGO_KEY MODULE_KEY RESOLVE_KEY MEDIA_KEY SIGNING_KEY METRICS_KEY FERNET_KEY AI_KEY AI_BASIC LICENSE_SALT LICENSE_BOOTSTRAP',
 'ai': 'PW_AI AI_KEY AI_HASH',
 'worker01': 'PW_W01 REDIS_W01 MEDIA_KEY SIGNING_KEY',
 'worker02': 'PW_W02 REDIS_W02 MEDIA_KEY SIGNING_KEY',
}
for host, keys in sets.items():
 d = p/'out'/host; d.mkdir(parents=True)
 selected = {k:s[k] for k in keys.split()}
 if host.startswith('worker'):
  (d/'secrets.json').write_text(json.dumps(selected, indent=2)+'\n')
 else:
  (d/'secrets.env').write_text(''.join(k+'='+shlex.quote(v)+'\n' for k,v in selected.items()))
print('Secrets generated; values were not printed.')
PY
```

Сохранить `master-secrets.json` в защищённом хранилище паролей/зашифрованном резервном архиве. Не включать `set -x`, запись терминала, не отправлять значения в чаты и отчёты. Не запускать генератор повторно для уже установленной площадки.

| Значение | Где должно совпасть |
|---|---|
| `PW_APP`, `PW_LICENSE`, `PW_AI` | соответствующая роль DB ↔ App/License/AI |
| `PW_W01`, `PW_W02` | соответствующая роль DB ↔ секрет Worker |
| `REDIS_APP`, `REDIS_W01`, `REDIS_W02` | Redis ACL ↔ соответствующий клиент |
| `MEDIA_KEY` | App `MEDIA_DOWNLOAD_API_KEY` ↔ Worker `media_key` |
| `SIGNING_KEY` | App `WORKFLOW_ARTIFACT_SIGNING_KEY` ↔ Worker `signing_key` |
| `AI_KEY` | AI `NOTEBOOK_API_KEY` ↔ App `PRODCAST_AI_API_KEY` |
| `AI_BASIC` / `AI_HASH` | App хранит пароль, AI — его scrypt verifier |
| `FERNET_KEY` | постоянный ключ расшифровки внешних credentials App |
| `LICENSE_SALT` | постоянный salt License: замена нарушает проверку выданных токенов |
| License client token | создаётся License API позже, переносится только в App |

## 4. Выпустить TLS-сертификаты

Если есть корпоративный CA, заказать те же leaf-сертификаты с указанными SAN и serverAuth; вместо генерации CA положить выданные ключи/цепочки в структуру ниже. Для самостоятельного CA на Admin Linux:

```bash
cd /root/prodcast-bootstrap
install -d -m 0700 pki
cd pki
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out ca.key
openssl req -x509 -new -sha256 -days 3650 -key ca.key -out ca.crt \
  -subj '/CN=ProdCast Production Root CA' \
  -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
while IFS='|' read -r name cn san; do
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out "$name.key"
  openssl req -new -key "$name.key" -out "$name.csr" -subj "/CN=$cn"
  printf '%s\n' 'basicConstraints=critical,CA:FALSE' \
    'keyUsage=critical,digitalSignature,keyEncipherment' \
    'extendedKeyUsage=serverAuth' "subjectAltName=$san" > "$name.ext"
  openssl x509 -req -in "$name.csr" -CA ca.crt -CAkey ca.key -CAcreateserial \
    -days 365 -sha256 -extfile "$name.ext" -out "$name.crt"
  openssl verify -CAfile ca.crt "$name.crt"
done <<'CERTS'
postgres|prodcast-db-01.example.internal|DNS:prodcast-db-01.example.internal,IP:192.0.2.128,IP:127.0.0.1
redis|prodcast-db-01.example.internal|DNS:prodcast-db-01.example.internal,IP:192.0.2.128,IP:127.0.0.1
site|prodcast-app-01.example.internal|DNS:prodcast-app-01.example.internal,IP:192.0.2.23
ai|prodcast-ai-01.example.internal|DNS:prodcast-ai-01.example.internal,IP:192.0.2.76
license|license-proxy|DNS:license-proxy
CERTS
openssl x509 -in ca.crt -noout -fingerprint -sha256
cd ..
cp pki/ca.crt out/db/ca.crt
cp pki/postgres.crt pki/postgres.key pki/redis.crt pki/redis.key out/db/
cp pki/ca.crt out/app/ca.crt
cp pki/site.crt pki/site.key pki/license.crt pki/license.key out/app/
cp pki/ca.crt out/ai/ca.crt
cp pki/ai.crt pki/ai.key out/ai/
cp pki/ca.crt out/worker01/prodcast-db-ca.crt
cp pki/ca.crt out/worker01/prodcast-app-ca.crt
cp pki/ca.crt out/worker02/prodcast-db-ca.crt
cp pki/ca.crt out/worker02/prodcast-app-ca.crt
```

`ca.key` остаётся только на Admin Linux/в защищённом хранилище CA. Если использованы разные корпоративные CA, `db-ca.crt`, `ai-ca.crt`, `license-ca.crt`, `prodcast-app-ca.crt` должны содержать соответствующие цепочки доверия, а leaf `.crt` — leaf + intermediate, без приватного ключа CA. В примере все сервисы используют один собственный CA.

На клиентских Windows-компьютерах импортировать **только публичный `ca.crt`** в Trusted Root Certification Authorities после сверки fingerprint. Через повышенную PowerShell: `Import-Certificate -FilePath C:\Install\ca.crt -CertStoreLocation Cert:\LocalMachine\Root`. Приватные серверные ключи туда не переносить.

## 5. Доставить отдельный комплект на каждый сервер

Передавать по SSH/SFTP с проверенным host key. Пример с административным Linux-пользователем `deployadmin` (заменить реальным; root SSH не требуется):

```bash
cd /root/prodcast-bootstrap
ssh deployadmin@prodcast-db-01.example.internal 'umask 077; mkdir -p ~/prodcast-inbox'
scp out/db/* deployadmin@prodcast-db-01.example.internal:prodcast-inbox/
```

На DB в сессии этого пользователя: `sudo install -m 0600 ~/prodcast-inbox/* /root/prodcast-inbox/`. Повторить для App с `out/app` и для AI с `out/ai`. Проверить владельца root и права 0700/0600. После импорта удалить временные копии из домашнего каталога пользователя; пароль/ключ CA в комплект не входит.

Windows: через согласованный защищённый канал передать содержимое `out/worker01` в `C:\Install\prodcast-inbox` на Worker 01 и `out/worker02` на Worker 02. У каталога убрать наследуемые права обычных пользователей, оставить SYSTEM и Administrators. `secrets.json` нужен только для защищённого интерактивного ввода; дальнейшее хранение рабочих секретов — DPAPI.

## 6. Подготовить полный дистрибутив v0.2

Скачать `ProdCast-v0.2-complete.zip` и `ProdCast-v0.2-complete.zip.sha256` из GitHub Release v0.2. Проверить хеш по доверенной странице релиза и companion-файлу, затем распаковать. В ZIP находятся все десять runtime-файлов пяти компонентов, документация, provenance, общий manifest и `SHA256SUMS`. Автоматические GitHub Source code ZIP/TAR не являются установочным комплектом.

В Linux проверить внешнюю оболочку: `sha256sum -c ProdCast-v0.2-complete.zip.sha256`. После распаковки перейти в каталог файлов и выполнить `sha256sum -c SHA256SUMS`. Внешний ZIP не включён в свой внутренний SHA256SUMS, чтобы не создавать циклический хеш; он проверяется отдельным companion-файлом.

На App положить содержимое комплекта в `/srv/prodcast-dist/v0.2`. На AI — туда же, либо минимум два файла `prodcast-ai-v0.2-*`, manifest/SHA256SUMS и руководство. На каждый Worker передать `prodcast-worker-v0.2-windows-amd64.zip`, `SHA256SUMS` и `release-manifest.json` в `C:\Install\worker-release`. При передаче подмножества Linux `sha256sum --ignore-missing -c SHA256SUMS` проверяет только имеющиеся файлы: отдельно сверить наличие всех файлов нужного компонента.

Не переименовывать файлы перед проверкой. Один Worker ZIP применяется на обоих серверах, разные credentials создаются при установке. Agent EXE устанавливается только на рабочих компьютерах пользователей. Все бинарные файлы сохранены без пересборки; исходные image transport tags отражены в `packages.offline.env`.

**Результат главы:** машины доступны по именам, время верно, Docker готов на трёх Linux-хостах; у каждого сервера свой закрытый inbox; имеются доверенные CA и проверенные архивы. Заполнить дату, администратора и версии ОС в журнале из главы 07.
