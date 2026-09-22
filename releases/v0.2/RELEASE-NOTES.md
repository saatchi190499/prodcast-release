# ProdCast 0.2 — Production

Полный комплект **App, Agent, AI, License и Windows Worker** для production-развёртывания. Все прикладные бинарные файлы взяты без пересборки из указанных выпусков; их исходные версии и контрольные суммы сохранены.

| Компонент | Исходная версия | Commit |
|---|---|---|
| App | `v2026.9.19-rc.1` — тот же бинарный App, что в v0.1 | `e523b7fff298682d27eb27bda883a09f2558ed23` |
| Agent | `v2026.9.19-rc.1` — тот же установщик, что в v0.1 | `e55b494d96516fba8b6cc015adfac6e63596165f` |
| AI | `v2026.9.17-rc.1` | `6a288d98398f34ea42553f70b4a363747c5a1b93` |
| License | `v2026.9.17-rc.1` | `0df0ab14c9b6dc9a29611784b4d5f9be856a5e8b` |
| Worker | `v2026.9.17-rc.1` | `3fb03104f8ac39d31a0d338910a504364cfaff2c` |

## Скачать и установить

Скачать **ProdCast-v0.2-complete.zip** и его **.zip.sha256**. В архиве находятся все пять приложений, готовые Docker images, deployment configurations, Worker offline wheelhouse и Python installer, Agent EXE, руководство по каждому серверу и общий манифест. Те же файлы доступны отдельными assets.

Начать с **INSTALL-RU.md** либо **ProdCast-v0.2-manual.html**. Порядок: DB → AI → License/App и миграции → права DB → оба Workers → один scheduler → Agent/функциональная приёмка. Примеры IP/DNS в публикуемом руководстве обезличены и должны быть заменены параметрами площадки. Сборка из исходников не требуется.

## Что изменилось относительно v0.1

- Добавлены AI, License и Worker с готовыми runtime-пакетами.
- Добавлен полный архив для переноса всех приложений одним файлом.
- Добавлены пошаговые инструкции DB, AI, App/License, Worker 01, Worker 02 и Agent, включая TLS, роли, секреты, резервирование и откат.
- В deployment-пакеты добавлены offline image references и соответствующая документация v0.2.
- Сохранены исправления примеров v0.1: корректный Redis URL и отключение неиспользуемых Model Storage/NodeAll.
- App/Agent runtime-файлы не изменены. Исходные RC-теги внутри образов/EXE остаются прежними; v0.2 — номер общего дистрибутива.

## Production validation

Бинарно идентичный комплект проверен на существующей production-площадке **21.09.2026**: HTTPS/UI/login/licensing; четыре расписанных задания BLOCKS/NOTEBOOK × MODEL_DRIVEN/DATA_DRIVEN с SUCCESS и участием обоих Windows Workers; AI chat/notebook и отказ без авторизации; Agent notebook/blocks; рестарт служб Workers; восстановление App DB dump с проверкой 75 миграций.

При подготовке v0.2 повторно проверены GitHub SHA256 всех исходных assets, пять Docker archives и их config/transport tags, 34 Worker wheels по hash lock, WinSW hash, подпись Python Software Foundation и 44 проверки общих версий зависимостей. Синтаксис Bash/PowerShell/Python/YAML в новом руководстве проверяется отдельно от запуска на серверах. В provenance сохранены неизменённые исходные manifests/checksums, dependency inventories и Agent SBOM.

**Известное замечание CI:** у исходного Worker `Shared stack versions` завершился с ошибкой из-за отсутствия локального `prodcast_petex_plugins-0.2.0` wheel в общем allowlist. Release packaging, runtime compatibility и secret scan прошли. Независимая проверка v0.2 подтвердила hash wheel, совпадение версии плагина с App и общих pinned dependencies. Статус исходного CI и тег Worker не изменялись; все upstream проверки зелёными не объявляются.

Объём production validation ограничен описанным профилем существующей площадки. Новая чистая корпоративная установка, полностью offline-подготовка инфраструктуры, перезагрузка ОС всех серверов, нагрузочные испытания и полный upgrade/rollback всего комплекта не проверялись в рамках этой публикации. Эти проверки и акт допуска выполняются на целевой площадке. Подробности: **production-validation.json**.

## Инфраструктура и совместимость

ОС, Docker/Compose, PostgreSQL/pgvector, Redis, GPU driver, Ollama/model, DNS/TLS и секреты готовятся отдельно по руководству. Полный ZIP включает все приложения ProdCast, но не все сторонние инфраструктурные зависимости. Внешние PETEX/Office/PI, Model Storage/NodeAll, LDAP/Entra и RAG не активированы базовым профилем.

Worker: CPython **3.14.7 x64**, Windows AppContainer, отдельная non-admin service account. Agent installer не подписан Authenticode; его SHA256 сохранён. Python installer внутри Worker имеет действительную подпись Python Software Foundation. Секреты и сертификаты действующей площадки не публикуются.

Работающий v0.1 с теми же пятью исходными версиями не требует переустановки ради номера v0.2. Перед любыми изменениями сохранить данные и ключи; не запускать первичную инициализацию поверх существующей базы. GitHub **Source code** archives содержат только документацию/метаданные этого distribution-репозитория; для установки скачивать assets.
