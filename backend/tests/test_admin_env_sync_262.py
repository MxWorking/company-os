"""Opt-in Vercel Owner ENV sync: real login, rotation, preservation, collisions."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from test_bootstrap_221 import BASE, _run


def test_env_sync_rotates_owner_and_preserves_other_accounts():
    backend=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        original={**os.environ,**BASE,'ADMIN_ENV_SYNC':'true','DATABASE_URL':'sqlite:///'+str(Path(tmp)/'db.sqlite')}
        _run(['-c', '''from main import app
from fastapi.testclient import TestClient
from database import SessionLocal
from ops.models import Account
from ops.router import make_hash
with TestClient(app) as c:
 assert c.post('/api/v2/auth/login',json={'username':'localowner','password':'UniquePassword-NotForProduction-2026'}).status_code==200
 with SessionLocal() as db:
  db.add(Account(username='untouched_staff',full_name='Employee',password_hash=make_hash('SafeMemberPassword-2026')));db.commit()
'''],original,backend)
        updated={**original,'ADMIN_USERNAME':'newowner','ADMIN_PASSWORD':'NewStrongOwnerPassword-2026'}
        _run(['-c', '''from main import app
from fastapi.testclient import TestClient
from sqlalchemy import select
from database import SessionLocal
from ops.models import Account,Membership
with TestClient(app) as c:
 assert c.post('/api/v2/auth/login',json={'username':'localowner','password':'UniquePassword-NotForProduction-2026'}).status_code==401
 assert c.post('/api/v2/auth/login',json={'username':'newowner','password':'UniquePassword-NotForProduction-2026'}).status_code==401
 assert c.post('/api/v2/auth/login',json={'username':'newowner','password':'NewStrongOwnerPassword-2026'}).status_code==200
 assert c.get('/api/v2/me').json()['role']=='owner'
 with SessionLocal() as db:
  assert db.scalar(select(Account.id).where(Account.username=='untouched_staff'))
  assert len(db.scalars(select(Membership).where(Membership.role=='owner')).all())==1
'''],updated,backend)
        _run(['-c', '''from main import app
from fastapi.testclient import TestClient
with TestClient(app) as c:
 assert c.post('/api/v2/auth/login',json={'username':'newowner','password':'NewStrongOwnerPassword-2026'}).status_code==200
'''],updated,backend)


def test_env_sync_rejects_username_collision_and_preserves_owner():
    backend=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        env={**os.environ,**BASE,'ADMIN_ENV_SYNC':'true','DATABASE_URL':'sqlite:///'+str(Path(tmp)/'collision.db')}
        _run(['-c', '''from main import app
from fastapi.testclient import TestClient
from database import SessionLocal
from ops.models import Account
from ops.router import make_hash
with TestClient(app):
 with SessionLocal() as db:
  db.add(Account(username='taken',full_name='Member',password_hash=make_hash('SafeMemberPassword-2026')));db.commit()
'''],env,backend)
        collision={**env,'ADMIN_USERNAME':'taken','ADMIN_PASSWORD':'NewStrongOwnerPassword-2026'}
        result=subprocess.run([sys.executable,'-c','from main import app; from fastapi.testclient import TestClient\nwith TestClient(app): pass'],cwd=backend,env=collision,capture_output=True,text=True,timeout=45)
        assert result.returncode!=0 and 'owner sync refused' in result.stderr+result.stdout
        _run(['-c', '''from main import app
from fastapi.testclient import TestClient
with TestClient(app) as c:
 assert c.post('/api/v2/auth/login',json={'username':'localowner','password':'UniquePassword-NotForProduction-2026'}).status_code==200
'''],env,backend)
