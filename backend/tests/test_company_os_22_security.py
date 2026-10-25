"""Access-control and domain regression checks with public demo bypass explicitly DISABLED."""
import io
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import select
from main import app
import main
import ops.router as workspace
from database import SessionLocal
from ops.models import Account, Membership, Organization
from ops.router import make_hash


def test_real_session_gate_personnel_and_support(monkeypatch):
    monkeypatch.setattr(main,'DEMO_MODE',False)
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as client:
        assert client.get('/api/v2/me').status_code==401
        assert client.get('/api/v2/personnel').status_code==401
        assert client.get('/api/v1/dashboard').status_code==401
        assert client.get('/api/v2/support/contacts').status_code==401
        assert client.post('/api/v2/personnel',json={}).status_code==401
        with SessionLocal() as db:
            org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
            name='review-owner-'+secrets.token_hex(4)
            db.add(owner:=Account(username=name,full_name='Owner QA',password_hash=make_hash('review-owner-password-very-strong')))
            db.flush();db.add(Membership(organization_id=org.id,account_id=owner.id,role='owner'));db.commit()
        assert client.post('/api/v2/auth/login',json={'username':name,'password':'incorrect'}).status_code==401
        assert client.post('/api/v2/auth/login',json={'username':name,'password':'review-owner-password-very-strong'}).status_code==200
        me=client.get('/api/v2/me').json();csrf=me['csrf'];client.headers.update({'X-Company-CSRF':csrf})
        assert client.get('/api/v2/personnel').status_code==200
        # No imaginary phone numbers or social links should be prepopulated.
        assert client.get('/api/v2/support/contacts').json()==[]
        invalid=client.post('/api/v2/support/contacts',json={'kind':'telegram','audience':'company','label':'bad','value':'javascript:alert(1)'})
        assert invalid.status_code==422
        link=client.post('/api/v2/support/contacts',json={'kind':'telegram','audience':'company','label':'QA Support','value':'https://t.me/support_example'})
        assert link.status_code==201,link.text
        assert client.get('/api/v2/support/contacts').json()[0]['href']=='https://t.me/support_example'
        member=client.post('/api/v2/members',json={'username':'staff-'+secrets.token_hex(4),'full_name':'QA Staff','password':'staff-review-password-strong','role':'member'})
        assert member.status_code==201,member.text
        staff=member.json()
        profile=client.post('/api/v2/personnel',json={'account_id':staff['id'],'personnel_code':'X-'+secrets.token_hex(4),'job_title':'QA','department':'Testing','employment_type':'full_time','employment_status':'active'})
        assert profile.status_code==201,profile.text
        assert 'national_id' not in str(profile.json())
        assert client.get('/api/v2/personnel').json()[0]['account_id']==staff['id']
        # Manager-only identity vault is independent of ordinary HR records.
        valid_id='0013549583'
        from ops.router_ext import national_id_valid
        if not national_id_valid(valid_id):
            valid_id=next(f'{n:010}' for n in range(100000000,100001000) if national_id_valid(f'{n:010}'))
        res=client.put('/api/v2/identity/'+str(staff['id']),json={'national_id':valid_id,'phone':'09123456789'})
        assert res.status_code==200,res.text
        assert res.json()['phone_verified'] is False
        assert client.post('/api/v2/identity/'+str(staff['id'])+'/verify-phone').status_code==501
        private_info={'first_name':'Test','last_name':'Only','father_name':'Private Father','birth_date':'1990-05-06','certificate_number':'secret-991'}
        saved=client.put(f'/api/v2/identity/{staff["id"]}/details',json=private_info)
        assert saved.status_code==200 and saved.json()['encrypted'] is True
        details=client.get(f'/api/v2/identity/{staff["id"]}/details')
        assert details.status_code==200 and details.json()['data']['father_name']=='Private Father'
        from ops.models_people import IdentityDetails
        with SessionLocal() as db:
            private=db.scalar(select(IdentityDetails).where(IdentityDetails.account_id==staff['id']))
            assert private and b'Private Father' not in private.encrypted_blob
        png=b'\x89PNG\r\n\x1a\n' + b'QA_FAKE_IMAGE_BYTES'
        sent=client.post(f'/api/v2/identity/{staff["id"]}/documents?kind=national_card_front',files={'file':('qa.png',io.BytesIO(png),'image/png')})
        assert sent.status_code==201,sent.text
        docs=client.get('/api/v2/identity/'+str(staff['id'])+'/documents').json()
        assert len(docs)==1
        retrieved=client.get(f'/api/v2/identity/{staff["id"]}/documents/{docs[0]["id"]}')
        assert retrieved.status_code==200 and retrieved.content==png
        assert client.post('/api/v2/auth/logout').status_code==200
        assert client.get('/api/v2/personnel').status_code==401
        assert client.get('/api/v2/identity/'+str(staff['id'])).status_code==401


def test_staff_cannot_view_full_hr_or_modify_support_config(monkeypatch):
    monkeypatch.setattr(main,'DEMO_MODE',False)
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as client:
        with SessionLocal() as db:
            org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
            username='staff-access-'+secrets.token_hex(4)
            db.add(staff:=Account(username=username,full_name='Limited Staff',password_hash=make_hash('limited-review-password-strong')))
            db.flush();db.add(Membership(organization_id=org.id,account_id=staff.id,role='member'));db.commit()
        assert client.post('/api/v2/auth/login',json={'username':username,'password':'limited-review-password-strong'}).status_code==200
        user=client.get('/api/v2/me').json();client.headers.update({'X-Company-CSRF':user['csrf']})
        assert user['permissions']['hr']['read'] is False
        assert user['permissions']['support']['read'] is True
        assert client.get('/api/v2/personnel').status_code==403
        assert client.get('/api/v2/personnel/accounts').status_code==403
        assert client.get('/api/v2/support/contacts').status_code==200
        assert client.post('/api/v2/support/contacts',json={'audience':'developer','kind':'phone','label':'fake','value':'02112345678'}).status_code==403
        assert client.get('/api/v1/dashboard').status_code==403
