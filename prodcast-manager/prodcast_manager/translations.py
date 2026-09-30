"""English UI catalogue. Russian strings are stable message keys."""
EN = {'Восстановить': 'Repair',
 'Файл модели AI для офлайн-установки:': 'AI model file for offline installation:',
 'Выбрать модель…': 'Select model…',
 'Компоненты Ollama для AI (ZIP):': 'Ollama components for AI (ZIP):',
 'Выбрать Ollama…': 'Select Ollama…',
 'Офлайн-релиз требует выданный файл активации и публичный PEM.': 'An offline release requires an issued activation file and public PEM.',
 'Для восстановления выберите точный установленный релиз и исходную площадку.': 'For recovery, select the exact installed release and original site profile.',
 'Восстановление контейнеров и Workers из установленного релиза. Данные сохраняются. Используйте исходную площадку; возможен перезапуск неисправных сервисов.': 'Recover containers and Workers from the installed release. Data is preserved. Use the original site profile; failed services may restart.',
 'Локальный журнал: ': 'Local log: ',
 'ОШИБКА: ': 'ERROR: ',
 'Укажите ID компании, полученный с сервера активации.': 'Enter the company ID provided by the activation service.',
 'Выберите онлайн или офлайн активацию.': 'Select online or offline activation.',
 'Файл активации слишком большой.': 'The activation file is too large.',
 'Неподдерживаемый формат файла активации.': 'Unsupported activation file format.',
 'Некорректный ID публичного ключа.': 'Invalid public key ID.',
 'Требуется публичный ключ Ed25519; приватный ключ загружать нельзя.': 'An Ed25519 public key is required; do not upload a private key.',
 'Файл выпущен для другой установки, компании или среды.': 'The file was issued for another installation, company or deployment '
                                                           'environment.',
 'Файл активации ещё не действует или срок истёк.': 'The activation file is not yet valid or has expired.',
 'Укажите HTTPS адрес сервера активации без пароля и параметров.': 'Enter the activation service HTTPS address without credentials or '
                                                                   'query parameters.',
 'Укажите клиентский токен компании (не токен администратора).': 'Enter the company client token, not an administrator token.',
 'Адрес должен оканчиваться на /v1/decision или содержать только имя сервера.': 'Use the server address alone or an address ending in '
                                                                                '/v1/decision.',
 'Повторяющееся поле в файле активации.': 'Duplicate field in the activation file.',
 'Подключение активации App': 'App activation connection',
 'ID установки — только чтение': 'Installation ID - read only',
 'Онлайн-сервер': 'Online server',
 'Импорт готового файла': 'Import issued file',
 'Загрузить выданный файл (.license)…': 'Load issued file (.license)...',
 'Загрузить публичный ключ (.pem)…': 'Load public key (.pem)...',
 'Настройки применяются при следующей установке или обновлении App.': 'Settings are applied during the next App installation or update.',
 'Сохранить подключение': 'Save connection',
 'ID компании': 'Company ID',
 'HTTPS адрес сервера': 'Server HTTPS address',
 'Клиентский токен компании': 'Company client token',
 'Импортировать готовый файл': 'Import the issued file',
 'Выданный файл активации': 'Issued activation file',
 'Публичный сертификат / ключ': 'Public certificate / key',
 'Файл слишком большой.': 'The file is too large.',
 'Приватный ключ загружать нельзя. Нужен публичный ключ или сертификат.': 'Do not upload a private key. A public key or certificate is '
                                                                          'required.',
 '. Он будет проверен при импорте.': '. It will be validated on import.',
 'Импорт файла': 'Import file',
 'Подключение активации': 'Activation connection',
 'Офлайн-файл выпускается только на сервере лицензий.\nЗдесь можно подключить онлайн-сервер или импортировать готовый файл.': 'Offline '
                                                                                                                              'files are '
                                                                                                                              'issued only '
                                                                                                                              'by the '
                                                                                                                              'licensing '
                                                                                                                              'service.\n'
                                                                                                                              'Connect an '
                                                                                                                              'online '
                                                                                                                              'server or '
                                                                                                                              'import an '
                                                                                                                              'issued file '
                                                                                                                              'here.',
 'Загрузить CA онлайн-сервера…': 'Load online server CA...',
 'CA нужен, если сервер использует внутренний сертификат.\nКлиентский токен выдаёт администратор сервера.': 'A CA is needed if the service '
                                                                                                            'uses an internal '
                                                                                                            'certificate.\n'
                                                                                                            'The service administrator '
                                                                                                            'provides the client token.',
 'Получите у администратора два готовых файла:': 'Obtain two issued files from the administrator:',
 'Ранее загруженный файл сохранён.': 'Previously loaded file is saved.',
 'Файл не выбран.': 'No file selected.',
 'Компания, срок и права берутся из подписанного файла.\nManager не меняет их. Приватный ключ подписи не требуется.': 'The company, '
                                                                                                                      'validity and '
                                                                                                                      'entitlements come '
                                                                                                                      'from the signed '
                                                                                                                      'file.\n'
                                                                                                                      'Manager does not '
                                                                                                                      'change them. A '
                                                                                                                      'private signing key '
                                                                                                                      'is not required.',
 'Показать ID этой установки': 'Show this installation ID',
 'Справочный ID для администратора сервера лицензий.': 'Reference ID for the licensing service administrator.',
 'Копировать ID': 'Copy ID',
 'Выбран файл: ': 'Selected file: ',
 'Выберите готовый .license, выданный сервером лицензий.': 'Select an issued .license file from the licensing service.',
 'Не удалось проверить подпись выданного файла.': 'Could not verify the signature of the issued file.',
 'Все файлы': 'All files',
 'Для сертификата организации укажите DNS-имя сайта, а не IP VM.': 'Enter the website DNS name for the corporate certificate, not the VM '
                                                                   'IP.',
 'Укажите полный адрес https://имя-сервера, без пути /login, логина и пароля; порт 443. Доменная зона может быть любой, .local не требуется.': 'Enter '
                                                                                                                                               'the '
                                                                                                                                               'full '
                                                                                                                                               'https://server-name '
                                                                                                                                               'address '
                                                                                                                                               'without '
                                                                                                                                               '/login '
                                                                                                                                               'or '
                                                                                                                                               'credentials; '
                                                                                                                                               'port '
                                                                                                                                               '443. '
                                                                                                                                               'Any '
                                                                                                                                               'DNS '
                                                                                                                                               'zone '
                                                                                                                                               'is '
                                                                                                                                               'allowed; '
                                                                                                                                               '.local '
                                                                                                                                               'is '
                                                                                                                                               'not '
                                                                                                                                               'required.',
 'Укажите корректное DNS-имя сайта клиента (для IDN используйте punycode).': 'Enter a valid website DNS name (use punycode for IDN).',
 'Слишком большой PFX или файл CA.': 'The PFX or CA file is too large.',
 'PFX должен содержать серверный сертификат и его приватный ключ. Запросите экспорт с ключом.': 'The PFX must contain a server certificate '
                                                                                                'and its private key. Request an export '
                                                                                                'with the key.',
 'Импортируйте серверный сертификат App, а не приватный ключ CA.': 'Import the App server certificate, not the CA private key.',
 'В PFX нет корневого CA. Выберите дополнительный PEM-файл с цепочкой CA организации.': 'The PFX does not contain the root CA. Select an '
                                                                                        'additional PEM with the corporate CA chain.',
 'Адрес клиента должен отличаться от внутреннего HTTPS адреса App на вкладке «Площадка». Для новой установки укажите там https://IP_App; адрес существующей площадки не меняйте.': 'The '
                                                                                                                                                                                   'client '
                                                                                                                                                                                   'address '
                                                                                                                                                                                   'must '
                                                                                                                                                                                   'differ '
                                                                                                                                                                                   'from '
                                                                                                                                                                                   'the '
                                                                                                                                                                                   'internal '
                                                                                                                                                                                   'App '
                                                                                                                                                                                   'HTTPS '
                                                                                                                                                                                   'address '
                                                                                                                                                                                   'on '
                                                                                                                                                                                   'the '
                                                                                                                                                                                   'Site '
                                                                                                                                                                                   'tab. '
                                                                                                                                                                                   'Use '
                                                                                                                                                                                   'https://IP_App '
                                                                                                                                                                                   'there '
                                                                                                                                                                                   'for '
                                                                                                                                                                                   'a '
                                                                                                                                                                                   'new '
                                                                                                                                                                                   'installation; '
                                                                                                                                                                                   'keep '
                                                                                                                                                                                   'the '
                                                                                                                                                                                   'existing '
                                                                                                                                                                                   "site's "
                                                                                                                                                                                   'address '
                                                                                                                                                                                   'unchanged.',
 'Сертификат и приватный ключ не соответствуют друг другу.': 'The certificate and private key do not match.',
 'Для HTTPS требуется ключ RSA от 2048 бит или EC от 256 бит.': 'HTTPS requires RSA of at least 2048 bits or EC of at least 256 bits.',
 'Не прошла проверка SAN, назначения Server Authentication или цепочки CA. Проверьте адрес сайта и приложите полную цепочку до корневого CA.': 'SAN, '
                                                                                                                                               'Server '
                                                                                                                                               'Authentication '
                                                                                                                                               'usage '
                                                                                                                                               'or '
                                                                                                                                               'CA '
                                                                                                                                               'chain '
                                                                                                                                               'validation '
                                                                                                                                               'failed. '
                                                                                                                                               'Check '
                                                                                                                                               'the '
                                                                                                                                               'website '
                                                                                                                                               'address '
                                                                                                                                               'and '
                                                                                                                                               'provide '
                                                                                                                                               'the '
                                                                                                                                               'full '
                                                                                                                                               'chain '
                                                                                                                                               'up '
                                                                                                                                               'to '
                                                                                                                                               'the '
                                                                                                                                               'root '
                                                                                                                                               'CA.',
 'Неполный или неподдерживаемый сертификат HTTPS / цепочка CA.': 'Incomplete or unsupported HTTPS certificate / CA chain.',
 'Не удалось открыть PFX: проверьте пароль, формат и целостность файла.': 'Could not open the PFX: check its password, format and '
                                                                          'integrity.',
 'Дополнительная цепочка CA должна быть в формате PEM.': 'The additional CA chain must be in PEM format.',
 'Откройте исходную конфигурацию площадки. Для PFX не меняйте её внутренний HTTPS адрес.': 'Open the original site configuration. Do not '
                                                                                           'change its internal HTTPS address for PFX '
                                                                                           'import.',
 'Сертификат или CA ещё не действует либо уже истёк.': 'The certificate or CA is not yet valid or has expired.',
 'Корневой сертификат должен быть сертификатом CA.': 'The root certificate must be a CA certificate.',
 'Сначала завершите прерванную операцию с прежним сертификатом; затем импортируйте новый PFX.': 'Finish the interrupted operation with the '
                                                                                                'previous certificate before importing a '
                                                                                                'new PFX.',
 '{v0}: {v1} — демонстрационный адрес. Укажите актуальный IP перед подключением к серверам.': '{v0}: {v1} is an example address. Enter the '
                                                                                              'actual IP before connecting to servers.',
 'Сначала импортируйте PFX на вкладке «Сертификат App».': 'Import a PFX on the App certificate tab first.',
 'Нужны исходные site.json и vault уже установленной площадки.': "The installed site's original site.json and vault are required.",
 'Сначала завершите прерванную установку или обновление.': 'Finish the interrupted installation or update first.',
 'app: проверка SSH перед применением сертификата': 'app: checking SSH before applying the certificate',
 'app: установка сертификата и перезапуск веб-сервисов; возможна краткая недоступность сайта': 'app: applying certificate and restarting '
                                                                                               'web services; the website may be briefly '
                                                                                               'unavailable',
 'Для браузеров нужен DNS клиента и доверие к CA организации. Проверка сервера не меняет настройки ПК.': 'Browsers require client DNS and '
                                                                                                         'corporate CA trust. Server '
                                                                                                         'checks do not change PC '
                                                                                                         'settings.',
 'AI отключён: подключение, установка и проверки пропущены. Существующие службы AI не удаляются.': 'AI disabled: connection, installation '
                                                                                                   'and checks skipped. Existing AI '
                                                                                                   'services are not removed.',
 'AI: отдельный заключительный этап; ошибки не изменяют успех основного стека.': 'AI: optional final stage; errors do not change the core '
                                                                                 'stack result.',
 'AI: установка и проверка ответа из App завершены успешно.': 'AI: installation and response verification from App completed successfully.',
 'Сначала повторите «Применить сертификат на App» для завершения предыдущей операции.': 'Repeat Apply certificate to App to finish the '
                                                                                        'previous operation first.',
 'Сначала завершите установку. При первой установке импортированный PFX применяется автоматически.': 'Finish installation first. An '
                                                                                                     'imported PFX is applied '
                                                                                                     'automatically during initial '
                                                                                                     'installation.',
 'app: сертификат применён; HTTPS проверен для ': 'app: certificate applied; HTTPS verified for ',
 'Сертификат сохранён в vault. Устраните причину и повторите «Применить сертификат на App».': 'Certificate saved in the vault. Resolve the '
                                                                                              'cause and repeat Apply certificate to App.',
 'Проверю основной стек перед сменой режима незавершённой предварительной проверки. Старый журнал пока сохранён.': 'Checking the core '
                                                                                                                   'stack before changing '
                                                                                                                   'the unfinished '
                                                                                                                   'preflight mode. The '
                                                                                                                   'original journal is '
                                                                                                                   'preserved.',
 '{v0}: проверка SSH и прав': '{v0}: checking SSH and permissions',
 '{v0}: проверка пройдена': '{v0}: checks passed',
 'Установка уже существует. Выберите «Обновить»: текущая проверка не изменяла серверы.': 'An installation already exists. Select Update: '
                                                                                         'this preflight did not change the servers.',
 'Резервное копирование доступно после установки Manager на App, DB и обоих Workers. Сначала завершите «Установить».': 'Backup is '
                                                                                                                       'available after '
                                                                                                                       'Manager installs '
                                                                                                                       'App, DB and both '
                                                                                                                       'Workers. Complete '
                                                                                                                       'Install first.',
 'Основной стек: успешно. App, DB и Workers проверены; результат сохранён.': 'Core stack: successful. App, DB and Workers verified; result '
                                                                             'saved.',
 'Операция для App, DB и Workers завершена; результат сохранён.': 'App, DB and Worker operation completed; result saved.',
 'Укажите адрес AI и подтвердите его SSH-отпечаток на вкладке серверов.': 'Enter the AI address and verify its SSH fingerprint on the '
                                                                          'Servers tab.',
 'Основной стек остаётся успешно развёрнутым. AI можно повторить отдельно с тем же релизом.': 'The core stack remains successfully '
                                                                                              'deployed. AI can be retried separately with '
                                                                                              'the same release.',
 'Сначала завершите установку основного стека.': 'Finish core stack installation first.',
 'Включите AI на вкладке серверов и выполните обновление основного стека для настройки App.': 'Enable AI on the Servers tab and update the '
                                                                                              'core stack to configure App.',
 'Старые сертификаты дополнены AKI/SKI; ключи и CA сохранены. Зашифрованная копия прежнего vault находится в history.': 'Legacy '
                                                                                                                        'certificates '
                                                                                                                        'updated with '
                                                                                                                        'AKI/SKI; keys and '
                                                                                                                        'CA preserved. An '
                                                                                                                        'encrypted copy of '
                                                                                                                        'the previous '
                                                                                                                        'vault is in '
                                                                                                                        'history.',
 'Есть незавершённая операция «{v0}» с начатыми серверными шагами. Продолжите её с исходным релизом; смена режима сейчас заблокирована.': 'Unfinished '
                                                                                                                                          '{v0} '
                                                                                                                                          'operation '
                                                                                                                                          'has '
                                                                                                                                          'started '
                                                                                                                                          'server '
                                                                                                                                          'changes. '
                                                                                                                                          'Resume '
                                                                                                                                          'it '
                                                                                                                                          'with '
                                                                                                                                          'the '
                                                                                                                                          'original '
                                                                                                                                          'release; '
                                                                                                                                          'changing '
                                                                                                                                          'mode '
                                                                                                                                          'is '
                                                                                                                                          'blocked.',
 'На одной из VM есть состояние установки. Смена режима небезопасна: продолжите исходную операцию с исходным релизом. Журнал сохранён.': 'A '
                                                                                                                                         'VM '
                                                                                                                                         'has '
                                                                                                                                         'installation '
                                                                                                                                         'state. '
                                                                                                                                         'Changing '
                                                                                                                                         'mode '
                                                                                                                                         'is '
                                                                                                                                         'unsafe: '
                                                                                                                                         'resume '
                                                                                                                                         'the '
                                                                                                                                         'original '
                                                                                                                                         'operation '
                                                                                                                                         'with '
                                                                                                                                         'its '
                                                                                                                                         'original '
                                                                                                                                         'release. '
                                                                                                                                         'Journal '
                                                                                                                                         'preserved.',
 'Предыдущая попытка остановилась до изменений. Все серверы подтвердили завершённую установку; обновление разрешено. Журнал проверки сохранён в history.': 'The '
                                                                                                                                                           'previous '
                                                                                                                                                           'attempt '
                                                                                                                                                           'stopped '
                                                                                                                                                           'before '
                                                                                                                                                           'changes. '
                                                                                                                                                           'All '
                                                                                                                                                           'servers '
                                                                                                                                                           'confirm '
                                                                                                                                                           'a '
                                                                                                                                                           'completed '
                                                                                                                                                           'installation; '
                                                                                                                                                           'update '
                                                                                                                                                           'is '
                                                                                                                                                           'allowed. '
                                                                                                                                                           'Preflight '
                                                                                                                                                           'journal '
                                                                                                                                                           'archived '
                                                                                                                                                           'in '
                                                                                                                                                           'history.',
 'Основной стек подтвердил отсутствие установки Manager. Предыдущий журнал сохранён в history; выбранный режим разрешён.': 'The core stack '
                                                                                                                           'confirms no '
                                                                                                                           'Manager '
                                                                                                                           'installation. '
                                                                                                                           'The previous '
                                                                                                                           'journal is '
                                                                                                                           'archived in '
                                                                                                                           'history; the '
                                                                                                                           'selected mode '
                                                                                                                           'is allowed.',
 '{v0}: установка Manager не найдена — доступен режим «Установить».': '{v0}: no Manager installation found; Install is available.',
 'Не удалось дополнить отчёт результатом AI. Успешный журнал основного стека сохранён.': 'Could not add the AI result to the report. The '
                                                                                         'successful core stack journal is saved.',
 'успешно': 'successful',
 'отключён': 'disabled',
 'требует внимания': 'needs attention',
 'проверен': 'checked',
 'не установлен': 'not installed',
 'Готово. Основной стек: успешно. AI: ': 'Done. Core stack: successful. AI: ',
 'Предварительная проверка остановлена. Основные шаги установки/обновления этого запуска ещё не выполнялись. Сохраните vault и журнал, устраните причину и повторите ту же операцию.': 'Preflight '
                                                                                                                                                                                       'stopped. '
                                                                                                                                                                                       'This '
                                                                                                                                                                                       'run '
                                                                                                                                                                                       'has '
                                                                                                                                                                                       'not '
                                                                                                                                                                                       'started '
                                                                                                                                                                                       'installation/update '
                                                                                                                                                                                       'steps. '
                                                                                                                                                                                       'Keep '
                                                                                                                                                                                       'the '
                                                                                                                                                                                       'vault '
                                                                                                                                                                                       'and '
                                                                                                                                                                                       'journal, '
                                                                                                                                                                                       'resolve '
                                                                                                                                                                                       'the '
                                                                                                                                                                                       'cause '
                                                                                                                                                                                       'and '
                                                                                                                                                                                       'repeat '
                                                                                                                                                                                       'the '
                                                                                                                                                                                       'same '
                                                                                                                                                                                       'operation.',
 'Операция остановлена. Не удаляйте vault и журнал. Повторите ту же операцию после устранения причины; откат БД автоматически не выполняется.': 'Operation '
                                                                                                                                                'stopped. '
                                                                                                                                                'Keep '
                                                                                                                                                'the '
                                                                                                                                                'vault '
                                                                                                                                                'and '
                                                                                                                                                'journal. '
                                                                                                                                                'Resolve '
                                                                                                                                                'the '
                                                                                                                                                'cause '
                                                                                                                                                'and '
                                                                                                                                                'repeat '
                                                                                                                                                'the '
                                                                                                                                                'same '
                                                                                                                                                'operation; '
                                                                                                                                                'database '
                                                                                                                                                'rollback '
                                                                                                                                                'is '
                                                                                                                                                'not '
                                                                                                                                                'automatic.',
 'AI: сначала повторите незавершённый этап AI с исходным релизом через «Повторить AI». Основной стек уже готов.': 'AI: use Retry AI with '
                                                                                                                  'the original release to '
                                                                                                                  'finish the pending AI '
                                                                                                                  'stage first. The core '
                                                                                                                  'stack is already ready.',
 'ПРЕДУПРЕЖДЕНИЕ AI: ': 'AI WARNING: ',
 'Результат AI сохранён отдельно; общий отчёт обновить не удалось.': 'AI result saved separately; could not update the main report.',
 'Сначала сохраните онлайн или офлайн активацию App на вкладке площадки.': 'Save online or offline App activation on the Site tab first.',
 '{v0}: установка Manager не найдена. Для первичного развёртывания выберите «Установить» с релизом v0.2. Обновление доступно после завершения установки.': '{v0}: '
                                                                                                                                                           'no '
                                                                                                                                                           'Manager '
                                                                                                                                                           'installation '
                                                                                                                                                           'found. '
                                                                                                                                                           'Select '
                                                                                                                                                           'Install '
                                                                                                                                                           'for '
                                                                                                                                                           'a '
                                                                                                                                                           'new '
                                                                                                                                                           'deployment. '
                                                                                                                                                           'Update '
                                                                                                                                                           'is '
                                                                                                                                                           'available '
                                                                                                                                                           'after '
                                                                                                                                                           'installation '
                                                                                                                                                           'completes.',
 'Не удалось очистить временный inbox на одном из серверов; удалите его после проверки операции.': "Could not clean a server's temporary "
                                                                                                   'inbox; remove it after checking the '
                                                                                                   'operation.',
 'AI: не удалось записать отдельный журнал; журнал основного стека сохранён.': 'AI: could not save its separate journal; the core stack '
                                                                               'journal is preserved.',
 'AI: временный каталог не удалось очистить; основной стек не затронут.': 'AI: could not clean the temporary folder; the core stack is '
                                                                          'unaffected.',
 'Сохранено в vault': 'Saved in vault',
 'Доступ администратора App': 'App administrator access',
 'Скопировано в буфер обмена.': 'Copied to clipboard.',
 'ProdCast Manager {v0} — установка и обновление': 'ProdCast Manager {v0} - installation and updates',
 'SSH порт': 'SSH port',
 'SSH пользователь': 'SSH user',
 'Вход': 'Authentication',
 'Путь к SSH-ключу': 'SSH key path',
 'Новая площадка: введите адреса и SSH-доступ. Данные прежней площадки сохранены.': 'New site: enter addresses and SSH access. Previous '
                                                                                    'site data is preserved.',
 'Прежний пароль vault не подошёл либо файл повреждён. Исходный vault не изменён.': 'The old vault password is incorrect or the file is '
                                                                                    'damaged. The original vault is unchanged.',
 'Данные доступа': 'Access details',
 '{v0}\nАдрес: {v1}\nВыдан: {v2}\nДействует до: {v3}\nSHA256 сертификата: {v4}\nSHA256 корневого CA: {v5}': '{v0}\n'
                                                                                                            'Address: {v1}\n'
                                                                                                            'Issuer: {v2}\n'
                                                                                                            'Valid until: {v3}\n'
                                                                                                            'Certificate SHA256: {v4}\n'
                                                                                                            'Root CA SHA256: {v5}',
 'Пароль копируется полностью, даже когда скрыт звёздочками.': 'The complete password is copied even when hidden by asterisks.',
 '1. Серверы': '1. Servers',
 '2. Площадка': '2. Site',
 '3. Сертификат App': '3. App certificate',
 '4. Установка и обновление': '4. Installation and updates',
 'ID площадки': 'Site ID',
 'HTTPS адрес App': 'App HTTPS address',
 'IPv4 рабочего ПК администратора': 'Administrator PC IPv4',
 'Имя администратора App': 'App administrator user name',
 'Email администратора': 'Administrator email',
 'Свободная подсеть Docker /24': 'Unused Docker /24 subnet',
 'План': 'Plan',
 'Проверить доступ': 'Check access',
 'Установить': 'Install',
 'Обновить': 'Update',
 'Состояние': 'Status',
 'Резервная копия': 'Backup',
 'Повторить AI': 'Retry AI',
 'Копировать выделенное': 'Copy selection',
 'Копировать всё': 'Copy all',
 'Выделить всё': 'Select all',
 'Журнал этого запуска: ': 'Session log: ',
 'Проверяется только выбранная VM. Пароль для получения отпечатка не нужен.': 'Only the selected VM is checked. No password is needed to '
                                                                              'retrieve its fingerprint.',
 'Получить отпечаток без отправки пароля': 'Get fingerprint without sending password',
 'Использовать эти данные': 'Use these details',
 'Новая площадка — будет сохранена в data/sites рядом с Manager': 'New site - will be saved in data/sites beside Manager',
 'Конфигурация сохранена рядом с Manager.': 'Configuration saved beside Manager.',
 'Данные доступа сохранены в portable-площадке; пароль хранилища больше не требуется.': 'Access details saved in the portable site; a '
                                                                                        'vault password is no longer required.',
 'Нет прав записи в папку Manager. Распакуйте приложение в доступную для записи папку.': 'No write access to the Manager folder. Extract '
                                                                                         'the application to a writable folder.',
 'Адрес сайта клиента (https://имя)': 'Client website address (https://name)',
 'PFX / P12 файл': 'PFX / P12 file',
 'Пароль PFX': 'PFX password',
 'Цепочка CA в PEM (если нет в PFX)': 'CA chain in PEM (if missing from PFX)',
 'Сертификат организации ещё не загружен из vault.': 'Corporate certificate has not been loaded from the vault yet.',
 'В vault нет сертификата организации. Используется внутренний сертификат Manager.': "No corporate certificate in the vault. Manager's "
                                                                                     'internal certificate is used.',
 'Операция выполняется': 'Operation in progress',
 'Дождитесь завершения текущего шага. Отключение SSH может оставить операцию незавершённой.': 'Wait for the current operation. '
                                                                                              'Disconnecting SSH may leave it unfinished.',
 'Папка логов недоступна': 'Log folder unavailable',
 'Адрес App': 'App address',
 'Логин': 'User name',
 'Пароль': 'Password',
 'Копировать': 'Copy',
 'Пароль SSH': 'SSH password',
 'Пароль SSH-ключа': 'SSH key passphrase',
 'Пароль sudo (Linux)': 'sudo password (Linux)',
 'Подключение к {v0}:{v1}…': 'Connecting to {v0}:{v1}...',
 'Конфигурация': 'Configuration',
 'Импорт прежней площадки': 'Import previous site',
 'Введите прежний пароль vault один раз. После импорта он больше не понадобится.': 'Enter the original vault password once. It will no '
                                                                                   'longer be needed after import.',
 'Выберите PFX / P12 файл.': 'Select a PFX / P12 file.',
 'Сохранено в vault; для установленной площадки нажмите «Применить»': 'Saved in vault; for an installed site, click Apply',
 'Проверка пройдена; ещё не сохранено в vault': 'Validation passed; not yet saved in vault',
 'Импорт PFX': 'Import PFX',
 'Доступ App': 'App access',
 'Начальный пароль появится после начала установки этой площадки.': 'The initial password becomes available after installation starts for '
                                                                    'this site.',
 'Логи': 'Logs',
 'Выберите полный релиз ZIP или каталог': 'Select a complete release ZIP or folder',
 'Проверка': 'Validation',
 'Не удалось создать logs рядом с EXE. Переместите приложение в папку с правом записи.\n': 'Could not create logs beside the EXE. Move the '
                                                                                           'application to a writable folder.\n',
 'Начальные данные установки. Если пароль меняли в App, используйте новый.': 'Initial installation credentials. If the password was '
                                                                             'changed in App, use the new one.',
 'Показать пароль': 'Show password',
 'Закрыть': 'Close',
 'Пять VM · App / DB + Redis / AI + Ollama / Worker 01 / Worker 02': 'App / DB + Redis / optional AI + Ollama / Worker 01 / Worker 02',
 'Установка и обновление через SSH. Состояние сохраняется в журнале площадки.': 'Installation and updates over SSH. State is saved in the '
                                                                                'site journal.',
 'Установить AI': 'Install AI',
 'Сверьте SHA256 ключа каждого сервера с его администратором. Доступ сохраняется в папке площадки рядом с Manager.\nSudo-пароль может отличаться от SSH-пароля. Для root и sudo без пароля оставьте поле пустым.': 'Verify '
                                                                                                                                                                                                                   'each '
                                                                                                                                                                                                                   "server's "
                                                                                                                                                                                                                   'SHA256 '
                                                                                                                                                                                                                   'fingerprint '
                                                                                                                                                                                                                   'with '
                                                                                                                                                                                                                   'its '
                                                                                                                                                                                                                   'administrator. '
                                                                                                                                                                                                                   'Access '
                                                                                                                                                                                                                   'is '
                                                                                                                                                                                                                   'saved '
                                                                                                                                                                                                                   'beside '
                                                                                                                                                                                                                   'Manager.\n'
                                                                                                                                                                                                                   'The '
                                                                                                                                                                                                                   'sudo '
                                                                                                                                                                                                                   'password '
                                                                                                                                                                                                                   'may '
                                                                                                                                                                                                                   'differ '
                                                                                                                                                                                                                   'from '
                                                                                                                                                                                                                   'SSH. '
                                                                                                                                                                                                                   'Leave '
                                                                                                                                                                                                                   'it '
                                                                                                                                                                                                                   'blank '
                                                                                                                                                                                                                   'for '
                                                                                                                                                                                                                   'root '
                                                                                                                                                                                                                   'or '
                                                                                                                                                                                                                   'passwordless '
                                                                                                                                                                                                                   'sudo.',
 'Открыть site.json': 'Open site.json',
 'Новая площадка': 'New site',
 'Сохранить конфигурацию': 'Save configuration',
 'AI использует доступный GPU с готовым драйвером либо CPU. Manager не устанавливает драйверы.\nДля PFX используйте вкладку «Сертификат App», сохранив здесь внутренний адрес (для новой площадки — https://IP_App).\nИзменение адресов выбирает отдельную площадку.': 'AI '
                                                                                                                                                                                                                                                                       'uses '
                                                                                                                                                                                                                                                                       'an '
                                                                                                                                                                                                                                                                       'available '
                                                                                                                                                                                                                                                                       'GPU '
                                                                                                                                                                                                                                                                       'with '
                                                                                                                                                                                                                                                                       'a '
                                                                                                                                                                                                                                                                       'preinstalled '
                                                                                                                                                                                                                                                                       'driver, '
                                                                                                                                                                                                                                                                       'or '
                                                                                                                                                                                                                                                                       'CPU. '
                                                                                                                                                                                                                                                                       'Manager '
                                                                                                                                                                                                                                                                       'does '
                                                                                                                                                                                                                                                                       'not '
                                                                                                                                                                                                                                                                       'install '
                                                                                                                                                                                                                                                                       'drivers.\n'
                                                                                                                                                                                                                                                                       'For '
                                                                                                                                                                                                                                                                       'PFX, '
                                                                                                                                                                                                                                                                       'use '
                                                                                                                                                                                                                                                                       'the '
                                                                                                                                                                                                                                                                       'App '
                                                                                                                                                                                                                                                                       'certificate '
                                                                                                                                                                                                                                                                       'tab '
                                                                                                                                                                                                                                                                       'and '
                                                                                                                                                                                                                                                                       'keep '
                                                                                                                                                                                                                                                                       'the '
                                                                                                                                                                                                                                                                       'internal '
                                                                                                                                                                                                                                                                       'address '
                                                                                                                                                                                                                                                                       'here '
                                                                                                                                                                                                                                                                       '(https://IP_App '
                                                                                                                                                                                                                                                                       'for '
                                                                                                                                                                                                                                                                       'a '
                                                                                                                                                                                                                                                                       'new '
                                                                                                                                                                                                                                                                       'site).\n'
                                                                                                                                                                                                                                                                       'Changing '
                                                                                                                                                                                                                                                                       'core '
                                                                                                                                                                                                                                                                       'VM '
                                                                                                                                                                                                                                                                       'addresses '
                                                                                                                                                                                                                                                                       'selects '
                                                                                                                                                                                                                                                                       'a '
                                                                                                                                                                                                                                                                       'separate '
                                                                                                                                                                                                                                                                       'site.',
 'Подключение активации App…': 'App activation connection...',
 'Полный релиз ZIP / каталог:': 'Complete release ZIP / folder:',
 'Каталог…': 'Folder...',
 'SHA256 manifest релиза:': 'Release manifest SHA256:',
 'Данные доступа сохраняются автоматически рядом с Manager.': 'Access details are saved automatically beside Manager.',
 'Сохранить данные доступа': 'Save access details',
 'Копировать весь лог': 'Copy entire log',
 'Открыть папку логов': 'Open log folder',
 'Обновление требует окна обслуживания. При ошибке сохраняются данные и журнал; повторите ту же операцию. Автоматический откат БД не выполняется.': 'Updates '
                                                                                                                                                    'require '
                                                                                                                                                    'a '
                                                                                                                                                    'maintenance '
                                                                                                                                                    'window. '
                                                                                                                                                    'On '
                                                                                                                                                    'error, '
                                                                                                                                                    'data '
                                                                                                                                                    'and '
                                                                                                                                                    'journal '
                                                                                                                                                    'are '
                                                                                                                                                    'preserved; '
                                                                                                                                                    'repeat '
                                                                                                                                                    'the '
                                                                                                                                                    'same '
                                                                                                                                                    'operation. '
                                                                                                                                                    'Database '
                                                                                                                                                    'rollback '
                                                                                                                                                    'is '
                                                                                                                                                    'not '
                                                                                                                                                    'automatic.',
 'Загружена сохранённая конфигурация: ': 'Saved configuration loaded: ',
 'Подключение активации App сохранено.': 'App activation connection saved.',
 'Готовый офлайн-файл проверен и импортирован.': 'Issued offline file verified and imported.',
 'Доверенный ключ сервера SHA256:': 'Trusted server key SHA256:',
 'SSH порт должен быть от 1 до 65535': 'SSH port must be between 1 and 65535',
 '. Исходная папка не изменена.': '. The original folder is unchanged.',
 'Площадка: ': 'Site: ',
 'Импорт отменён; существующий vault не изменён.': 'Import cancelled; the existing vault is unchanged.',
 '. Сохраните всю папку площадки.': '. Keep the entire site folder.',
 'Сертификат организации для сайта ProdCast': 'Corporate certificate for the ProdCast website',
 'Выберите PFX/P12, содержащий серверный сертификат и приватный ключ. Пароль PFX нужен только для открытия файла.\nДля существующей площадки внутренний HTTPS адрес на вкладке «Площадка» менять не нужно.': 'Select '
                                                                                                                                                                                                             'a '
                                                                                                                                                                                                             'PFX/P12 '
                                                                                                                                                                                                             'containing '
                                                                                                                                                                                                             'the '
                                                                                                                                                                                                             'server '
                                                                                                                                                                                                             'certificate '
                                                                                                                                                                                                             'and '
                                                                                                                                                                                                             'private '
                                                                                                                                                                                                             'key. '
                                                                                                                                                                                                             'Its '
                                                                                                                                                                                                             'password '
                                                                                                                                                                                                             'is '
                                                                                                                                                                                                             'only '
                                                                                                                                                                                                             'used '
                                                                                                                                                                                                             'to '
                                                                                                                                                                                                             'open '
                                                                                                                                                                                                             'the '
                                                                                                                                                                                                             'file.\n'
                                                                                                                                                                                                             'For '
                                                                                                                                                                                                             'an '
                                                                                                                                                                                                             'existing '
                                                                                                                                                                                                             'site, '
                                                                                                                                                                                                             'keep '
                                                                                                                                                                                                             'its '
                                                                                                                                                                                                             'internal '
                                                                                                                                                                                                             'HTTPS '
                                                                                                                                                                                                             'address '
                                                                                                                                                                                                             'on '
                                                                                                                                                                                                             'the '
                                                                                                                                                                                                             'Site '
                                                                                                                                                                                                             'tab '
                                                                                                                                                                                                             'unchanged.',
 'Выбрать…': 'Browse...',
 'Ключ из PFX сохраняется в данных площадки автоматически. Пароль старого vault нужен только при первом импорте.\nПереносите всю папку Manager; она содержит доступ к серверам. Приватный ключ CA организации не требуется.': 'The '
                                                                                                                                                                                                                              'PFX '
                                                                                                                                                                                                                              'key '
                                                                                                                                                                                                                              'is '
                                                                                                                                                                                                                              'saved '
                                                                                                                                                                                                                              'automatically '
                                                                                                                                                                                                                              'in '
                                                                                                                                                                                                                              'the '
                                                                                                                                                                                                                              'site '
                                                                                                                                                                                                                              'data. '
                                                                                                                                                                                                                              'An '
                                                                                                                                                                                                                              'old '
                                                                                                                                                                                                                              'vault '
                                                                                                                                                                                                                              'password '
                                                                                                                                                                                                                              'is '
                                                                                                                                                                                                                              'only '
                                                                                                                                                                                                                              'needed '
                                                                                                                                                                                                                              'for '
                                                                                                                                                                                                                              'initial '
                                                                                                                                                                                                                              'import.\n'
                                                                                                                                                                                                                              'Transfer '
                                                                                                                                                                                                                              'the '
                                                                                                                                                                                                                              'entire '
                                                                                                                                                                                                                              'Manager '
                                                                                                                                                                                                                              'folder; '
                                                                                                                                                                                                                              'it '
                                                                                                                                                                                                                              'contains '
                                                                                                                                                                                                                              'server '
                                                                                                                                                                                                                              'access. '
                                                                                                                                                                                                                              'The '
                                                                                                                                                                                                                              'corporate '
                                                                                                                                                                                                                              'CA '
                                                                                                                                                                                                                              'private '
                                                                                                                                                                                                                              'key '
                                                                                                                                                                                                                              'is '
                                                                                                                                                                                                                              'not '
                                                                                                                                                                                                                              'required.',
 'Проверить PFX': 'Validate PFX',
 'Сохранить сертификат': 'Save certificate',
 'Показать сохранённый сертификат': 'Show saved certificate',
 'Применить сертификат на App': 'Apply certificate to App',
 'Импорт сохраняет сертификат локально. «Применить» подключается только к App и перезапускает веб-сервисы — нужно окно обслуживания.\nПри первой установке и последующих обновлениях сохранённый сертификат применяется автоматически.\nDNS клиента должен указывать имя сайта на IP App. ПК пользователей должны доверять CA организации. Автопродление PFX не выполняется.': 'Import '
                                                                                                                                                                                                                                                                                                                                                                               'saves '
                                                                                                                                                                                                                                                                                                                                                                               'the '
                                                                                                                                                                                                                                                                                                                                                                               'certificate '
                                                                                                                                                                                                                                                                                                                                                                               'locally. '
                                                                                                                                                                                                                                                                                                                                                                               'Apply '
                                                                                                                                                                                                                                                                                                                                                                               'connects '
                                                                                                                                                                                                                                                                                                                                                                               'only '
                                                                                                                                                                                                                                                                                                                                                                               'to '
                                                                                                                                                                                                                                                                                                                                                                               'App '
                                                                                                                                                                                                                                                                                                                                                                               'and '
                                                                                                                                                                                                                                                                                                                                                                               'restarts '
                                                                                                                                                                                                                                                                                                                                                                               'web '
                                                                                                                                                                                                                                                                                                                                                                               'services; '
                                                                                                                                                                                                                                                                                                                                                                               'schedule '
                                                                                                                                                                                                                                                                                                                                                                               'maintenance.\n'
                                                                                                                                                                                                                                                                                                                                                                               'The '
                                                                                                                                                                                                                                                                                                                                                                               'saved '
                                                                                                                                                                                                                                                                                                                                                                               'certificate '
                                                                                                                                                                                                                                                                                                                                                                               'is '
                                                                                                                                                                                                                                                                                                                                                                               'applied '
                                                                                                                                                                                                                                                                                                                                                                               'automatically '
                                                                                                                                                                                                                                                                                                                                                                               'during '
                                                                                                                                                                                                                                                                                                                                                                               'installation '
                                                                                                                                                                                                                                                                                                                                                                               'and '
                                                                                                                                                                                                                                                                                                                                                                               'updates.\n'
                                                                                                                                                                                                                                                                                                                                                                               'Client '
                                                                                                                                                                                                                                                                                                                                                                               'DNS '
                                                                                                                                                                                                                                                                                                                                                                               'must '
                                                                                                                                                                                                                                                                                                                                                                               'point '
                                                                                                                                                                                                                                                                                                                                                                               'to '
                                                                                                                                                                                                                                                                                                                                                                               'App. '
                                                                                                                                                                                                                                                                                                                                                                               'User '
                                                                                                                                                                                                                                                                                                                                                                               'PCs '
                                                                                                                                                                                                                                                                                                                                                                               'must '
                                                                                                                                                                                                                                                                                                                                                                               'trust '
                                                                                                                                                                                                                                                                                                                                                                               'the '
                                                                                                                                                                                                                                                                                                                                                                               'corporate '
                                                                                                                                                                                                                                                                                                                                                                               'CA. '
                                                                                                                                                                                                                                                                                                                                                                               'PFX '
                                                                                                                                                                                                                                                                                                                                                                               'auto-renewal '
                                                                                                                                                                                                                                                                                                                                                                               'is '
                                                                                                                                                                                                                                                                                                                                                                               'not '
                                                                                                                                                                                                                                                                                                                                                                               'supported.',
 '. Сервер пока не изменён.': '. The server is not changed yet.',
 'Не удалось прочитать файлы или сохранить vault. Проверьте доступ и пароль vault.': 'Could not read files or save the vault. Check file '
                                                                                     'access and vault password.',
 '\nНе удалось записать локальный лог: ': '\nCould not write the local log: ',
 'План установки (AI — отдельный необязательный этап):\n': 'Installation plan (AI is a separate optional stage):\n',
 'Перезапуск веб-сервисов App. Адрес: ': 'Restarting App web services. Address: ',
 'Обновление остановит доступ к App и планировщик до завершения.': 'Update will stop App access and the scheduler until completion.',
 'Будет выполнена выбранная операция на этих VM.': 'The selected operation will run on these VMs.',
 'Запуск операции': 'Start operation',
 'Пароли / ключ сервера': 'Passwords / host key',
 'Локальные логи: ': 'Local logs: ',
 'Не удалось загрузить сохранённую конфигурацию: ': 'Could not load saved configuration: ',
 'Диагностика SSH': 'SSH diagnostics',
 'Открыта portable-площадка: ': 'Portable site opened: ',
 'Не удалось прочитать или сохранить данные доступа: ': 'Could not read or save access details: ',
 'Сертификат организации сохранён в зашифрованном vault для ': 'Corporate certificate saved in the encrypted vault for ',
 'сначала импортируйте PFX': 'import a PFX first',
 '\n\nПродолжить?': '\n\nContinue?',
 'Сверка SSH ключа': 'Verify SSH host key',
 'Сервер {v0}:{v1}\n\n{v2}\n\nСверьте этот отпечаток через консоль VM или с администратором. Он совпадает?': 'Server {v0}:{v1}\n'
                                                                                                             '\n'
                                                                                                             '{v2}\n'
                                                                                                             '\n'
                                                                                                             'Compare this fingerprint '
                                                                                                             'with the VM console or '
                                                                                                             'administrator. Does it '
                                                                                                             'match?',
 'Отпечаток подтверждён. Сохраните окно и конфигурацию площадки.': 'Fingerprint confirmed. Save this dialog and the site configuration.',
 'Отпечаток не подтверждён; доверенный ключ не изменён.': 'Fingerprint not confirmed; the trusted key is unchanged.',
 'Эта площадка уже есть в data/sites. Откройте её site.json из папки Manager.': 'This site already exists in data/sites. Open its '
                                                                                'site.json from the Manager folder.',
 'Импорт состояния через символические ссылки запрещён': 'Importing state through symbolic links is not allowed',
 'Путь площадки выходит за пределы portable-папки': 'The site path is outside the portable folder',
 'В истории найдена символическая ссылка': 'A symbolic link was found in history',
 'Не найден secrets.key. Восстановите его из копии этой площадки; новый ключ создавать нельзя.': 'secrets.key is missing. Restore it from '
                                                                                                 "this site's backup; do not create a new "
                                                                                                 'key.',
 'Введите прежний пароль vault один раз для импорта площадки.': 'Enter the original vault password once to import the site.',
 'установка NVIDIA-драйвера и сборка модулей ядра': 'installing NVIDIA driver and building kernel modules',
 'драйвер установлен; для GPU могут потребоваться перезагрузка и регистрация ключа Secure Boot; продолжаем с доступными ресурсами': 'driver '
                                                                                                                                    'installed; '
                                                                                                                                    'GPU '
                                                                                                                                    'may '
                                                                                                                                    'need '
                                                                                                                                    'a '
                                                                                                                                    'reboot '
                                                                                                                                    'and '
                                                                                                                                    'Secure '
                                                                                                                                    'Boot '
                                                                                                                                    'key '
                                                                                                                                    'enrolment; '
                                                                                                                                    'continuing '
                                                                                                                                    'with '
                                                                                                                                    'available '
                                                                                                                                    'resources',
 'загрузка контейнеров AI из релиза': 'loading AI containers from the release',
 'скачивание Ollama; длительность зависит от скорости сети': 'downloading Ollama; duration depends on network speed',
 'скачивание модели Ollama': 'downloading the Ollama model',
 'проверка генерации ответа; на CPU может занять несколько минут': 'checking response generation; CPU execution may take several minutes',
 'Подключение к {v0}…': 'Connecting to {v0}...',
 '{v0} — демонстрационный адрес из шаблона. На вкладке «Серверы» замените его реальным IP виртуальной машины, затем повторите получение отпечатка.': '{v0} '
                                                                                                                                                     'is '
                                                                                                                                                     'a '
                                                                                                                                                     'template '
                                                                                                                                                     'address. '
                                                                                                                                                     'Enter '
                                                                                                                                                     'the '
                                                                                                                                                     'actual '
                                                                                                                                                     'VM '
                                                                                                                                                     'IP '
                                                                                                                                                     'on '
                                                                                                                                                     'the '
                                                                                                                                                     'Servers '
                                                                                                                                                     'tab '
                                                                                                                                                     'and '
                                                                                                                                                     'retry '
                                                                                                                                                     'the '
                                                                                                                                                     'fingerprint '
                                                                                                                                                     'scan.',
 '{v0}: TCP доступен. Ожидание ответа SSH…': '{v0}: TCP connected. Waiting for SSH...',
 'пустой ответ': 'empty response',
 'ответ не содержит единственного служебного блока': 'response does not contain exactly one service block',
 'PowerShell вернул CLIXML вместо текстового ответа': 'PowerShell returned CLIXML instead of a text response',
 '{v0}: проверка ОС и прав — {v1}. Проверьте запуск PowerShell/Python через SSH и используйте актуальную версию Manager.': '{v0}: OS and '
                                                                                                                           'permissions '
                                                                                                                           'check - {v1}. '
                                                                                                                           'Check '
                                                                                                                           'PowerShell/Python '
                                                                                                                           'over SSH and '
                                                                                                                           'use the '
                                                                                                                           'current '
                                                                                                                           'Manager '
                                                                                                                           'version.',
 'Получение отпечатка отменено.': 'Fingerprint scan cancelled.',
 '{v0}: TCP-подключение не установлено за {v1:g} с. Проверьте IP, SSH-порт, VPN/маршрут и правила firewall. Пароль и SSH-ключ ещё не использовались.': '{v0}: '
                                                                                                                                                       'TCP '
                                                                                                                                                       'connection '
                                                                                                                                                       'timed '
                                                                                                                                                       'out '
                                                                                                                                                       'after '
                                                                                                                                                       '{v1:g} '
                                                                                                                                                       's. '
                                                                                                                                                       'Check '
                                                                                                                                                       'IP, '
                                                                                                                                                       'SSH '
                                                                                                                                                       'port, '
                                                                                                                                                       'VPN/route '
                                                                                                                                                       'and '
                                                                                                                                                       'firewall. '
                                                                                                                                                       'No '
                                                                                                                                                       'password '
                                                                                                                                                       'or '
                                                                                                                                                       'SSH '
                                                                                                                                                       'key '
                                                                                                                                                       'has '
                                                                                                                                                       'been '
                                                                                                                                                       'used '
                                                                                                                                                       'yet.',
 '{v0}: соединение отклонено. Проверьте, запущена ли служба SSH и слушает ли она этот порт.': '{v0}: connection refused. Check the SSH '
                                                                                              'service and listening port.',
 '{v0}: ошибка сети ({v1}). Проверьте адрес, VPN/маршрут и доступность VM.': '{v0}: network error ({v1}). Check the address, VPN/route and '
                                                                             'VM availability.',
 '{v0}: отпечаток получен; требуется сверка с консолью VM.': '{v0}: fingerprint received; verify it against the VM console.',
 '{v0}: проверка ОС и прав — повреждён или неполон служебный ответ SSH. Установка не продолжена.': '{v0}: OS and permissions check - '
                                                                                                   'damaged or incomplete SSH response. '
                                                                                                   'Installation did not continue.',
 '{v0}: передача {v1}': '{v0}: uploading {v1}',
 '{v0}: {v1} — отсутствует однозначный служебный ответ сервера; проверьте защищённый журнал на VM': '{v0}: {v1} - no unambiguous service '
                                                                                                    'response; check the protected log on '
                                                                                                    'the VM',
 '{v0}: TCP-порт доступен, но корректное SSH-приветствие не получено. Возможно, указан порт другой службы, SSH не отвечает или соединение закрывает firewall/прокси. Причина: {v1}': '{v0}: '
                                                                                                                                                                                     'TCP '
                                                                                                                                                                                     'port '
                                                                                                                                                                                     'is '
                                                                                                                                                                                     'reachable '
                                                                                                                                                                                     'but '
                                                                                                                                                                                     'no '
                                                                                                                                                                                     'valid '
                                                                                                                                                                                     'SSH '
                                                                                                                                                                                     'greeting '
                                                                                                                                                                                     'was '
                                                                                                                                                                                     'received. '
                                                                                                                                                                                     'Wrong '
                                                                                                                                                                                     'service '
                                                                                                                                                                                     'port, '
                                                                                                                                                                                     'unresponsive '
                                                                                                                                                                                     'SSH '
                                                                                                                                                                                     'or '
                                                                                                                                                                                     'a '
                                                                                                                                                                                     'firewall/proxy '
                                                                                                                                                                                     'may '
                                                                                                                                                                                     'be '
                                                                                                                                                                                     'the '
                                                                                                                                                                                     'cause: '
                                                                                                                                                                                     '{v1}',
 '{v0}: {v1} — повреждён служебный ответ сервера; проверьте защищённый журнал на VM': '{v0}: {v1} - damaged service response; check the '
                                                                                      'protected log on the VM',
 '{v0}: сервер ответил по SSH. Обмен ключами…': '{v0}: SSH responded. Exchanging keys...',
 '{v0}: SSH ответил, но обмен ключами не завершился. Проверьте журнал sshd, ограничения соединений и совместимость алгоритмов. Причина: {v1}': '{v0}: '
                                                                                                                                               'SSH '
                                                                                                                                               'responded '
                                                                                                                                               'but '
                                                                                                                                               'key '
                                                                                                                                               'exchange '
                                                                                                                                               'did '
                                                                                                                                               'not '
                                                                                                                                               'finish. '
                                                                                                                                               'Check '
                                                                                                                                               'sshd '
                                                                                                                                               'logs, '
                                                                                                                                               'connection '
                                                                                                                                               'limits '
                                                                                                                                               'and '
                                                                                                                                               'supported '
                                                                                                                                               'algorithms. '
                                                                                                                                               'Cause: '
                                                                                                                                               '{v1}',
 '{v0}: шаг выполняется, прошло {v1} с': '{v0}: step running, elapsed {v1} s',
 'журнал на Linux VM: /var/lib/prodcast-manager/operation.log': 'Linux VM log: /var/lib/prodcast-manager/operation.log',
 '{v0}: передано {v1} / {v2} МБ': '{v0}: uploaded {v1} / {v2} MB',
 '{v0}: диагностика сервера сохранена на этом ПК: {v1}': '{v0}: server diagnostics saved on this PC: {v1}',
 '{v0}: не удалось сохранить диагностику сервера; основной журнал запуска находится в папке logs рядом с приложением': '{v0}: could not '
                                                                                                                       'save server '
                                                                                                                       'diagnostics; the '
                                                                                                                       'main session log '
                                                                                                                       'is in logs beside '
                                                                                                                       'the application',
 'Количество Workers': 'Number of Workers',
 'Язык / Language': 'Language / Язык',
 'Русский': 'Русский',
 'Дождитесь завершения операции перед сменой языка.': 'Wait for the operation to finish before changing language.',
 'Количество Workers установленной площадки менять нельзя. Для новой установки создайте отдельную площадку.': 'The Worker count of an '
                                                                                                              'initialized site cannot be '
                                                                                                              'changed here. Create a '
                                                                                                              'separate site for a new '
                                                                                                              'installation.',
 'App / DB + Redis / AI (по выбору) / Workers': 'App / DB + Redis / optional AI / Workers',
 'AI использует доступный GPU с готовым драйвером либо CPU. Manager не устанавливает драйверы.\nДля PFX используйте вкладку «Сертификат App», сохранив здесь внутренний адрес (для новой площадки — https://IP_App).\nИзменение адресов основных VM выбирает отдельную площадку.': 'AI '
                                                                                                                                                                                                                                                                                   'uses '
                                                                                                                                                                                                                                                                                   'an '
                                                                                                                                                                                                                                                                                   'available '
                                                                                                                                                                                                                                                                                   'GPU '
                                                                                                                                                                                                                                                                                   'with '
                                                                                                                                                                                                                                                                                   'a '
                                                                                                                                                                                                                                                                                   'preinstalled '
                                                                                                                                                                                                                                                                                   'driver, '
                                                                                                                                                                                                                                                                                   'or '
                                                                                                                                                                                                                                                                                   'CPU. '
                                                                                                                                                                                                                                                                                   'Manager '
                                                                                                                                                                                                                                                                                   'does '
                                                                                                                                                                                                                                                                                   'not '
                                                                                                                                                                                                                                                                                   'install '
                                                                                                                                                                                                                                                                                   'drivers.\n'
                                                                                                                                                                                                                                                                                   'For '
                                                                                                                                                                                                                                                                                   'PFX, '
                                                                                                                                                                                                                                                                                   'use '
                                                                                                                                                                                                                                                                                   'the '
                                                                                                                                                                                                                                                                                   'App '
                                                                                                                                                                                                                                                                                   'certificate '
                                                                                                                                                                                                                                                                                   'tab '
                                                                                                                                                                                                                                                                                   'and '
                                                                                                                                                                                                                                                                                   'keep '
                                                                                                                                                                                                                                                                                   'the '
                                                                                                                                                                                                                                                                                   'internal '
                                                                                                                                                                                                                                                                                   'address '
                                                                                                                                                                                                                                                                                   'here '
                                                                                                                                                                                                                                                                                   '(https://IP_App '
                                                                                                                                                                                                                                                                                   'for '
                                                                                                                                                                                                                                                                                   'a '
                                                                                                                                                                                                                                                                                   'new '
                                                                                                                                                                                                                                                                                   'site).\n'
                                                                                                                                                                                                                                                                                   'Changing '
                                                                                                                                                                                                                                                                                   'core '
                                                                                                                                                                                                                                                                                   'VM '
                                                                                                                                                                                                                                                                                   'addresses '
                                                                                                                                                                                                                                                                                   'selects '
                                                                                                                                                                                                                                                                                   'a '
                                                                                                                                                                                                                                                                                   'separate '
                                                                                                                                                                                                                                                                                   'site.',
 'Резервное копирование доступно после установки Manager на App, DB и выбранных Workers. Сначала завершите «Установить».': 'Backup is '
                                                                                                                           'available '
                                                                                                                           'after Manager '
                                                                                                                           'installs App, '
                                                                                                                           'DB and the '
                                                                                                                           'selected '
                                                                                                                           'Workers. '
                                                                                                                           'Complete '
                                                                                                                           'Install first.'}
