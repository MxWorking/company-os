"""Company OS 2.1 regression suite for project isolation, delegated rights, notes, HR vault, and accounting.
These run in the local preview database only. They are not a security penetration test.
"""
import io
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import select
from main import app
from database import SessionLocal
from ops.models import Account,Membership
from ops.models_ext import IdentityDocument
from ops.router_ext import national_id_valid


def new_user(client, role='member'):
    name='qa-'+secrets.token_hex(5)
    password='testing-strong-password-9876'
    resp=client.post('/api/v2/members',json={'username':name,'full_name':'QA Test Staff','role':role,'password':password})
    assert resp.status_code==201,resp.text
    return name,password,resp.json()['id']


def test_role_aware_capabilities_and_delegated_override():
    with TestClient(app) as owner:
        username,password,user_id=new_user(owner,'member')
        with TestClient(app) as employee:
            login=employee.post('/api/v2/auth/login',json={'username':username,'password':password})
            assert login.status_code==200,login.text
            who=employee.get('/api/v2/me').json()
            assert who['permissions']['finance']['read'] is False
            assert employee.get('/api/v2/ledger/accounts').status_code==403
            assert employee.put(f'/api/v2/members/{user_id}/grants',json={'module':'finance','read':True,'write':True}).status_code==403
            assert owner.put(f'/api/v2/members/{user_id}/grants',json={'module':'finance','read':True,'write':True}).status_code==422
            assert employee.get('/api/v2/ledger/accounts').status_code==403
            assert owner.patch(f'/api/v2/members/{user_id}/role?role=accountant').status_code==200
            who=employee.get('/api/v2/me').json()
            assert who['permissions']['finance']=={'read':True,'write':True}
            assert employee.get('/api/v2/ledger/accounts').status_code==200
            assert employee.post('/api/v2/ledger/accounts',json={'code':'QA'+secrets.token_hex(2),'name':'Accountant asset','category':'asset'}).status_code==201
            assert owner.patch(f'/api/v2/members/{user_id}/role?role=member').status_code==200
            assert employee.get('/api/v2/ledger/accounts').status_code==403


def test_project_membership_notes_and_chat_isolation():
    with TestClient(app) as owner:
        p=owner.post('/api/v2/records/project',json={'title':'Restricted Project '+secrets.token_hex(3)}).json()['id']
        other=owner.post('/api/v2/records/project',json={'title':'Other Private Project'}).json()['id']
        username,password,user_id=new_user(owner)
        with TestClient(app) as employee:
            assert employee.post('/api/v2/auth/login',json={'username':username,'password':password}).status_code==200
            before=employee.get('/api/v2/records/project').json()['items']
            assert p not in [r['id'] for r in before]
            assert employee.get(f'/api/v2/projects/{p}/members').status_code==403
            assert employee.post('/api/v2/messages',params={'project_id':p},json={'body':'intrusion','category':'chat'}).status_code==403
            assert owner.post(f'/api/v2/projects/{p}/members',json={'account_id':user_id}).status_code==201
            visible=employee.get('/api/v2/records/project').json()['items']
            assert p in [r['id'] for r in visible]
            assert other not in [r['id'] for r in visible]
            sent=employee.post('/api/v2/messages',params={'project_id':p},json={'body':'Daily work: integrated UI','category':'daily'})
            assert sent.status_code==201,sent.text
            assert employee.post('/api/v2/messages',params={'project_id':p},json={'body':'approved without manager','category':'decision'}).status_code==403
            assert owner.get('/api/v2/messages',params={'project_id':p}).json()[-1]['body']=='Daily work: integrated UI'
            saved=employee.post('/api/v2/private-notes',json={'title':'My private note','body':'Secret personal plan','project_id':p})
            assert saved.status_code==201,saved.text
            note_id=saved.json()['id']
            assert employee.get('/api/v2/private-notes',params={'project_id':p}).json()[0]['title']=='My private note'
            assert owner.put(f'/api/v2/private-notes/{note_id}',json={'title':'hacked','body':'x','project_id':p}).status_code==404
            assert employee.post('/api/v2/projects/%s/events'%p,json={'title':'Delivery','starts_on':'2026-10-22','event_type':'delivery'}).status_code==201
            assert employee.get(f'/api/v2/projects/{p}/events').json()[0]['event_type']=='delivery'
            assert employee.get(f'/api/v2/projects/{other}/events').status_code==403
            assert owner.delete(f'/api/v2/projects/{p}/members/{user_id}').status_code==204
            assert employee.get('/api/v2/messages',params={'project_id':p}).status_code==403
            assert employee.get('/api/v2/private-notes',params={'project_id':p}).status_code==403


def test_support_tickets_are_local_and_private_to_submitter():
    with TestClient(app) as owner:
        username,password,_=new_user(owner)
        with TestClient(app) as employee:
            employee.post('/api/v2/auth/login',json={'username':username,'password':password})
            assert employee.post('/api/v2/support/tickets',json={'audience':'developer','title':'Something is broken','message':'Please repair the widget'}).status_code==201
            assert employee.get('/api/v2/support/tickets').json()[0]['audience']=='developer'
            cfg=employee.get('/api/v2/support/config').json()
            assert cfg['tickets_are_local_only'] is True


def test_double_entry_balancing_post_and_closed_period():
    with TestClient(app) as c:
        nonce=secrets.token_hex(4)
        a=c.post('/api/v2/ledger/accounts',json={'code':'A'+nonce,'name':'Cash asset','category':'asset'}).json()['id']
        r=c.post('/api/v2/ledger/accounts',json={'code':'R'+nonce,'name':'Revenue','category':'revenue'}).json()['id']
        wrong={'entry_date':'2026-10-15','memo':'Mismatch','lines':[{'account_id':a,'debit':1000,'credit':0},{'account_id':r,'debit':0,'credit':900}]}
        assert c.post('/api/v2/ledger/entries',json=wrong).status_code==422
        correct={**wrong,'memo':'Sale voucher','lines':[{'account_id':a,'debit':1000,'credit':0},{'account_id':r,'debit':0,'credit':1000}]}
        posted=c.post('/api/v2/ledger/entries',json=correct)
        assert posted.status_code==201,posted.text
        entry_id=posted.json()['id']
        assert c.post(f'/api/v2/ledger/entries/{entry_id}/post').status_code==200
        assert c.post(f'/api/v2/ledger/entries/{entry_id}/post').status_code==409
        report=c.get('/api/v2/ledger/reports/trial-balance').json()
        assert report['balanced'] is True and report['debits']==report['credits']
        assert c.put('/api/v2/ledger/periods',json={'period':'2026-10','locked':True}).status_code==200
        assert c.post('/api/v2/ledger/entries',json=correct).status_code==409
        assert c.put('/api/v2/ledger/periods',json={'period':'2026-10','locked':False}).status_code==200


def valid_national_id(prefix='123456789'):
    remainder=sum(int(prefix[i])*(10-i) for i in range(9))%11
    return prefix+str(remainder if remainder<2 else 11-remainder)


def test_identity_vault_uses_managed_encryption_and_isolation():
    with TestClient(app) as owner:
        _,_,user_id=new_user(owner)
        national=valid_national_id('008457594')
        assert national_id_valid(national)
        result=owner.put(f'/api/v2/identity/{user_id}',json={'national_id':national,'phone':'09123456789'})
        assert result.status_code==200,result.text
        assert result.json()['phone_verified'] is False
        assert owner.post(f'/api/v2/identity/{user_id}/verify-phone').status_code==501
        bad=owner.put(f'/api/v2/identity/{user_id}',json={'national_id':'0000000000','phone':'09123456789'})
        assert bad.status_code==422
        with SessionLocal() as db:
            from ops.models_ext import IdentityProfile
            profile=db.scalar(select(IdentityProfile).where(IdentityProfile.account_id==user_id))
            assert national.encode() not in profile.national_id_cipher
        response=owner.post(f'/api/v2/identity/{user_id}/documents',params={'kind':'national_card_front'},files={'file':('id.png',b'\x89PNG\r\n\x1a\n'+b'not-a-real-image-for-test','image/png')})
        assert response.status_code==201,response.text
        with SessionLocal() as db:
            doc=db.get(IdentityDocument,response.json()['id'])
            assert b'not-a-real-image-for-test' not in doc.encrypted_bytes
        assert owner.get(f'/api/v2/identity/{user_id}/documents/{response.json()["id"]}').content.startswith(b'\x89PNG')


def test_compact_navigation_and_workspaces_static_contract():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    source=(root/'frontend/components/CompanyOS.tsx').read_text()
    assert 'sidebarGroups' in source and 'side-submenu' in source
    assert "fa:'وظایف',en:'Tasks'" in source
    assert "fa:'وظایف من'" in source
    assert 'allowed(x.key)' in source
    assert 'AccountWorkspace' in source and 'AadinAccountingHub' in source and 'ProjectHub' in source
    assert 'AccountingWorkspace' in (root/'frontend/components/AadinAccountingHub.tsx').read_text()
    module=(root/'frontend/components/CompanyModules.tsx').read_text()
    for name in ('ProjectHub','NotesWorkspace','AccountingWorkspace','SupportWorkspace','AccountWorkspace'):
        assert f'function {name}' in module


def test_project_approvals_and_multiple_team_assignments():
    with TestClient(app) as owner:
        p=owner.post('/api/v2/records/project',json={'title':'Decision Room '+secrets.token_hex(3)}).json()['id']
        team1=owner.post('/api/v2/records/team',json={'title':'Engineering QA Team'}).json()['id']
        team2=owner.post('/api/v2/records/team',json={'title':'Design QA Team'}).json()['id']
        for t in [team1,team2]:
            assert owner.post(f'/api/v2/projects/{p}/teams',json={'team_id':t}).status_code==201
        assert len(owner.get(f'/api/v2/projects/{p}/teams').json())==2
        username,password,user_id=new_user(owner)
        owner.post(f'/api/v2/projects/{p}/members',json={'account_id':user_id})
        with TestClient(app) as employee:
            employee.post('/api/v2/auth/login',json={'username':username,'password':password})
            req=employee.post(f'/api/v2/projects/{p}/approvals',json={'title':'Change layout','description':'Need review'})
            assert req.status_code==201,req.text
            request_id=req.json()['id']
            assert employee.post(f'/api/v2/projects/{p}/approvals/{request_id}/decide',params={'decision':'approved'}).status_code==403
            assert owner.post(f'/api/v2/projects/{p}/approvals/{request_id}/decide',params={'decision':'approved'}).status_code==200
            assert owner.post(f'/api/v2/projects/{p}/approvals/{request_id}/decide',params={'decision':'rejected'}).status_code==409
            assert employee.get(f'/api/v2/projects/{p}/approvals').json()[0]['status']=='approved'
        assert owner.delete(f'/api/v2/projects/{p}/teams/{team2}').status_code==204
        assert len(owner.get(f'/api/v2/projects/{p}/teams').json())==1
