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


def test_preflight_requires_only_admin_credentials():
    validate_bootstrap_env(BASE)
    for change in ({'ADMIN_USERNAME':''},{'ADMIN_PASSWORD':''}):
        try:
            validate_bootstrap_env({**BASE,**change})
        except BootstrapConfigError as exc:
            assert 'ADMIN_' in str(exc)
        else:
            assert False,'missing admin credential accepted'


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
        # Updating the two environment values synchronizes the ONE existing Owner.
        env['ADMIN_PASSWORD']=fresh
        old_code=script.replace('USER','"localowner"').replace('PASSWORD','"'+old+'"').replace('WRONG','"bad-password"')
        # The env-managed account rejects the previous password after startup.
        renamed={**env,'ADMIN_USERNAME':'newowner','ADMIN_ENV_SYNC':'true'}
        new_code=script.replace('USER','"newowner"').replace('PASSWORD','"'+fresh+'"').replace('WRONG','"'+old+'"')
        _run(['-c',new_code],renamed,backend)
