"""2.3: pending registration, review, accountant-only finance and private request threads."""
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import select
from main import app
from database import SessionLocal
from ops.models import Account,Organization,Membership
from ops.router import make_hash
import ops.router as workspace
from ops.models_registration import JoinApplication


def payload(title='مهندس نرم افزار',org='company-os'):
    suffix=secrets.token_hex(5)
    return {'username':'join-'+suffix,'full_name':'New Hire '+suffix,'password':'StrongDemoSecret123!'+suffix,
            'organization_slug':org,'requested_job_title':title,'department':'Engineering'}


def owner_login(client):
    name='qa-owner-join-'+secrets.token_hex(5)
    password='owner-test-password-strong'
    with SessionLocal() as db:
        org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
        acc=Account(username=name,full_name='QA Owner',password_hash=make_hash(password))
        db.add(acc);db.flush();db.add(Membership(organization_id=org.id,account_id=acc.id,role='owner'));db.commit()
    assert client.post('/api/v2/auth/login',json={'username':name,'password':password}).status_code==200
    client.headers.update({'X-Company-CSRF':client.get('/api/v2/me').json()['csrf']})


def test_registration_pending_manager_approval_and_job_title(monkeypatch):
    with TestClient(app) as admin:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(admin)
        candidate=payload('Chief Executive Officer')
        with TestClient(app) as guest:
            assert guest.get('/api/v2/membership-applications').status_code==401
            assert guest.get('/api/v2/me').status_code==401
            assert guest.post('/api/v2/auth/register',json={**candidate,'password':'short'}).status_code==422
            result=guest.post('/api/v2/auth/register',json=candidate)
            assert result.status_code==201,result.text
            assert result.json()['status']=='pending'
            assert guest.post('/api/v2/auth/register',json=candidate).status_code==409
            attempt=guest.post('/api/v2/auth/login',json={'username':candidate['username'],'password':candidate['password']})
            assert attempt.status_code==403
            assert guest.get('/api/v2/me').status_code==401
            assert guest.post('/api/v2/auth/application-status',json={'username':candidate['username'],'password':candidate['password']}).json()['status']=='pending'
            assert guest.post('/api/v2/auth/application-status',json={'username':candidate['username'],'password':'wrong'}).status_code==401
            pending=admin.get('/api/v2/membership-applications').json()
            row=next(r for r in pending if r['username']==candidate['username'])
            assert row['requested_job_title']=='Chief Executive Officer'
            assert not row['assigned_role']
            assert admin.post(f"/api/v2/membership-applications/{row['id']}/review",json={'decision':'approved','approved_job_title':''}).status_code==422
            approved=admin.post(f"/api/v2/membership-applications/{row['id']}/review",json={
                'decision':'approved','approved_job_title':'Software Engineer','assigned_role':'member'})
            assert approved.status_code==200,approved.text
            assert approved.json()['approved_job_title']=='Software Engineer'
            assert admin.post(f"/api/v2/membership-applications/{row['id']}/review",json={
                'decision':'approved','approved_job_title':'CEO','assigned_role':'admin'}).status_code==409
            assert guest.post('/api/v2/auth/login',json={'username':candidate['username'],'password':candidate['password']}).status_code==200
            me=guest.get('/api/v2/me').json()
            guest.headers.update({'X-Company-CSRF':me['csrf']})
            assert me['role']=='member' and me['job_title']=='Software Engineer'
            assert me['permissions']['finance']['read'] is False
            assert guest.get('/api/v2/ledger/accounts').status_code==403
            assert guest.get('/api/v2/membership-applications').status_code==403


def test_rejection_never_creates_membership(monkeypatch):
    with TestClient(app) as admin:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(admin)
        with TestClient(app) as guest:
            candidate=payload('CFO')
            assert guest.post('/api/v2/auth/register',json=candidate).status_code==201
            row=next(r for r in admin.get('/api/v2/membership-applications').json() if r['username']==candidate['username'])
            reject=admin.post(f"/api/v2/membership-applications/{row['id']}/review",json={'decision':'rejected','reason':'Role does not match personnel record'})
            assert reject.status_code==200
            assert guest.post('/api/v2/auth/login',json={'username':candidate['username'],'password':candidate['password']}).status_code==403
            assert guest.post('/api/v2/auth/application-status',json={'username':candidate['username'],'password':candidate['password']}).json()['status']=='rejected'
            assert candidate['username'] not in [m['username'] for m in admin.get('/api/v2/members').json()]
            with SessionLocal() as db:
                acc=db.scalar(select(Account).where(Account.username==candidate['username']))
                assert not acc.active

def test_finance_request_access_message_replies_and_accountant_role(monkeypatch):
    with TestClient(app) as admin:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(admin)
        staff=[]
        for _ in range(2):
            p=payload('Worker')
            assert admin.post('/api/v2/members',json={'username':p['username'],'full_name':p['full_name'],'password':p['password'],'role':'member'}).status_code==201
            staff.append(p)
        with TestClient(app) as alice, TestClient(app) as bob:
            assert alice.post('/api/v2/auth/login',json={'username':staff[0]['username'],'password':staff[0]['password']}).status_code==200
            alice.headers.update({'X-Company-CSRF':alice.get('/api/v2/me').json()['csrf']})
            assert bob.post('/api/v2/auth/login',json={'username':staff[1]['username'],'password':staff[1]['password']}).status_code==200
            bob.headers.update({'X-Company-CSRF':bob.get('/api/v2/me').json()['csrf']})
            a=alice.post('/api/v2/finance-requests',json={'subject':'Invoice payment request','description':'Pay service invoice for design work'})
            assert a.status_code==201,a.text
            aid=a.json()['id']
            assert len(alice.get('/api/v2/finance-requests').json())==1
            assert bob.get('/api/v2/finance-requests').json()==[]
            assert bob.get(f'/api/v2/finance-requests/{aid}/messages').status_code==404
            assert bob.post(f'/api/v2/finance-requests/{aid}/messages',json={'body':'Intrusion'}).status_code==404
            assert bob.patch(f'/api/v2/finance-requests/{aid}/status',json={'status':'closed'}).status_code==403
            assert alice.patch(f'/api/v2/finance-requests/{aid}/status',json={'status':'closed'}).status_code==403
            assert alice.post(f'/api/v2/finance-requests/{aid}/messages',json={'body':'Can you provide payment date?'}).status_code==201
            aliceid=alice.get('/api/v2/me').json()['id']
            assert admin.patch(f'/api/v2/members/{aliceid}/role?role=accountant').status_code==200
            assert alice.get('/api/v2/me').json()['permissions']['finance']['write'] is True
            assert alice.get('/api/v2/ledger/accounts').status_code==200
            assert alice.patch(f'/api/v2/finance-requests/{aid}/status',json={'status':'answered'}).status_code==200
            assert alice.post(f'/api/v2/finance-requests/{aid}/messages',json={'body':'Payment approved; awaiting invoice'}).status_code==201
            assert len(alice.get(f'/api/v2/finance-requests/{aid}/messages').json())==2
            assert len(admin.get('/api/v2/finance-requests').json())>=1
            assert bob.get('/api/v2/ledger/accounts').status_code==403


def test_registration_cross_tenant_review_blocked(monkeypatch):
    with TestClient(app) as admin:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(admin)
        other_org=admin.post('/api/v2/organizations',json={'name':'Other join tenant '+secrets.token_hex(2),'slug':'join-org-'+secrets.token_hex(4)})
        assert other_org.status_code==201
        org_id=other_org.json()['id']
        with TestClient(app) as guest:
            cand=payload()
            assert guest.post('/api/v2/auth/register',json=cand).status_code==201
            row=next(r for r in admin.get('/api/v2/membership-applications').json() if r['username']==cand['username'])
            assert admin.post(f'/api/v2/organizations/switch?org_id={org_id}').status_code==200
            assert admin.get('/api/v2/membership-applications').json()==[]
            assert admin.post(f"/api/v2/membership-applications/{row['id']}/review",json={'decision':'approved','approved_job_title':'Worker'}).status_code==404


def test_manager_can_review_staff_but_cannot_elevate_to_admin(monkeypatch):
    with TestClient(app) as owner:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(owner)
        manager=payload('Manager')
        created=owner.post('/api/v2/members',json={'username':manager['username'],'full_name':manager['full_name'],'password':manager['password'],'role':'manager'})
        assert created.status_code==201
        with TestClient(app) as applicant:
            candidate=payload('Office Engineer')
            assert applicant.post('/api/v2/auth/register',json=candidate).status_code==201
        with TestClient(app) as mgr:
            assert mgr.post('/api/v2/auth/login',json={'username':manager['username'],'password':manager['password']}).status_code==200
            role=mgr.get('/api/v2/me').json()
            mgr.headers.update({'X-Company-CSRF':role['csrf']})
            assert role['role']=='manager' and role['permissions']['finance']['write'] is True
            requests=mgr.get('/api/v2/membership-applications').json()
            row=next(r for r in requests if r['username']==candidate['username'])
            elevate=mgr.post(f"/api/v2/membership-applications/{row['id']}/review",json={
               'decision':'approved','approved_job_title':'Office Engineer','assigned_role':'admin'})
            assert elevate.status_code==403
            approved=mgr.post(f"/api/v2/membership-applications/{row['id']}/review",json={
               'decision':'approved','approved_job_title':'Engineer','assigned_role':'member'})
            assert approved.status_code==200


def test_rejected_member_can_update_title_and_reapply(monkeypatch):
    with TestClient(app) as owner:
        monkeypatch.setattr(workspace,'DEMO_MODE',False)
        owner_login(owner)
        with TestClient(app) as guest:
            cand=payload('Chief Accountant')
            assert guest.post('/api/v2/auth/register',json=cand).status_code==201
            row=next(r for r in owner.get('/api/v2/membership-applications').json() if r['username']==cand['username'])
            assert owner.post(f"/api/v2/membership-applications/{row['id']}/review",json={'decision':'rejected'}).status_code==200
            assert guest.post('/api/v2/auth/reapply',json={'username':cand['username'],'password':'bad','requested_job_title':'Clerk'}).status_code==401
            updated=guest.post('/api/v2/auth/reapply',json={'username':cand['username'],'password':cand['password'],'requested_job_title':'Clerk','department':'Office'})
            assert updated.status_code==200 and updated.json()['status']=='pending'
            assert guest.post('/api/v2/auth/login',json={'username':cand['username'],'password':cand['password']}).status_code==403
            assert next(r for r in owner.get('/api/v2/membership-applications').json() if r['username']==cand['username'])['requested_job_title']=='Clerk'
