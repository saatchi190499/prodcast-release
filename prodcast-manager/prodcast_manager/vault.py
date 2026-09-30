import base64
import hashlib
import ipaddress
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from .config import atomic_json, topology_hash, file_lock, worker_roles

class Vault:
    def __init__(self,path,password):
        if len(password)<12: raise ValueError('Vault password must contain at least 12 characters')
        self.path=Path(path)
        doc=json.loads(self.path.read_text('utf-8')) if self.path.exists() else None
        if doc and doc['schema']!=1: raise ValueError('Unsupported vault')
        self.salt=base64.b64decode(doc['salt']) if doc else secrets.token_bytes(16)
        key=Scrypt(salt=self.salt,length=32,n=2**17,r=8,p=1).derive(password.encode())
        self.fernet=Fernet(base64.urlsafe_b64encode(key))
        self.data=json.loads(self.fernet.decrypt(doc['ciphertext'].encode())) if doc else {}
        self.loaded_ciphertext=doc['ciphertext'] if doc else None

    def save(self):
        with file_lock(self.path.with_suffix('.lock')):
            current=json.loads(self.path.read_text('utf-8'))['ciphertext'] if self.path.exists() else None
            if current!=self.loaded_ciphertext: raise RuntimeError('Vault changed in another process; reopen it instead of overwriting secrets')
            ciphertext=self.fernet.encrypt(json.dumps(self.data).encode()).decode()
            atomic_json(self.path,{'schema':1,'salt':base64.b64encode(self.salt).decode(),'ciphertext':ciphertext})
            self.loaded_ciphertext=ciphertext

    def initialize(self,c):
        fingerprint=topology_hash(c)
        if 'topology' in self.data:
            if self.data['topology']!=fingerprint: raise ValueError('Topology differs from encrypted installation state; use the original site file')
            if ensure_ai_certificate(self.data,c):self.save()
            return
        s={k:secrets.token_hex(32) for k in ('PG_ADMIN PW_APP PW_LICENSE PW_AI PW_W01 PW_W02 REDIS_ADMIN REDIS_APP REDIS_W01 REDIS_W02 DJANGO_KEY MODULE_KEY RESOLVE_KEY MEDIA_KEY SIGNING_KEY METRICS_KEY LICENSE_SALT LICENSE_BOOTSTRAP AI_KEY AI_BASIC ADMIN_PASSWORD SVC_W01 SVC_W02').split()}
        for role in worker_roles(c):
            for prefix in ('PW_W','REDIS_W','SVC_W'):
                s.setdefault(prefix+f'{int(role[6:]):02}',secrets.token_hex(32))
        # Windows complexity is independent of the random sample's character distribution.
        for k in list(s):
            if k=='ADMIN_PASSWORD' or k.startswith('SVC_W'):s[k]='Pc!9'+s[k]
        s['FERNET_KEY']=Fernet.generate_key().decode()
        salt=secrets.token_bytes(24)
        enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
        s['AI_HASH']='scrypt$16384$8$1$'+enc(salt)+'$'+enc(hashlib.scrypt(s['AI_BASIC'].encode(),salt=salt,n=16384,r=8,p=1,dklen=32))
        self.data.update(installation_id=secrets.token_hex(16),topology=fingerprint,secrets=s,tls=make_pki(c),ssh=self.data.get('ssh',{}))
        self.save()

def make_pki(c):
    now=datetime.now(timezone.utc)
    key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,c['site_id']+' CA')])
    ca=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5))
        .not_valid_after(now+timedelta(days=3650)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()),False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()),False)
        .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True).sign(key,hashes.SHA256()))
    pem=lambda k:k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
    cert=lambda x:x.public_bytes(serialization.Encoding.PEM).decode()
    out={'ca.crt':cert(ca),'ca.key':pem(key)}
    for n,names in {'postgres':[c['hosts']['db']['address'],'127.0.0.1'],
                    'redis':[c['hosts']['db']['address'],'127.0.0.1'],
                    'ai':([c['hosts']['ai']['address']] if c.get('install_ai',True) else [])+['127.0.0.1'],
                    'site':[urlsplit(c['public_url']).hostname,c['hosts']['app']['address'],'127.0.0.1'],
                    'license':['license-proxy','127.0.0.1']}.items():
        leaf=rsa.generate_private_key(public_exponent=65537,key_size=3072); san=[]
        for v in set(names)-{''}:
            try: san.append(x509.IPAddress(ipaddress.ip_address(v)))
            except ValueError: san.append(x509.DNSName(v))
        crt=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,n)]))
             .issuer_name(name).public_key(leaf.public_key()).serial_number(x509.random_serial_number())
             .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=365))
             .add_extension(x509.SubjectAlternativeName(san),False).add_extension(x509.BasicConstraints(False,None),True)
             .add_extension(x509.SubjectKeyIdentifier.from_public_key(leaf.public_key()),False)
             .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()),False)
             .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False).sign(key,hashes.SHA256()))
        out[n+'.crt']=cert(crt); out[n+'.key']=pem(leaf)
    return out


def ensure_ai_certificate(data,c):
    """Issue only the optional leaf, using the existing installation CA."""
    if not c.get('install_ai',True):return False
    address=ipaddress.ip_address(c['hosts']['ai']['address']);tls=data['tls']
    old=x509.load_pem_x509_certificate(tls['ai.crt'].encode())
    if address in old.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.IPAddress):return False
    ca=x509.load_pem_x509_certificate(tls['ca.crt'].encode())
    key=serialization.load_pem_private_key(tls['ca.key'].encode(),None)
    leaf=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    now=datetime.now(timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'ai')]))
        .issuer_name(ca.subject).public_key(leaf.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(address),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),False)
        .add_extension(x509.BasicConstraints(False,None),True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(leaf.public_key()),False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()),False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False).sign(key,hashes.SHA256()))
    tls['ai.crt']=cert.public_bytes(serialization.Encoding.PEM).decode()
    tls['ai.key']=leaf.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
    return True
