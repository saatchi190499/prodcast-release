"""Upgrade legacy certificate metadata without changing installation keys/trust."""
import shutil
import uuid
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization

def upgrade_legacy_certificates(vault):
    tls=vault.data.get('tls',{})
    if not tls:return False
    ca=x509.load_pem_x509_certificate(tls['ca.crt'].encode())
    key=serialization.load_pem_private_key(tls['ca.key'].encode(),password=None)
    public=lambda k:k.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
    if public(ca.public_key())!=public(key.public_key()):raise ValueError('Vault CA key mismatch')
    replacements={}
    for name,pem in tls.items():
        if not name.endswith('.crt'):continue
        cert=x509.load_pem_x509_certificate(pem.encode())
        missing=[]
        for kind in (x509.SubjectKeyIdentifier,x509.AuthorityKeyIdentifier):
            try:cert.extensions.get_extension_for_class(kind)
            except x509.ExtensionNotFound:missing.append(kind)
        if not missing:continue
        cert.verify_directly_issued_by(ca)
        builder=(x509.CertificateBuilder().subject_name(cert.subject).issuer_name(cert.issuer)
                 .public_key(cert.public_key()).serial_number(cert.serial_number)
                 .not_valid_before(cert.not_valid_before_utc).not_valid_after(cert.not_valid_after_utc))
        for extension in cert.extensions:builder=builder.add_extension(extension.value,extension.critical)
        if x509.SubjectKeyIdentifier in missing:
            builder=builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(cert.public_key()),False)
        if x509.AuthorityKeyIdentifier in missing:
            builder=builder.add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca.public_key()),False)
        replacements[name]=builder.sign(key,hashes.SHA256()).public_bytes(serialization.Encoding.PEM).decode()
    if not replacements:return False
    folder=vault.path.parent/'history';folder.mkdir(exist_ok=True)
    shutil.copy2(vault.path,folder/('vault-before-certificate-upgrade-'+uuid.uuid4().hex+'.json'))
    previous=dict(tls)
    tls.update(replacements)
    try:vault.save()
    except Exception:
        vault.data['tls']=previous;raise
    return True
