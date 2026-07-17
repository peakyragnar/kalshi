import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from kalshi_data.core.auth_client import sign


def test_signature_verifies_with_public_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ts, method, path = "1789000000000", "GET", "/trade-api/v2/portfolio/balance"
    sig = base64.b64decode(sign(key, ts, method, path))
    key.public_key().verify(
        sig,
        f"{ts}{method}{path}".encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=hashes.SHA256().digest_size),
        hashes.SHA256(),
    )  # raises on mismatch


def test_signed_message_binds_method_and_path():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    sig = base64.b64decode(sign(key, "1", "GET", "/a"))
    try:
        key.public_key().verify(
            sig, b"1GET/b",
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=hashes.SHA256().digest_size),
            hashes.SHA256(),
        )
        raise AssertionError("signature verified against wrong path")
    except Exception as e:
        assert "wrong path" not in str(e)


def test_private_key_loads_from_pem_roundtrip(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    loaded = serialization.load_pem_private_key(pem, password=None)
    assert loaded.key_size == 2048
