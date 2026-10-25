"""Business-ledger/stock/security regression tests. All inputs are non-sensitive fake fixtures."""
import secrets
from fastapi.testclient import TestClient
import test_api
from main import app
from test_membership_finance_23 import owner_login,payload
import ops.router as workspace

def fake(client):
    code=secrets.token_hex(5)
    p=client.post('/api/v2/accounting/operations/parties',json={'name':'QA Supplier / Customer '+code,'role':'both'})
    assert p.status_code==201,p.text
    i=client.post('/api/v2/accounting/operations/items',json={'name':'QA Item '+code,'sku':'QA-'+code,'purchase_price':700,'sale_price':1000})
    assert i.status_code==201,i.text
    return p.json()['id'],i.json()['id']

def invoice(client,kind,person,product,quantity,price,request_key=None):
    return client.post('/api/v2/accounting/operations/documents',json={'kind':kind,'party_id':person,'entry_date':'2026-05-01','request_key':request_key or secrets.token_hex(20),'lines':[{'item_id':product,'quantity':quantity,'price':price}]})

def test_workflow_posting_stock_journal_settlement_and_duplicate(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        owner_login(c)
        person,product=fake(c)
        purchase=invoice(c,'purchase',person,product,5,700)
        assert purchase.status_code==201,purchase.text
        pid=purchase.json()['id']
        assert purchase.json()['status']=='draft'
        assert next(i for i in c.get('/api/v2/accounting/operations/items').json() if i['id']==product)['on_hand']==0
        posted=c.post(f'/api/v2/accounting/operations/documents/{pid}/post')
        assert posted.status_code==200,posted.text
        assert posted.json()['status']=='posted'
        assert c.post(f'/api/v2/accounting/operations/documents/{pid}/post').json()['ledger_entry_id']==posted.json()['ledger_entry_id']
        assert next(i for i in c.get('/api/v2/accounting/operations/items').json() if i['id']==product)['on_hand']==5
        same_key='idempotent-'+secrets.token_hex(14)
        sale=invoice(c,'sale',person,product,2,1000,same_key)
        assert sale.status_code==201,sale.text
        same=invoice(c,'sale',person,product,2,1000,same_key)
        assert same.json()['id']==sale.json()['id']
        assert invoice(c,'sale',person,product,3,1000,same_key).status_code==409
        sale_id=sale.json()['id']
        assert c.post(f'/api/v2/accounting/operations/documents/{sale_id}/post').status_code==200
        remaining=next(i for i in c.get('/api/v2/accounting/operations/items').json() if i['id']==product)
        assert remaining['on_hand']==3 and remaining['avg_cost']==700
        summary=c.get('/api/v2/accounting/operations/summary').json()
        assert summary['sales']>=2000 and summary['purchases']>=3500
        journal=c.get('/api/v2/ledger/reports/trial-balance').json()
        assert journal['balanced'] and journal['debits']==journal['credits']
        cash=c.post('/api/v2/ledger/accounts',json={'code':'10'+secrets.token_hex(6),'name':'Test petty cash','category':'asset'})
        assert cash.status_code==201,cash.text
        paybody={'document_id':sale_id,'cash_account_id':cash.json()['id'],'amount':1000,'entry_date':'2026-05-02','request_key':'payment-'+secrets.token_hex(16)}
        first=c.post('/api/v2/accounting/operations/payments',json=paybody)
        assert first.status_code==201,first.text
        second=c.post('/api/v2/accounting/operations/payments',json=paybody)
        assert second.status_code==201 and second.json()['id']==first.json()['id']
        assert c.post('/api/v2/accounting/operations/payments',json={**paybody,'amount':999}).status_code==409
        record=next(d for d in c.get('/api/v2/accounting/operations/documents').json() if d['id']==sale_id)
        assert record['paid']==1000 and record['remaining']==1000
        too_much=c.post('/api/v2/accounting/operations/payments',json={**paybody,'amount':2000,'request_key':'other-'+secrets.token_hex(16)})
        assert too_much.status_code==422

def test_not_enough_stock_cannot_post_and_draft_cannot_be_paid(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        owner_login(c)
        p,i=fake(c)
        sale=invoice(c,'sale',p,i,3,1000)
        assert sale.status_code==201
        before=len(c.get('/api/v2/ledger/entries').json())
        assert c.post(f'/api/v2/accounting/operations/documents/{sale.json()["id"]}/post').status_code==409
        assert len(c.get('/api/v2/ledger/entries').json())==before
        assert next(row for row in c.get('/api/v2/accounting/operations/items').json() if row['id']==i)['on_hand']==0
        invalid=invoice(c,'purchase',p,i,1,700)
        assert invalid.status_code==201
        assert c.post('/api/v2/accounting/operations/payments',json={'document_id':invalid.json()['id'],'cash_account_id':1,'amount':100,'entry_date':'2026-05-01'}).status_code==409

def test_guest_staff_and_other_organization_isolation(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        assert c.get('/api/v2/accounting/operations/parties').status_code==401
        owner_login(c)
        p,i=fake(c)
        ident=invoice(c,'purchase',p,i,1,500).json()['id']
        user=payload('Ops-finance-staff')
        assert c.post('/api/v2/members',json={**user,'role':'member'}).status_code==201
        with TestClient(app) as staff:
            assert staff.post('/api/v2/auth/login',json={'username':user['username'],'password':user['password']}).status_code==200
            staff.headers.update({'X-Company-CSRF':staff.get('/api/v2/me').json()['csrf']})
            assert staff.get('/api/v2/accounting/operations/documents').status_code==403
            assert staff.post('/api/v2/accounting/operations/documents',json={'kind':'sale','party_id':p,'entry_date':'2026-05-01','lines':[{'item_id':i,'quantity':1,'price':900}]}).status_code==403
        org=c.post('/api/v2/organizations',json={'name':'Accounting Private QA','slug':'finance-test-'+secrets.token_hex(5)})
        assert org.status_code==201
        assert c.post('/api/v2/organizations/switch',params={'org_id':org.json()['id']}).status_code==200
        assert c.get('/api/v2/accounting/operations/parties').json()==[]
        assert c.get('/api/v2/accounting/operations/documents').json()==[]
        assert c.post(f'/api/v2/accounting/operations/documents/{ident}/post').status_code==404
        assert invoice(c,'sale',p,i,1,900).status_code==422

def test_expenses_are_posted_once_and_cheques_are_tracking_only(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        owner_login(c);p,i=fake(c)
        cash=c.post('/api/v2/ledger/accounts',json={'code':'10'+secrets.token_hex(5),'name':'QA Expense Cash','category':'asset'})
        assert cash.status_code==201,cash.text
        starting=len(c.get('/api/v2/ledger/entries').json())
        expense={'title':'QA Test Expense','category':'test','amount':15000,'cash_account_id':cash.json()['id'],'entry_date':'2026-05-10','request_key':'cost-'+secrets.token_hex(20)}
        e=c.post('/api/v2/accounting/operations/expenses',json=expense)
        assert e.status_code==201,e.text
        assert c.post('/api/v2/accounting/operations/expenses',json=expense).json()['id']==e.json()['id']
        assert c.post('/api/v2/accounting/operations/expenses',json={**expense,'amount':17000}).status_code==409
        assert len(c.get('/api/v2/ledger/entries').json())==starting+1
        assert c.get('/api/v2/accounting/operations/summary').json()['expenses']>=15000
        cheque={'number':'CHK-'+secrets.token_hex(5),'direction':'received','party_id':p,'amount':99000,'due_date':'2026-06-30'}
        ch=c.post('/api/v2/accounting/operations/cheques',json=cheque)
        assert ch.status_code==201 and ch.json()['posting']=='tracking_only'
        assert c.post('/api/v2/accounting/operations/cheques',json=cheque).status_code==409
        assert len(c.get('/api/v2/ledger/entries').json())==starting+1
        assert any(row['id']==ch.json()['id'] for row in c.get('/api/v2/accounting/operations/cheques').json())
        assert c.get('/api/v2/ledger/reports/trial-balance').json()['balanced']

def test_expenses_cheques_are_protected_and_tenant_scoped(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        assert c.get('/api/v2/accounting/operations/cheques').status_code==401
        assert c.get('/api/v2/accounting/operations/expenses').status_code==401
        owner_login(c)
        user=payload('QAFinance25')
        created=c.post('/api/v2/members',json={**user,'role':'member'})
        assert created.status_code==201
        with TestClient(app) as staff:
            assert staff.post('/api/v2/auth/login',json={'username':user['username'],'password':user['password']}).status_code==200
            staff.headers.update({'X-Company-CSRF':staff.get('/api/v2/me').json()['csrf']})
            assert staff.get('/api/v2/accounting/operations/cheques').status_code==403
            assert staff.get('/api/v2/accounting/operations/expenses').status_code==403
            assert staff.post('/api/v2/accounting/operations/expenses',json={'title':'bad','amount':1,'cash_account_id':1,'entry_date':'2026-05-10'}).status_code==403

def test_inventory_value_is_conserved_with_integer_rial_rounding_and_cash_report(monkeypatch):
    monkeypatch.setattr(workspace,'DEMO_MODE',False)
    with TestClient(app) as c:
        owner_login(c)
        p,i=fake(c)
        purchase=invoice(c,'purchase',p,i,3,1)
        assert purchase.status_code==201
        assert c.post(f'/api/v2/accounting/operations/documents/{purchase.json()["id"]}/post').status_code==200
        sale=invoice(c,'sale',p,i,1,4)
        assert c.post(f'/api/v2/accounting/operations/documents/{sale.json()["id"]}/post').status_code==200
        remaining=next(x for x in c.get('/api/v2/accounting/operations/items').json() if x['id']==i)
        assert remaining['on_hand']==2 and remaining['stock_value']==2
        cash=c.post('/api/v2/ledger/accounts',json={'code':'10'+secrets.token_hex(6),'name':'Cash QA Cashflow','category':'asset'})
        assert cash.status_code==201
        payment=c.post('/api/v2/accounting/operations/payments',json={'document_id':sale.json()['id'],'cash_account_id':cash.json()['id'],'amount':4,'entry_date':'2026-05-03'})
        assert payment.status_code==201,payment.text
        moves=c.get('/api/v2/accounting/operations/cash-movements').json()
        assert any(x['account_id']==cash.json()['id'] and x['debit']==4 for x in moves)
        assert c.get('/api/v2/ledger/reports/trial-balance').json()['balanced']
