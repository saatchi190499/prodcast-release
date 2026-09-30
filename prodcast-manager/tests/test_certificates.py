from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from prodcast_manager.certificates import upgrade_legacy_certificates
from prodcast_manager.config import example
from prodcast_manager.vault import Vault

def test_legacy_certificate_upgrade_preserves_keys_trust_and_encrypted_backup(tmp_path):
    vault=Vault(tmp_path/'vault.json','long enough test password');vault.initialize(example())
    key=serialization.load_pem_private_key(vault.data['tls']['ca.key'].encode(),password=None)
    for name,pem in list(vault.data['tls'].items()):
        if not name.endswith('.crt'):continue
        c=x509.load_pem_x509_certificate(pem.encode())
        b=(x509.CertificateBuilder().subject_name(c.subject).issuer_name(c.issuer).public_key(c.public_key())
           .serial_number(c.serial_number).not_valid_before(c.not_valid_before_utc).not_valid_after(c.not_valid_after_utc))
        for extension in c.extensions:
            if not isinstance(extension.value,(x509.SubjectKeyIdentifier,x509.AuthorityKeyIdentifier)):
                b=b.add_extension(extension.value,extension.critical)
        vault.data['tls'][name]=b.sign(key,hashes.SHA256()).public_bytes(serialization.Encoding.PEM).decode()
    vault.save();original=dict(vault.data['tls']);encrypted=vault.path.read_bytes()
    assert upgrade_legacy_certificates(vault)
    assert next((tmp_path/'history').glob('vault-before-*.json')).read_bytes()==encrypted
    for name,pem in original.items():
        if name.endswith('.key'):assert vault.data['tls'][name]==pem;continue
        before=x509.load_pem_x509_certificate(pem.encode())
        after=x509.load_pem_x509_certificate(vault.data['tls'][name].encode())
        assert before.subject==after.subject and before.issuer==after.issuer
        assert before.serial_number==after.serial_number
        assert before.public_key().public_numbers()==after.public_key().public_numbers()
        after.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
        after.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier)
    assert not upgrade_legacy_certificates(vault)
    assert Vault(vault.path,'long enough test password').data==vault.data
