# ProdCast releases

Готовые дистрибутивы ProdCast. Исходный код приложений и история их сборки хранятся в отдельных репозиториях; здесь публикуются runtime-пакеты, инструкции и сведения о проверках.

## Полный комплект v0.2.1 — Manager

[ProdCast 0.2.1 — Complete](https://github.com/saatchi190499/prodcast-release/releases/tag/v0.2.1): App **v2026.9.23-rc.2**, остальные приложения побайтно сохранены из v0.2. Agent **v2026.9.19-rc.1**; AI, License, Worker **v2026.9.17-rc.1**.

Скачайте **ProdCast-v0.2.1-complete.zip**. Для Manager 0.1.11 нужен SHA256 нового manifest из описания релиза. Используйте исходную площадку и «Обновить» для v0.2, «Установить» для новой площадки. [Инструкция](releases/v0.2.1/INSTALL-RU.md), [manifest](releases/v0.2.1/release-manifest.json), [границы проверок](releases/v0.2.1/compatibility-validation.json). Полный upgrade на пяти VM и функциональная приёмка нового App пока не выполнены.

## Полный комплект v0.2

[**ProdCast 0.2 — Production**](https://github.com/saatchi190499/prodcast-release/releases/tag/v0.2) содержит **App, Agent, AI, License и Windows Worker**:

| Компоненты | Исходная версия |
|---|---|
| App и Agent — та же пара, что в v0.1 | `v2026.9.19-rc.1` |
| AI, License, Worker | `v2026.9.17-rc.1` |

Скачать `ProdCast-v0.2-complete.zip` и `.zip.sha256`, проверить хеш, распаковать и проверить вложенный `SHA256SUMS`. Все приложения также доступны отдельными assets. Сборка из исходников для установки не требуется.

- [Пошаговое руководство по серверам](docs/v0.2/README.md).
- [С чего начать](releases/v0.2/INSTALL-RU.md).
- [Изменения и границы production validation](releases/v0.2/RELEASE-NOTES.md).
- [Манифест компонентов и контрольных сумм](releases/v0.2/release-manifest.json).
- [Подробный отчёт проверок](releases/v0.2/production-validation.json).

Бинарно идентичный комплект прошёл функциональную проверку на существующей production-площадке 21.09.2026. Новый дистрибутив проверен по целостности, происхождению и зависимостям. Новая чистая площадка, полностью автономная инфраструктура, нагрузка и полный upgrade/rollback требуют отдельной приёмки. Известное замечание upstream CI Worker описано в отчёте; исходные RC-теги/манифесты не переписаны.

## Установка и инфраструктура

Инструкции включают DB, AI, App/License, два Windows Worker и клиентский Agent: конфигурации, TLS, роли, секреты, запуск, проверки, резервное копирование и откат. Примеры адресов обезличены: заменить их параметрами площадки перед установкой.

Linux images входят в поставку и загружаются через `docker load`; `packages.offline.env` сохраняет исходные transport tags. При установке через registry используются digest references в `packages.env`; доступ GHCR при необходимости предоставляется отдельно. Не использовать publishing token для развёртывания.

ОС, Docker/Compose, PostgreSQL/Redis, GPU driver, Ollama/model, DNS/TLS и уникальные секреты готовятся отдельно. Полный ZIP включает все пять приложений ProdCast, но не все сторонние инфраструктурные зависимости. Ни приватные ключи, ни данные/пароли действующей площадки не распространяются.

Agent installer не имеет Authenticode-подписи; проверить SHA256 и правила допуска ПО своей организации. Windows Worker включает Python 3.14.7 x64 installer с подписью Python Software Foundation и offline wheelhouse.

## Предыдущие версии и содержимое репозитория

[v0.1](https://github.com/saatchi190499/prodcast-release/releases/tag/v0.1) остаётся доступным без изменений и содержит App/Agent. Версии `-rc.N` обозначают исходные release candidates. Во v0.2 прикладные бинарные файлы не пересобирались; обновлён состав общего дистрибутива и документация.

Автоматические GitHub **Source code (zip/tar.gz)** содержат только файлы этого distribution-репозитория. Для установки использовать release assets.

Core Python поставляется в bytecode, который допускает восстановление кода. Браузерный JavaScript и open-source integration plugins доступны для анализа; формат дистрибутива не является механизмом шифрования исходников.
