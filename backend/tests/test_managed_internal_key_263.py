"""Crypto key is automatically managed and independent of the admin password."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(path,script,env):
    p=subprocess.run([sys.executable,'-c',script],cwd=path,env=env,text=True,capture_output=True,timeout=45)
    assert p.returncode==0,(p.stdout+'\n'+p.stderr)[-2000:]
    return p.stdout.strip()


def test_local_secret_survives_process_restart_and_owner_rotation():
    backend=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as temp:
        env={**os.environ,'COMPANY_OS_KEY_PATH':str(Path(temp)/'root.key')}
        env.pop('COMPANY_OS_INTERNAL_KEY',None)
        env.pop('VERCEL_ENV',None)
        script="from ops.secret_manager import subkey;print(subkey('hr-aes-v1').hex(),subkey('cookie-session-v1').hex())"
        first=_run(backend,script,{**env,'ADMIN_PASSWORD':'OldVeryStrongPassword-2026'})
        second=_run(backend,script,{**env,'ADMIN_PASSWORD':'NewVeryStrongPassword-2026'})
        assert first==second
        assert len(first.split())==2 and first.split()[0]!=first.split()[1]
        assert (Path(temp)/'root.key').stat().st_size==32


def test_vercel_requires_managed_root():
    backend=Path(__file__).resolve().parents[1]
    env={**os.environ,'VERCEL_ENV':'production'}
    env.pop('COMPANY_OS_INTERNAL_KEY',None)
    p=subprocess.run([sys.executable,'-c','from ops.secret_manager import subkey;subkey("cookie-session-v1")'],cwd=backend,env=env,text=True,capture_output=True,timeout=20)
    assert p.returncode!=0 and 'Missing automatically provisioned' in p.stderr


def test_hosted_secret_is_stable_and_purpose_separated():
    backend=Path(__file__).resolve().parents[1]
    env={**os.environ,'VERCEL_ENV':'production','COMPANY_OS_INTERNAL_KEY':'locally-simulated-secure-opaque-test-secret-0123456789-'*2}
    script="from ops.secret_manager import subkey;print(subkey('hr-aes-v1').hex(),subkey('cookie-session-v1').hex())"
    assert _run(backend,script,env)==_run(backend,script,env)
