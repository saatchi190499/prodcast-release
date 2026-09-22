# ProdCast v0.2 — начать установку

Полный production-комплект пяти приложений. App/Agent: `v2026.9.19-rc.1`; AI/License/Worker: `v2026.9.17-rc.1`. Бинарные файлы не пересобраны. Внутренние версии образов/EXE остаются исходными; v0.2 обозначает комплект поставки.

## Что скачать

Для всего комплекта: `ProdCast-v0.2-complete.zip` и `ProdCast-v0.2-complete.zip.sha256`. Проверить SHA256 внешнего ZIP, распаковать, затем проверить каждый файл по вложенному `SHA256SUMS`. Все файлы можно также скачать отдельными assets со страницы релиза. Автоматические GitHub **Source code** ZIP/TAR не содержат установочных бинарных файлов.

```bash
sha256sum -c ProdCast-v0.2-complete.zip.sha256
# После распаковки перейти в каталог файлов:
sha256sum -c SHA256SUMS
```

На Windows внешнюю оболочку проверить `Get-FileHash -Algorithm SHA256 .\ProdCast-v0.2-complete.zip` и сравнить с companion-файлом/доверенным GitHub digest. Затем распаковать через Проводник или `Expand-Archive`. В руководстве есть проверка отдельных Worker/Agent файлов в PowerShell.

## Состав и назначение

| Роль | Файлы |
|---|---|
| App | `prodcast-app-v0.2-deployment.tar.gz`, три `prodcast-backend/frontend/gateway-v0.2-linux-amd64.tar.gz` |
| AI | `prodcast-ai-v0.2-deployment.tar.gz`, `prodcast-ai-v0.2-linux-amd64.tar.gz` |
| License | `prodcast-license-v0.2-deployment.tar.gz`, `prodcast-license-v0.2-linux-amd64.tar.gz` |
| Worker 01 и 02 | один `prodcast-worker-v0.2-windows-amd64.zip`: runtime, Python installer, WinSW, offline wheelhouse |
| Клиентский Agent | `ProdCastAgent-Setup-v0.2.exe` |
| Документация | `ProdCast-v0.2-manual.html`, `ProdCast-v0.2-manual.zip`, `RELEASE-NOTES.md` |
| Проверки/происхождение | `release-manifest.json`, `SHA256SUMS`, `production-validation.json`, `prodcast-provenance-v0.2.zip` |

## Порядок

Открыть **ProdCast-v0.2-manual.html** обычным браузером. Альтернатива: распаковать manual ZIP и начать с `manual-deployment-v0.2/README.md`. Руководство самодостаточно: исходные репозитории и прежние папки разработчика не требуются.

1. Заполнить параметры своей площадки вместо документационных IP/DNS, настроить ОС, сеть, время, секреты и TLS.
2. Настроить DB: PostgreSQL/pgvector и Redis TLS с отдельными учётными записями.
3. Загрузить готовый AI image, отдельно установить Ollama/модель, проверить API.
4. Загрузить готовые App/License images, создать License tenant/client token, заполнить runtime env, выполнить миграции и первичное заполнение новой БД.
5. Выдать права Workers на таблицы после миграций, установить Worker 01 и Worker 02 из одного ZIP с разными credentials.
6. Проверить consumers, включить единственный beat, установить Agent на нужные клиентские компьютеры.
7. Проверить реальные задания, AI, TLS, лицензирование, резервную копию/восстановление; заполнить акт площадки.

Образы загружаются `docker load`; для архивной установки используются `packages.offline.env` и `--pull never`. Эти env references содержат исходные теги `v2026.9.19-rc.1` / `v2026.9.17-rc.1`, а не придуманные GHCR tags `v0.2`. Не требуется собирать код, устанавливать Python-зависимости из Интернета на Workers или получать исходные приватные репозитории.

## Что площадка готовит отдельно

ОС и обновления, Docker/Compose, PostgreSQL/Redis images, NVIDIA GPU driver, Ollama и модель, DNS/время, TLS и секреты. Полный ZIP содержит все приложения ProdCast, но не является полностью автономным дистрибутивом ОС/моделей. Model Storage, NodeAll, внешние инженерные программы/лицензии, PI/LDAP/Entra и RAG не входят в активированный базовый профиль.

Паролей действующей площадки, customer CA и приватных ключей в поставке нет. Секреты создаются отдельно для каждой установки. Worker требует CPython **3.14.7 x64** из вложенного установщика. Agent не имеет Authenticode-подписи; применять правила допуска ПО своей организации.

## Если v0.1 уже работает

App и Agent в v0.2 бинарно совпадают с v0.1. Если на площадке уже используются указанные AI/License/Worker, изменение номера общего комплекта не требует переустановки работающих бинарных файлов. Сначала сверить версии/хеши и наличие всех компонентов. Сохранить существующие ключи, tenant/token, базы, media и конфигурацию. Не выполнять повторно первичную генерацию секретов, CREATE DATABASE, seed/init или установщик Windows поверх существующей службы. Для реального обновления следовать главе обслуживания с backup и планом отката.

## Production-проверка

Те же бинарные файлы прошли функциональную проверку на существующей production-площадке 21.09.2026. Подробности, исходные CI checks и известная ошибка allowlist-проверки Worker отражены в `production-validation.json`. Новый комплект v0.2 проверен по файлам/хешам/образам/зависимостям и синтаксису инструкции; новая чистая установка и полный цикл upgrade/rollback этого комплекта здесь не заявляются как выполненные.

`SHA256SUMS` проверяет payload и manifest. Внешний `ProdCast-v0.2-complete.zip` проверяется отдельным `.zip.sha256`; он не включён в собственный внутренний список хешей.
