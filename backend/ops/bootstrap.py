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

    missing = [key for key in ('ADMIN_USERNAME', 'ADMIN_PASSWORD') if not env.get(key, '').strip()]
    if missing:
        raise BootstrapConfigError(
            'Missing required setting(s): '+', '.join(missing)+'. '
            'For Docker, create .env alongside docker-compose.yml; for Vercel, add the values in the backend project Environment Variables and redeploy.'
        )

    username = env['ADMIN_USERNAME'].strip()
    password = env['ADMIN_PASSWORD']
    if not re.fullmatch(r'[A-Za-z0-9._-]{3,80}', username):
        raise BootstrapConfigError('ADMIN_USERNAME must be 3-80 characters: Latin letters, digits, period, underscore or hyphen.')
    if len(password) < 12 or password.upper().startswith(('REPLACE_', 'YOUR_OWN_', 'CHANGE_ME')):
        raise BootstrapConfigError(
            'ADMIN_PASSWORD is missing, still a placeholder, or too short (minimum: 12 characters). '
            'Set a UNIQUE strong password in the backend environment. '
            'The hosted backend synchronizes the unique existing Owner from these two variables automatically.'
        )


def main() -> int:
    try:
        validate_bootstrap_env()
    except BootstrapConfigError as exc:
        print('\n[Company OS] CONFIGURATION ERROR\n'+str(exc)+'\n', file=sys.stderr, flush=True)
        return 2
    print('[Company OS] Configuration preflight passed. ADMIN_USERNAME, password policy look valid. (Secrets not printed.)', flush=True)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
