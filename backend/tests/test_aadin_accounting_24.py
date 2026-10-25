"""Aadin-inspired navigation preparation endpoints: data isolation and non-posting safety."""
from fastapi.testclient import TestClient
import pytest
import test_api  # tests use same ephemeral DB and configure APP_ENV before app import
from main import app
from test_membership_finance_23 import owner_login,payload
import ops.router as workspace

PREFIX='/api/v2/accounting/preparations'

@pytest.fixture(autouse=True)
def admin_bootstrap_for_new_test_module(monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME','admin')
    monkeypatch.setenv('ADMIN_PASSWORD','an-example-only-strong-bootstrap-42')
    monkeypatch.setenv('SESSION_SECRET','an-example-only-random-looking-session-value-for-tests')


def test_guest_and_staff_cannot_access_accounting_preparations(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as guest:
        assert guest.get(PREFIX).status_code==401
        assert guest.post(PREFIX,json={'kind':'person','title':'Test Person'}).status_code==401
    with TestClient(app) as admin:
        owner_login(admin)
        user=payload('Staff')
        assert admin.post('/api/v2/members',json={'username':user['username'],'full_name':user['full_name'],'password':user['password'],'role':'member'}).status_code==201
        with TestClient(app) as staff:
            assert staff.post('/api/v2/auth/login',json={'username':user['username'],'password':user['password']}).status_code==200
            staff.headers.update({'X-Company-CSRF':staff.get('/api/v2/me').json()['csrf']})
            assert staff.get(PREFIX).status_code==403
            assert staff.post(PREFIX,json={'kind':'sales_invoice','title':'Could not post'}).status_code==403

def test_draft_crud_is_non_posting_and_validated(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as admin:
        owner_login(admin)
        previous=admin.get('/api/v2/ledger/entries').json()
        invalid=admin.post(PREFIX,json={'kind':'posted_payment','title':'Unsafe'})
        assert invalid.status_code==422
        invalid=admin.post(PREFIX,json={'kind':'sales_invoice','title':'Bad','details':{'secret_password':'never'}})
        assert invalid.status_code==422
        created=admin.post(PREFIX,json={'kind':'sales_invoice','title':'Draft sale','details':{'party':'Test Vendor','amount':12345,'reference':'Q-123'}})
        assert created.status_code==201,created.text
        item=created.json();ident=item['id']
        assert item['status']=='preparation_only'
        assert any(r['id']==ident for r in admin.get(PREFIX,params={'kind':'sales_invoice'}).json()['items'])
        assert admin.get('/api/v2/ledger/entries').json()==previous
        updated=admin.patch(f'{PREFIX}/{ident}',json={'kind':'sales_invoice','title':'Renamed draft','details':{'amount':77}})
        assert updated.status_code==200
        assert updated.json()['title']=='Renamed draft'
        assert admin.patch(f'{PREFIX}/{ident}',json={'kind':'item','title':'Wrong kind'}).status_code==422
        assert admin.delete(f'{PREFIX}/{ident}').status_code==204
        assert admin.patch(f'{PREFIX}/{ident}',json={'kind':'sales_invoice','title':'After archive'}).status_code==404
        assert all(d['id']!=ident for d in admin.get(PREFIX).json()['items'])

def test_accounting_preparations_are_organization_scoped(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as admin:
        owner_login(admin)
        created=admin.post(PREFIX,json={'kind':'item','title':'Org A product'})
        assert created.status_code==201,created.text
        ident=created.json()['id']
        other=admin.post('/api/v2/organizations',json={'name':'Aadin Tenant A','slug':'aadin-tenant-test-'+__import__('secrets').token_hex(4)})
        assert other.status_code==201,other.text
        assert admin.post('/api/v2/organizations/switch',params={'org_id':other.json()['id']}).status_code==200
        assert admin.get(PREFIX).json()['items']==[]
        assert admin.patch(f'{PREFIX}/{ident}',json={'kind':'item','title':'Hijack'}).status_code==404
        assert admin.delete(f'{PREFIX}/{ident}').status_code==404
