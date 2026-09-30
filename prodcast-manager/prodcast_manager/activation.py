"""Client activation only. Signing keys and entitlement issuance stay on the authority."""
from .i18n import tr
import base64
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import UUID
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def installation_id(vault):
    return str(UUID(vault.data['installation_id']))


def validate_activation(value, identity):
    result=dict(value)
    tenant=result.get('tenant_id','')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,47}',tenant) or tenant=='default':
        raise ValueError(tr('Укажите ID компании, полученный с сервера активации.'))
    mode=result.get('mode')
    if mode=='online':
        url=result.get('url','');u=urlsplit(url)
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or any(c in url for c in '\r\n\x00'):
            raise ValueError(tr('Укажите HTTPS адрес сервера активации без пароля и параметров.'))
        if not u.path.strip('/'):
            result['url']=url.rstrip('/')+'/v1/decision'
        elif u.path!='/v1/decision':
            raise ValueError(tr('Адрес должен оканчиваться на /v1/decision или содержать только имя сервера.'))
        token=result.get('token','')
        if len(token)<32 or any(c in token for c in '\r\n\x00'):
            raise ValueError(tr('Укажите клиентский токен компании (не токен администратора).'))
        if result.get('ca_pem'):x509.load_pem_x509_certificate(result['ca_pem'].encode())
        return {k:result.get(k,'') for k in ('mode','tenant_id','url','token','ca_pem')}
    if mode!='offline':raise ValueError(tr('Выберите онлайн или офлайн активацию.'))
    raw=result.get('document','');public=result.get('public_key','')
    if len(raw.encode())>65536 or len(public.encode())>16384:raise ValueError(tr('Файл активации слишком большой.'))
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError(tr('Повторяющееся поле в файле активации.'))
            d[k]=v
        return d
    doc=json.loads(raw,object_pairs_hook=unique)
    if set(doc)!={'format_version','key_id','payload','signature'} or type(doc['format_version']) is not int or doc['format_version']!=1:
        raise ValueError(tr('Неподдерживаемый формат файла активации.'))
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',doc['key_id']):raise ValueError(tr('Некорректный ID публичного ключа.'))
    key=serialization.load_pem_public_key(public.encode())
    if not isinstance(key,Ed25519PublicKey):raise ValueError(tr('Требуется публичный ключ Ed25519; приватный ключ загружать нельзя.'))
    unsigned={k:v for k,v in doc.items() if k!='signature'}
    key.verify(base64.b64decode(doc['signature'],validate=True),json.dumps(unsigned,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii'))
    p=doc['payload']
    if p.get('installation_id')!=str(UUID(identity)) or p.get('tenant_id')!=tenant or p.get('environment')!='PROD' or p.get('product')!='ProdCast':
        raise ValueError(tr('Файл выпущен для другой установки, компании или среды.'))
    now=datetime.now(timezone.utc)
    start=datetime.fromisoformat(p['valid_from'].replace('Z','+00:00'));end=datetime.fromisoformat(p['expires_at'].replace('Z','+00:00'))
    if start.tzinfo is None or end.tzinfo is None or not start<=now<end:raise ValueError(tr('Файл активации ещё не действует или срок истёк.'))
    return {'mode':mode,'tenant_id':tenant,'document':raw,'public_key':public,'key_id':doc['key_id']}
