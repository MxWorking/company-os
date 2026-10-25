"""V2.6 reference-data integration must never fabricate posted financial entries."""
from fastapi.testclient import TestClient
import secrets
import test_api
from main import app
from test_membership_finance_23 import owner_login, payload
import ops.router as workspace

ROOT='/api/v2/accounting/preparations'

def test_reference_catalog_records_are_tenant_scoped_and_non_posting(monkeypatch):
    monkeypatch.setattr(workspace, 'DEMO_MODE', False)
    with TestClient(app) as c:
        owner_login(c)
        old_journal=c.get('/api/v2/ledger/entries').json()
        refs=[('party_group',{'description':'retail'}),('item_unit',{'unit':'box','ratio':12}),('expense_group',{}),('currency_setting',{'currency':'IRR','calendar':'jalali'}),('invoice_template_setting',{'description':'bottom label'}),('sales_setting',{'value':'price_level_1'})]
        for kind,details in refs:
            result=c.post(ROOT,json={'kind':kind,'title':'QA '+kind,'details':details})
            assert result.status_code==201,(kind,result.text)
            assert result.json()['status']=='preparation_only'
            listing=c.get(ROOT,params={'kind':kind})
            assert listing.status_code==200 and any(x['id']==result.json()['id'] for x in listing.json()['items'])
        assert c.get('/api/v2/ledger/entries').json()==old_journal
        assert c.post(ROOT,json={'kind':'item_unit','title':'Bad','details':{'ratio':-2}}).status_code==422
        assert c.post(ROOT,json={'kind':'message_template_setting','title':'Unsafe','details':{'password':'secret'}}).status_code==422
        org=c.post('/api/v2/organizations',json={'name':'UI Separation','slug':'ui26-'+secrets.token_hex(5)})
        assert org.status_code==201,org.text
        assert c.post('/api/v2/organizations/switch',params={'org_id':org.json()['id']}).status_code==200
        assert c.get(ROOT).json()['items']==[]

def test_member_cannot_modify_accounting_reference_data(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as owner:
        owner_login(owner)
        u=payload('UI26 Staff')
        assert owner.post('/api/v2/members',json={'username':u['username'],'full_name':u['full_name'],'password':u['password'],'role':'member'}).status_code==201
        with TestClient(app) as staff:
            assert staff.post('/api/v2/auth/login',json={'username':u['username'],'password':u['password']}).status_code==200
            staff.headers.update({'X-Company-CSRF':staff.get('/api/v2/me').json()['csrf']})
            assert staff.get(ROOT,params={'kind':'item_group'}).status_code==403
            assert staff.post(ROOT,json={'kind':'item_group','title':'Unauthorized'}).status_code==403
