"""Safe environment preflight for Company OS local containers and servers.

Never logs raw secrets. It intentionally refuses weak bootstrap credentials
rather than starting with an unusable or insecure administrator account.
"""
import os
import re
import sys


class BootstrapConfigError(RuntimeError):
    """Expected, operator-actionable configuration error."""


def validate_bootstrap_env(environ=None) -> None:
    env = os.environ if environ is None else environ
    if env.get('APP_ENV', 'development').lower() == 'test' and env.get('DEMO_MODE', 'false').lower() == 'true':
        return  # pytest-only mode; never enable for a real server

    missing = [key for key in ('ADMIN_USERNAME', 'ADMIN_PASSWORD', 'SESSION_SECRET') if not env.get(key, '').strip()]
    if missing:
        raise BootstrapConfigError(
            'Missing required setting(s): '+', '.join(missing)+'. '
            'Create .env in the SAME folder as docker-compose.yml (not frontend/ or backend/). '
            'Run docker compose up -d --build --force-recreate.'
        )

    username = env['ADMIN_USERNAME'].strip()
    password = env['ADMIN_PASSWORD']
    secret = env['SESSION_SECRET']
    if not re.fullmatch(r'[A-Za-z0-9._-]{3,80}', username):
        raise BootstrapConfigError('ADMIN_USERNAME must be 3-80 characters: Latin letters, digits, period, underscore or hyphen.')
    if len(password) < 12 or password.upper().startswith(('REPLACE_', 'YOUR_OWN_', 'CHANGE_ME')):
        raise BootstrapConfigError(
            'ADMIN_PASSWORD is missing, still a placeholder, or too short (minimum: 12 characters). '
            'Set a UNIQUE strong password in the root .env, then recreate the backend container. '
            'Existing accounts are NOT reset by editing .env.'
        )
    if len(secret) < 32 or secret.upper().startswith(('REPLACE_', 'YOUR_GENERATED_', 'CHANGE_ME')):
        raise BootstrapConfigError('SESSION_SECRET must contain 32+ random characters, not a placeholder. Generate with Python secrets.token_urlsafe(48).')
    hr_key = env.get('HR_ENCRYPTION_KEY', '').strip()
    if hr_key:
        try:
            raw = bytes.fromhex(hr_key)
        except ValueError:
            raise BootstrapConfigError('HR_ENCRYPTION_KEY must be 64 hexadecimal characters (32 bytes).') from None
        if len(raw) != 32 or len(hr_key) != 64:
            raise BootstrapConfigError('HR_ENCRYPTION_KEY must be 64 hexadecimal characters (32 bytes).')


def main() -> int:
    try:
        validate_bootstrap_env()
    except BootstrapConfigError as exc:
        print('\n[Company OS] CONFIGURATION ERROR\n'+str(exc)+'\n', file=sys.stderr, flush=True)
        return 2
    print('[Company OS] Configuration preflight passed. ADMIN_USERNAME, password policy and session key look valid. (Secrets not printed.)', flush=True)
    if not os.environ.get('HR_ENCRYPTION_KEY'):
        print('[Company OS] NOTE: HR_ENCRYPTION_KEY unset; encrypted identity documents are unavailable.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
