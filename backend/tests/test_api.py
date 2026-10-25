"""Integration checks against an ephemeral SQLite database."""
import os
import tempfile
from pathlib import Path

_tmp=tempfile.TemporaryDirectory()
os.environ['DATABASE_URL']='sqlite:///'+str(Path(_tmp.name)/'test.db')
os.environ['APP_ENV']='test'
os.environ['DEMO_MODE']='true'

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


def test_demo_dashboard_and_crud():
    with TestClient(app) as client:
        assert client.get('/health').json()['status']=='ok'
        summary=client.get('/api/v1/dashboard'); assert summary.status_code==200
        assert summary.json()['stats']['projects']==24
        resp=client.post('/api/v1/projects',json={'name':'پروژه تست','manager':'تیم تست','progress':18})
        assert resp.status_code==201, resp.text
        project_id=resp.json()['id']
        assert client.patch(f'/api/v1/projects/{project_id}',json={'progress':75}).json()['progress']==75
        assert client.get('/api/v1/dashboard').json()['stats']['projects']==25
        assert client.delete(f'/api/v1/projects/{project_id}').status_code==204
        task=client.post('/api/v1/tasks',json={'title':'تست API','priority':'بالا'});assert task.status_code==201
        assert client.patch(f'/api/v1/tasks/{task.json()["id"]}',json={'status':'انجام شده'}).status_code==200
        module=client.post('/api/v1/modules/documents',json={'title':'سند آزمایشی'});assert module.status_code==201
        module_id=module.json()['id']
        assert client.patch(f'/api/v1/modules/documents/{module_id}',json={'title':'سند ویرایش‌شده','subtitle':'تست','status':'نهایی'}).status_code==200
        assert client.get('/api/v1/modules/documents').status_code==200
        assert client.delete(f'/api/v1/modules/documents/{module_id}').status_code==204
        approval=client.post('/api/v1/approvals',json={'title':'تأیید آزمایشی'});assert approval.status_code==201
        assert client.patch(f'/api/v1/approvals/{approval.json()["id"]}',json={'status':'تأیید شده'}).status_code==200
        assert client.post('/api/v1/assistant',json={'question':'وضعیت پروژه‌ها چیست؟'}).json()['mode']=='rules-based-demo'


def test_validation_and_missing():
    with TestClient(app) as client:
        assert client.post('/api/v1/projects',json={'name':'','progress':101}).status_code==422
        assert client.patch('/api/v1/projects/999999',json={'name':'x'}).status_code==404
        assert client.get('/api/v1/modules/unknown').status_code==404
        assert client.post('/api/v1/tasks',json={'title':'invalid relation','project_id':999999}).status_code==404


def test_auth_required_when_demo_is_disabled(monkeypatch):
    import main
    monkeypatch.setattr(main, 'DEMO_MODE', False)
    with TestClient(app) as client:
        assert client.get('/api/v1/dashboard').status_code == 401
        assert client.get('/api/v1/projects').status_code == 401
        assert client.get('/api/v1/auth/session').json()['authenticated'] is False


def test_employee_directory_full_crud_and_hierarchy():
    with TestClient(app) as client:
        people=client.get('/api/v1/employees')
        assert people.status_code==200
        payload={'personnel_code':'QA-X-991','first_name':'آزمایش','last_name':'مدیریت','role':'مدیر','department':'آزمایشگاه','employment_type':'تمام‌وقت','employment_status':'فعال','email':'qa@example.org'}
        boss=client.post('/api/v1/employees',json=payload)
        assert boss.status_code==201,boss.text
        bid=boss.json()['id']
        assert boss.json()['role']=='مدیر'
        assert client.post('/api/v1/employees',json=payload).status_code==409
        staff=dict(payload,personnel_code='QA-X-992',first_name='کارمند',role='کارگر',reporting_to_id=bid)
        worker=client.post('/api/v1/employees',json=staff)
        assert worker.status_code==201,worker.text
        wid=worker.json()['id']
        assert worker.json()['reporting_to_id']==bid
        assert client.patch(f'/api/v1/employees/{bid}',json=dict(payload,reporting_to_id=wid)).status_code==422
        assert client.patch(f'/api/v1/employees/{wid}',json=dict(staff,reporting_to_id=wid)).status_code==422
        updated=dict(staff,role='سرپرست',job_title='سرپرست عملیات')
        assert client.patch(f'/api/v1/employees/{wid}',json=updated).json()['job_title']=='سرپرست عملیات'
        assert client.delete(f'/api/v1/employees/{bid}').status_code==204
        roster=client.get('/api/v1/employees').json()
        assert next(x for x in roster if x['id']==wid)['reporting_to_id'] is None
        assert client.delete(f'/api/v1/employees/{wid}').status_code==204
        assert client.post('/api/v1/employees',json={**payload,'role':'unsupported'}).status_code==422


def test_employee_directory_requires_admin_session(monkeypatch):
    import main
    monkeypatch.setattr(main,'DEMO_MODE',False)
    with TestClient(app) as client:
        assert client.get('/api/v1/employees').status_code==401
        assert client.post('/api/v1/employees',json={'personnel_code':'LOCK','first_name':'A','last_name':'B'}).status_code==401
