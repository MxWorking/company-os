"""Stable internal cryptographic root with no user-managed session/HR keys.

A hosted backend needs COMPANY_OS_INTERNAL_KEY, provisioned by the deploy system,
not by the account holder. Local/Docker use an auto-generated persistent key file.
Never commit the key or include it in web frontend environment variables.
"""
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from threading import Lock

_key: bytes | None = None
_lock = Lock()


def _local_file() -> Path:
    configured = os.environ.get('COMPANY_OS_KEY_PATH', '').strip()
    return Path(configured).expanduser() if configured else Path.home() / '.local' / 'share' / 'company-os' / 'internal.key'


def _read_or_create_local() -> bytes:
    path = _local_file()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
            stream.write(secrets.token_bytes(32))
    except FileExistsError:
        pass
    raw = path.read_bytes()
    if len(raw) != 32:
        raise RuntimeError('Local Company OS internal key file must contain exactly 32 bytes. Restore the original key; do not regenerate it when encrypted HR data exists.')
    return raw


def master_key() -> bytes:
    global _key
    if _key is not None:
        return _key
    with _lock:
        if _key is not None:
            return _key
        env_secret = os.environ.get('COMPANY_OS_INTERNAL_KEY', '')
        if env_secret:
            # The deployed value must originate from a cryptographic RNG; hash it
            # to normalize opaque Vercel secret strings into 256-bit root material.
            if len(env_secret) < 48 or env_secret.upper().startswith(('REPLACE_', 'CHANGE_ME')):
                raise RuntimeError('The automatically provisioned backend internal key is invalid.')
            _key = hashlib.sha256(env_secret.encode('utf-8')).digest()
        elif os.environ.get('VERCEL_ENV') in ('production', 'preview'):
            raise RuntimeError('Missing automatically provisioned backend internal crypto key. Request a protected Vercel project configuration; never bypass this check.')
        else:
            _key = _read_or_create_local()
        return _key


def subkey(purpose: str) -> bytes:
    return hmac.new(master_key(), ('company-os-2.6:' + purpose).encode('utf-8'), hashlib.sha256).digest()
