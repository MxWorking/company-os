"""Regression tests for the Docker .env/password boot problem.

Runs an isolated real (non-demo) FastAPI startup using temporary SQLite.
No real admin secrets or identity data enter the test database.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from ops.bootstrap import validate_bootstrap_env, BootstrapConfigError


BASE={
    'ADMIN_USERNAME': 'localowner',
    'ADMIN_PASSWORD': 'UniquePassword-NotForProduction-2026',
    'SESSION_SECRET': 'dev-test-session-'+('z'*50),
    'HR_ENCRYPTION_KEY': 'cd'*32,
    'APP_ENV': 'development',
    'DEMO_MODE': 'false',
}


def test_preflight_rejects_short_password():
    try:
        validate_bootstrap_env({**BASE, 'ADMIN_PASSWORD': 'admin123'})
    except BootstrapConfigError as exc:
        assert 'ADMIN_PASSWORD' in str(exc) and '12' in str(exc)
    else:
        assert False, 'weak password was accepted'


def test_preflight_rejects_invalid_hr_key_and_missing_session_secret():
    for change,expected in [({'HR_ENCRYPTION_KEY':'bad'},'HR_ENCRYPTION_KEY'),({'SESSION_SECRET':''},'SESSION_SECRET')]:
        try:
            validate_bootstrap_env({**BASE, **change})
        except BootstrapConfigError as exc:
            assert expected in str(exc)
        else:
            assert False, 'invalid env accepted'


def _run(cmd, env, cwd):
    result = subprocess.run([sys.executable,*cmd], cwd=cwd, env=env, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, (result.stdout + '\n' + result.stderr)[-2500:]
    return result.stdout


def test_real_boot_login_password_reset_and_existing_owner_protection():
    backend=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        env={**os.environ,**BASE, 'DATABASE_URL':'sqlite:///'+str(Path(tmp)/'bootstrap.db')}
        old=BASE['ADMIN_PASSWORD']
        fresh='AnotherStrongPassword-ForTesting-2026'
        script='''from fastapi.testclient import TestClient
from main import app
with TestClient(app) as c:
    assert c.get('/health').json()['status']=='ok'
    good=c.post('/api/v2/auth/login',json={'username':USER,'password':PASSWORD})
    assert good.status_code==200, good.text
    assert c.get('/api/v2/me').json()['username']==USER
    assert c.post('/api/v2/auth/login',json={'username':USER,'password':WRONG}).status_code==401
'''
        code=script.replace('USER','"localowner"').replace('PASSWORD','"'+old+'"').replace('WRONG','"bad-password"')
        _run(['-c',code],env,backend)
        # Editing .env must not secretly change an existing account's password.
        env['ADMIN_PASSWORD']=fresh
        _run(['-c',code],env,backend)
        # Editing ADMIN_USERNAME must not silently mint another owner.
        renamed={**env,'ADMIN_USERNAME':'newowner'}
        _run(['-c',code],renamed,backend)
        # Explicit operator action rotates the existing owner's password and username.
        _run(['-m','ops.reset_admin','--apply','--rename-to-configured'],renamed,backend)
        new_code=script.replace('USER','"newowner"').replace('PASSWORD','"'+fresh+'"').replace('WRONG','"'+old+'"')
        _run(['-c',new_code],renamed,backend)
