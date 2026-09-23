# ProdCast 0.2.1 — Complete / Manager

Полный комплект для установки и обновления через ProdCast Manager. Обновлён только App.

| Компонент | Исходная версия |
|---|---|
| App — backend, frontend, gateway | v2026.9.23-rc.2 |
| Agent | v2026.9.19-rc.1 — без изменений |
| AI | v2026.9.17-rc.1 — без изменений |
| License | v2026.9.17-rc.1 — без изменений |
| Windows Worker | v2026.9.17-rc.1 — без изменений |

Скачайте **ProdCast-v0.2.1-complete.zip**. Используйте **Manager 0.1.11**, исходный site.json, SHA256 нового manifest и **«Обновить»** для установленного v0.2. Для новой площадки — «Установить». Agent устанавливается отдельно на ПК. Инструкция: INSTALL-RU.md.

Образы App взяты без пересборки из [v2026.9.23-rc.2](https://github.com/saatchi190499/prodcast-release/releases/tag/v2026.9.23-rc.2). AI, License, Worker и Agent побайтно совпадают с v0.2; изменены только внешние имена пакетов. В примерах App сохранены исправления комплекта v0.2: один query string CHANNEL_REDIS_URL и выключенные необязательные Model Storage/NodeAll.

App добавляет apiapp.0042_schedule_output_policy: три поля расписания, default output_mode=merge. Manager делает резервные копии перед миграциями; откат схемы автоматически не выполняется. Общая процедура может перезапустить и неизменённые компоненты.

Проверены целостность пакетов, контракт Manager, Compose, версии зависимостей и PFX-шаблон gateway. Полный upgrade на пяти VM и функциональная приёмка нового App пока не выполнены; исходный App имеет статус release-candidate. Старый production-отчёт v0.2 не выдаётся за приёмку 0.2.1. См. compatibility-validation.json.

Секреты, сертификаты и состояние существующей площадки в дистрибутив не включены. Комплект содержит приложения, а не полный offline-образ инфраструктуры. GitHub Source code не заменяет complete ZIP.
