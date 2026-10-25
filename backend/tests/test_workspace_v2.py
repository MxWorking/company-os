"""Organization isolation, role permissions, CRUD, notes/checklists and conflicts."""
from fastapi.testclient import TestClient
from sqlalchemy import select
from main import app
from database import SessionLocal
from ops.models import Account,Membership,Record
from ops.router import make_hash


def test_v2_eight_modules_are_data_backed():
    with TestClient(app) as client:
        me=client.get('/api/v2/me')
        assert me.status_code==200,me.text
        assert me.json()['role']=='owner'
        catalog=client.get('/api/v2/catalog').json()
        assert len(catalog['modules'])==8
        for module,kinds in catalog['modules'].items():
            assert kinds,module
            result=client.get('/api/v2/records/'+kinds[0])
            assert result.status_code==200,(module,result.text)
        stats=client.get('/api/v2/analytics/summary')
        assert stats.status_code==200
        assert 'finance' in stats.json()['counts']


def test_v2_task_workflow_notes_checklist_conflicts():
    with TestClient(app) as client:
        r=client.post('/api/v2/records/task',json={'title':'Product acceptance','status':'planned','payload':{'priority':'high','estimate_hours':3.5}})
        assert r.status_code==201,r.text
        task=r.json();id_=task['id']
        assert task['version']==1
        assert client.get('/api/v2/records/task').json()['items'][0]['id']==id_
        assert client.post(f'/api/v2/record/{id_}/notes',json={'body':'Use the project checklist'}).status_code==201
        assert len(client.get(f'/api/v2/record/{id_}/notes').json())==1
        item=client.post(f'/api/v2/record/{id_}/checklist',json={'title':'Review UI'}).json()
        assert client.patch(f'/api/v2/checklist/{item["id"]}?done=true').json()['done'] is True
        update=client.patch(f'/api/v2/record/{id_}',json={'status':'in_progress','version':1})
        assert update.status_code==200,update.text
        assert update.json()['version']==2
        assert client.patch(f'/api/v2/record/{id_}',json={'title':'stale','version':1}).status_code==409
        assert client.delete(f'/api/v2/record/{id_}').status_code==204
        assert client.get(f'/api/v2/record/{id_}').status_code==404


def test_v2_validation_reference_and_dependencies():
    with TestClient(app) as client:
        assert client.post('/api/v2/records/invoice',json={'title':'X','payload':{'amount':-1}}).status_code==422
        assert client.post('/api/v2/records/customer',json={'title':'X','payload':{'surprise':'oops'}}).status_code==422
        assert client.post('/api/v2/records/automation',json={'title':'X','payload':{'enabled':'yes'}}).status_code==422
        assert client.post('/api/v2/records/project',json={'title':'Bad reference','payload':{'owner':'A','budget':4.4}}).status_code==422
        assert client.post('/api/v2/records/task',json={'title':'Orphan','payload':{'project':'99999999'}}).status_code==404
        tasks=[]
        for name in ('A','B','C'):
            tasks.append(client.post('/api/v2/records/task',json={'title':name}).json()['id'])
        for i,j in ((0,1),(1,2)):
            assert client.post(f'/api/v2/record/{tasks[i]}/links',json={'target_id':tasks[j],'relation':'depends_on'}).status_code==201
        assert client.post(f'/api/v2/record/{tasks[2]}/links',json={'target_id':tasks[0],'relation':'depends_on'}).status_code==422


def test_v2_multi_org_isolation_and_member_permissions():
    with TestClient(app) as owner:
        created=owner.post('/api/v2/organizations',json={'name':'QA Second Org','slug':'qa-second-org'})
        assert created.status_code in (201,409),created.text
        orgs=owner.get('/api/v2/me').json()['organizations']
        first=next(x['id'] for x in orgs if x['name']=='Company OS')
        other=next(x['id'] for x in orgs if x['name']=='QA Second Org')
        a=owner.post('/api/v2/records/customer',json={'title':'Private customer A'}).json()['id']
        assert owner.post(f'/api/v2/organizations/switch?org_id={other}').status_code==200
        b=owner.post('/api/v2/records/customer',json={'title':'Private customer B'}).json()['id']
        assert owner.get(f'/api/v2/record/{a}').status_code==404
        assert owner.patch(f'/api/v2/record/{a}',json={'version':1,'title':'steal'}).status_code==404
        assert owner.get(f'/api/v2/record/{b}').status_code==200
        assert owner.post(f'/api/v2/organizations/switch?org_id={first}').status_code==200
        assert owner.get(f'/api/v2/record/{b}').status_code==404
        with SessionLocal() as db:
            from ops.models import Organization
            org=db.get(Organization,first)
            member=db.scalar(select(Account).where(Account.username=='qa-viewer-v2'))
            if member is None:
                member=Account(username='qa-viewer-v2',full_name='QA Viewer',password_hash=make_hash('correct-horse-battery-staple'))
                db.add(member);db.flush()
                db.add(Membership(organization_id=org.id,account_id=member.id,role='viewer'));db.commit()
        with TestClient(app) as viewer:
            login=viewer.post('/api/v2/auth/login',json={'username':'qa-viewer-v2','password':'correct-horse-battery-staple'})
            assert login.status_code==200,login.text
            assert viewer.get('/api/v2/records/task').status_code==200
            assert viewer.post('/api/v2/records/task',json={'title':'No'}).status_code==403
            assert viewer.get('/api/v2/records/invoice').status_code==403
            assert viewer.get('/api/v2/record/'+str(b)).status_code==404
            assert viewer.get('/api/v2/audit').status_code==403
            assert viewer.get('/api/v1/dashboard').status_code==403
            assert viewer.post('/api/v1/tasks',json={'title':'legacy bypass'}).status_code==403


def test_v2_csrf_rejection_in_non_demo_mode(monkeypatch):
    import ops.router as r
    with TestClient(app) as client:
        with SessionLocal() as db:
            from ops.models import Organization
            org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
            account=db.scalar(select(Account).where(Account.username=='qa-viewer-v2'))
            if account is None:
                account=Account(username='qa-viewer-v2',full_name='QA Viewer',password_hash=make_hash('correct-horse-battery-staple'))
                db.add(account);db.flush()
                db.add(Membership(organization_id=org.id,account_id=account.id,role='viewer'))
                db.commit()
        assert client.post('/api/v2/auth/login',json={'username':'qa-viewer-v2','password':'correct-horse-battery-staple'}).status_code==200
        data=client.get('/api/v2/me').json()
        assert data['csrf']
        monkeypatch.setattr(r,'DEMO_MODE',False)
        assert client.post('/api/v2/records/task',json={'title':'bad'}).status_code==403
        # viewer is still forbidden even with CSRF, as it should be.
        assert client.post('/api/v2/records/task',json={'title':'still bad'},headers={'X-Company-CSRF':data['csrf']}).status_code==403


def test_v2_reference_kind_integrity_and_soft_delete():
    with TestClient(app) as client:
        customer=client.post('/api/v2/records/customer',json={'title':'MVP Client'}).json()
        task=client.post('/api/v2/records/task',json={'title':'Not a customer'}).json()
        invalid=client.post('/api/v2/records/opportunity',json={'title':'Mismatch','payload':{'customer':str(task['id'])}})
        assert invalid.status_code==422,invalid.text
        valid=client.post('/api/v2/records/opportunity',json={'title':'New sale','payload':{'customer':str(customer['id']),'value':1000000}})
        assert valid.status_code==201,valid.text
        client.delete('/api/v2/record/'+str(customer['id']))
        assert client.get('/api/v2/record/'+str(customer['id'])).status_code==404
        audit=client.get('/api/v2/audit')
        assert audit.status_code==200
        assert any(e['action']=='record.archive' for e in audit.json())


def test_v2_my_work_and_member_cannot_edit_other_task():
    with TestClient(app) as client:
        member=client.post('/api/v2/members',json={'username':'worker-qa-v2','full_name':'Worker QA','password':'secure-worker-password-123','role':'member'})
        assert member.status_code in (201,409),member.text
        from sqlalchemy import select
        with SessionLocal() as db:
            worker=db.scalar(select(Account).where(Account.username=='worker-qa-v2'))
            worker_id=worker.id
        assigned=client.post('/api/v2/records/task',json={'title':'Assigned task','payload':{'assignee_id':worker_id}})
        assert assigned.status_code==201,assigned.text
        other=client.post('/api/v2/records/task',json={'title':'Private to owner'}).json()
        with TestClient(app) as worker_client:
            assert worker_client.post('/api/v2/auth/login',json={'username':'worker-qa-v2','password':'secure-worker-password-123'}).status_code==200
            tasks=worker_client.get('/api/v2/my-work').json()['items']
            assert assigned.json()['id'] in [x['id'] for x in tasks]
            assert other['id'] not in [x['id'] for x in tasks]
            assert worker_client.patch(f'/api/v2/record/{other["id"]}',json={'version':other['version'],'status':'done'}).status_code==403
            assert worker_client.patch(f'/api/v2/record/{assigned.json()["id"]}',json={'version':1,'status':'in_progress'}).status_code==200
