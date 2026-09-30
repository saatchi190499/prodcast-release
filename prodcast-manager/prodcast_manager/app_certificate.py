"""Import customer PKCS#12 credentials without writing plaintext keys locally."""
from .i18n import tr
import ipaddress
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.verification import PolicyBuilder, Store, VerificationError

from .config import file_lock, topology_hash


def client_hostname(url):
    u = urlsplit(url)
    if (u.scheme != 'https' or not u.hostname or u.username or u.password
            or u.port not in (None, 443) or u.path not in ('', '/') or u.query or u.fragment):
        raise ValueError(tr('Укажите полный адрес https://имя-сервера, без пути /login, логина и пароля; порт 443. Доменная зона может быть любой, .local не требуется.'))
    host = u.hostname.lower()
    if len(host) > 253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', p) for p in host.split('.')):
        raise ValueError(tr('Укажите корректное DNS-имя сайта клиента (для IDN используйте punycode).'))
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    raise ValueError(tr('Для сертификата организации укажите DNS-имя сайта, а не IP VM.'))


def validate_material(material):
    """Validate the complete supplied chain, name, usage, validity and key match."""
    host = client_hostname(material['url'])
    try:
        chain = x509.load_pem_x509_certificates(material['certificate'].encode('ascii'))
        roots = x509.load_pem_x509_certificates(material['ca'].encode('ascii'))
        key = serialization.load_pem_private_key(material['private_key'].encode('ascii'), None)
        leaf = chain[0]
        public = lambda k: k.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        if public(key.public_key()) != public(leaf.public_key()):
            raise ValueError(tr('Сертификат и приватный ключ не соответствуют друг другу.'))
        if not ((isinstance(key, rsa.RSAPrivateKey) and key.key_size >= 2048)
                or (isinstance(key, ec.EllipticCurvePrivateKey) and key.key_size >= 256)):
            raise ValueError(tr('Для HTTPS требуется ключ RSA от 2048 бит или EC от 256 бит.'))
        now = datetime.now(timezone.utc)
        for cert in [*chain, *roots]:
            if not cert.not_valid_before_utc <= now < cert.not_valid_after_utc:
                raise ValueError(tr('Сертификат или CA ещё не действует либо уже истёк.'))
        for root in roots:
            root.verify_directly_issued_by(root)
            if not root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
                raise ValueError(tr('Корневой сертификат должен быть сертификатом CA.'))
        verifier = (PolicyBuilder().store(Store(roots)).time(now).max_chain_depth(8)
                    .build_server_verifier(x509.DNSName(host)))
        verified = verifier.verify(leaf, chain[1:])
    except VerificationError:
        raise ValueError(tr('Не прошла проверка SAN, назначения Server Authentication или цепочки CA. Проверьте адрес сайта и приложите полную цепочку до корневого CA.')) from None
    except (IndexError, x509.ExtensionNotFound, UnsupportedAlgorithm):
        raise ValueError(tr('Неполный или неподдерживаемый сертификат HTTPS / цепочка CA.')) from None
    return verified


def read_pfx(data, password, url, ca_pem=b''):
    host = client_hostname(url)
    if len(data) > 16 * 1024 * 1024 or len(ca_pem) > 4 * 1024 * 1024:
        raise ValueError(tr('Слишком большой PFX или файл CA.'))
    try:
        key, leaf, extra = pkcs12.load_key_and_certificates(data, password.encode('utf-8') if password else None)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise ValueError(tr('Не удалось открыть PFX: проверьте пароль, формат и целостность файла.')) from None
    if key is None or leaf is None:
        raise ValueError(tr('PFX должен содержать серверный сертификат и его приватный ключ. Запросите экспорт с ключом.'))
    try:
        is_ca = leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound:
        is_ca = False
    if is_ca:
        raise ValueError(tr('Импортируйте серверный сертификат App, а не приватный ключ CA.'))
    try:
        additional = list(extra or []) + (x509.load_pem_x509_certificates(ca_pem) if ca_pem else [])
    except ValueError:
        raise ValueError(tr('Дополнительная цепочка CA должна быть в формате PEM.')) from None
    unique = {c.fingerprint(hashes.SHA256()): c for c in additional}
    roots, intermediates = [], []
    for c in unique.values():
        if c == leaf:
            continue
        (roots if c.subject == c.issuer else intermediates).append(c)
    if not roots:
        raise ValueError(tr('В PFX нет корневого CA. Выберите дополнительный PEM-файл с цепочкой CA организации.'))
    pem = lambda c: c.public_bytes(serialization.Encoding.PEM).decode('ascii')
    material = {'url': 'https://' + host, 'certificate': ''.join(map(pem, [leaf, *intermediates])),
                'private_key': key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                 serialization.NoEncryption()).decode('ascii'),
                'ca': ''.join(map(pem, roots))}
    verified = validate_material(material)
    # nginx expects the leaf first, followed by its actual issuing chain. Do not serve unrelated certificates.
    material['certificate'] = ''.join(map(pem, verified[:-1]))
    material['ca'] = pem(verified[-1])
    material['info'] = {'subject': leaf.subject.rfc4514_string(), 'issuer': leaf.issuer.rfc4514_string(),
                        'expires': leaf.not_valid_after_utc.isoformat(),
                        'sha256': leaf.fingerprint(hashes.SHA256()).hex(),
                        'ca_sha256': verified[-1].fingerprint(hashes.SHA256()).hex()}
    return material


def validate_for_site(material, site):
    validate_material(material)
    if client_hostname(material['url']) == urlsplit(site['public_url']).hostname.lower():
        raise ValueError(tr('Адрес клиента должен отличаться от внутреннего HTTPS адреса App на вкладке «Площадка». Для новой установки укажите там https://IP_App; адрес существующей площадки не меняйте.'))


def store_app_certificate(vault, site, material):
    validate_for_site(material, site)
    with file_lock(vault.path.parent / 'operation.lock'):
        if vault.data.get('topology') and vault.data['topology'] != topology_hash(site):
            raise ValueError(tr('Откройте исходную конфигурацию площадки. Для PFX не меняйте её внутренний HTTPS адрес.'))
        for name in ('journal.json', 'app-tls-journal.json'):
            path = vault.path.parent / name
            if path.exists() and json.loads(path.read_text('utf-8')).get('status') in ('running', 'failed'):
                raise ValueError(tr('Сначала завершите прерванную операцию с прежним сертификатом; затем импортируйте новый PFX.'))
        if vault.path.exists():
            folder = vault.path.parent / 'history'
            folder.mkdir(exist_ok=True)
            shutil.copy2(vault.path, folder / ('vault-before-app-pfx-' + uuid.uuid4().hex + '.json'))
        old = vault.data.get('app_tls')
        vault.data['app_tls'] = material
        try:
            vault.save()
        except Exception:
            if old is None:
                vault.data.pop('app_tls', None)
            else:
                vault.data['app_tls'] = old
            raise
