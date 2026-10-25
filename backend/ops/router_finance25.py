"""Accountable MVP for party -> goods -> sale/purchase -> posting -> settlement.
No cheque clearing, statutory tax compliance or migration from old drafts. All integer IRR.
"""
from datetime import date
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .router import ActorDep, DB, check, log
from .models_ext import FiscalPeriod, LedgerAccount, JournalEntry, JournalLine
from .models_finance25 import FinanceParty,FinanceItem,FinanceDocument,FinanceDocumentLine,FinanceStockMovement,FinancePayment,FinanceExpense,FinanceCheque

router=APIRouter(prefix='/api/v2/accounting/operations', tags=['Accounting Operations 2.5'])
LIMIT=10**12

class PartyIn(BaseModel):
    name:str=Field(min_length=2,max_length=180)
    role:Literal['customer','supplier','both']='both'
    phone:str=Field(default='',max_length=40)
    description:str=Field(default='',max_length=500)

class ItemIn(BaseModel):
    sku:str=Field(min_length=1,max_length=64)
    name:str=Field(min_length=2,max_length=180)
    kind:Literal['product','service']='product'
    unit:str=Field(default='عدد',min_length=1,max_length=32)
    sale_price:int=Field(ge=0,le=LIMIT,default=0)
    purchase_price:int=Field(ge=0,le=LIMIT,default=0)
    min_stock:int=Field(ge=0,le=10**8,default=0)

class LineIn(BaseModel):
    item_id:int=Field(gt=0)
    quantity:int=Field(gt=0,le=10**7)
    price:int=Field(ge=0,le=10**10)
    discount:int=Field(ge=0,le=LIMIT,default=0)

class DocumentIn(BaseModel):
    kind:Literal['sale','purchase']
    party_id:int=Field(gt=0)
    entry_date:date
    memo:str=Field(default='',max_length=350)
    request_key:str=Field(default_factory=lambda:uuid4().hex,min_length=12,max_length=80)
    lines:list[LineIn]=Field(min_length=1,max_length=80)

class PaymentIn(BaseModel):
    document_id:int=Field(gt=0)
    cash_account_id:int=Field(gt=0)
    amount:int=Field(gt=0,le=LIMIT)
    entry_date:date
    request_key:str=Field(default_factory=lambda:uuid4().hex,min_length=12,max_length=80)

def guard_period(db,org_id:int,when:str):
    locked=db.scalar(select(FiscalPeriod.locked).where(FiscalPeriod.organization_id==org_id,FiscalPeriod.period==when[:7]))
    if locked:raise HTTPException(409,'Accounting period is locked.')

def party(db,org_id,ident):
    p=db.scalar(select(FinanceParty).where(FinanceParty.organization_id==org_id,FinanceParty.id==ident,FinanceParty.active.is_(True)))
    if not p:raise HTTPException(422,'Party not found in current organization.')
    return p

def item(db,org_id,ident,lock=False):
    q=select(FinanceItem).where(FinanceItem.organization_id==org_id,FinanceItem.id==ident,FinanceItem.active.is_(True))
    if lock:q=q.with_for_update()
    i=db.scalar(q)
    if not i:raise HTTPException(422,'Item not found in current organization.')
    return i

def account(db,org,code,name,category):
    acc=db.scalar(select(LedgerAccount).where(LedgerAccount.organization_id==org,LedgerAccount.code==code))
    if acc:
        if not acc.active or acc.category!=category:raise HTTPException(409,f'Configured account {code} incompatible with financial posting.')
        return acc
    acc=LedgerAccount(organization_id=org,code=code,name=name,category=category)
    db.add(acc);db.flush();return acc

def journal(db,actor,when,memo,lines):
    # Keep all journal lines + origin doc in the SAME database transaction.
    values=[(a,dr,cr) for a,dr,cr in lines if dr or cr]
    if not values or sum(dr for _,dr,_ in values)!=sum(cr for _,_,cr in values):
        raise HTTPException(422,'Unbalanced financial entry.')
    entry=JournalEntry(organization_id=actor.org.id,entry_date=when,memo=memo,posted=True,created_by=actor.user.id)
    db.add(entry);db.flush()
    for a,dr,cr in values:db.add(JournalLine(organization_id=actor.org.id,entry_id=entry.id,account_id=a.id,debit=dr,credit=cr))
    return entry

def detail(db,document):
    rows=db.scalars(select(FinanceDocumentLine).where(FinanceDocumentLine.document_id==document.id,FinanceDocumentLine.organization_id==document.organization_id).order_by(FinanceDocumentLine.id)).all()
    return {'id':document.id,'request_key':document.request_key,'kind':document.kind,'status':document.status,'party_id':document.party_id,'entry_date':document.entry_date,'memo':document.memo,'total':document.total,'paid':document.paid,'remaining':document.total-document.paid,'ledger_entry_id':document.ledger_entry_id,'lines':[{'item_id':r.item_id,'quantity':r.quantity,'price':r.price,'discount':r.discount,'total':r.total,'cost_at_post':r.cost_at_post} for r in rows]}

@router.get('/parties')
def parties(db:DB,actor:ActorDep):
    check(actor,'finance')
    return [{'id':p.id,'name':p.name,'role':p.role,'phone':p.phone,'description':p.description} for p in db.scalars(select(FinanceParty).where(FinanceParty.organization_id==actor.org.id,FinanceParty.active.is_(True)).order_by(FinanceParty.id.desc())).all()]

@router.post('/parties',status_code=201)
def new_party(data:PartyIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    p=FinanceParty(organization_id=actor.org.id,**data.model_dump());db.add(p);db.flush()
    log(db,actor,'finance.party.create',f'party:{p.id}');db.commit()
    return {'id':p.id,'name':p.name,'role':p.role}

@router.get('/items')
def items(db:DB,actor:ActorDep):
    check(actor,'finance')
    return [{'id':i.id,'sku':i.sku,'name':i.name,'kind':i.kind,'unit':i.unit,'sale_price':i.sale_price,'purchase_price':i.purchase_price,'on_hand':i.on_hand,'avg_cost':i.avg_cost,'stock_value':i.stock_value,'min_stock':i.min_stock} for i in db.scalars(select(FinanceItem).where(FinanceItem.organization_id==actor.org.id,FinanceItem.active.is_(True)).order_by(FinanceItem.id.desc())).all()]

@router.post('/items',status_code=201)
def new_item(data:ItemIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    if db.scalar(select(FinanceItem.id).where(FinanceItem.organization_id==actor.org.id,FinanceItem.sku==data.sku)):raise HTTPException(409,'SKU already exists.')
    i=FinanceItem(organization_id=actor.org.id,**data.model_dump());db.add(i);db.flush()
    log(db,actor,'finance.item.create',f'item:{i.id}')
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'SKU already exists.')
    return {'id':i.id,'name':i.name,'sku':i.sku}

@router.get('/documents')
def documents(db:DB,actor:ActorDep,kind:Literal['sale','purchase']|None=None):
    check(actor,'finance')
    q=select(FinanceDocument).where(FinanceDocument.organization_id==actor.org.id)
    if kind:q=q.where(FinanceDocument.kind==kind)
    return [detail(db,d) for d in db.scalars(q.order_by(FinanceDocument.id.desc()).limit(300)).all()]

@router.post('/documents',status_code=201)
def new_document(data:DocumentIn,db:DB,actor:ActorDep):
    check(actor,'finance',True); org=actor.org.id
    existing=db.scalar(select(FinanceDocument).where(FinanceDocument.organization_id==org,FinanceDocument.request_key==data.request_key))
    if existing:
        # Reusing a key for a DIFFERENT invoice must never silently return an unrelated document.
        same=(existing.kind==data.kind and existing.party_id==data.party_id and existing.entry_date==str(data.entry_date) and existing.memo==data.memo)
        prev=db.scalars(select(FinanceDocumentLine).where(FinanceDocumentLine.organization_id==org,FinanceDocumentLine.document_id==existing.id).order_by(FinanceDocumentLine.id)).all()
        same=same and len(prev)==len(data.lines) and all((x.item_id,x.quantity,x.price,x.discount)==(y.item_id,y.quantity,y.price,y.discount) for x,y in zip(prev,data.lines))
        if not same:raise HTTPException(409,'Idempotency key already used for a different invoice.')
        return detail(db,existing)
    party(db,org,data.party_id);guard_period(db,org,str(data.entry_date))
    prepared=[];total=0
    for row in data.lines:
        current=item(db,org,row.item_id)
        amount=row.quantity*row.price-row.discount
        if amount<0 or amount>LIMIT:raise HTTPException(422,'Invalid line total / discount.')
        # No duplicate SKU lines: aggregate explicitly instead of hidden updates.
        if any(r.item_id==row.item_id for r,_ in prepared):raise HTTPException(422,'Duplicate item line.')
        prepared.append((row,amount));total+=amount
    if total<=0 or total>LIMIT:raise HTTPException(422,'Document total must be positive and below limit.')
    doc=FinanceDocument(organization_id=org,request_key=data.request_key,kind=data.kind,party_id=data.party_id,entry_date=str(data.entry_date),memo=data.memo,total=total,created_by=actor.user.id)
    db.add(doc);db.flush()
    for r,amount in prepared:
        db.add(FinanceDocumentLine(organization_id=org,document_id=doc.id,item_id=r.item_id,quantity=r.quantity,price=r.price,discount=r.discount,total=amount))
    log(db,actor,'finance.document.draft',f'document:{doc.id}',{'kind':doc.kind})
    try:db.commit()
    except IntegrityError:
        db.rollback();existing=db.scalar(select(FinanceDocument).where(FinanceDocument.organization_id==org,FinanceDocument.request_key==data.request_key))
        if existing:raise HTTPException(409,'Concurrent duplicate invoice; refresh the list to locate its result.')
        raise HTTPException(409,'Could not create invoice due to a concurrent conflict.')
    return detail(db,doc)

@router.post('/documents/{document_id}/post')
def post_document(document_id:int,db:DB,actor:ActorDep):
    check(actor,'finance',True);org=actor.org.id
    doc=db.scalar(select(FinanceDocument).where(FinanceDocument.organization_id==org,FinanceDocument.id==document_id).with_for_update())
    if not doc:raise HTTPException(404,'Document not found.')
    if doc.status=='posted':return detail(db,doc)
    guard_period(db,org,doc.entry_date)
    lines=db.scalars(select(FinanceDocumentLine).where(FinanceDocumentLine.document_id==doc.id,FinanceDocumentLine.organization_id==org).order_by(FinanceDocumentLine.item_id)).all()
    cost_total=0
    # Validate ALL stock first; no partial effects if a later row fails.
    locked_items={r.item_id:item(db,org,r.item_id,True) for r in lines}
    for row in lines:
        product=locked_items[row.item_id]
        if doc.kind=='sale' and product.kind=='product' and product.on_hand<row.quantity:
            raise HTTPException(409,f'Insufficient stock for SKU {product.sku}.')
        if doc.kind=='purchase' and product.kind=='service':
            raise HTTPException(422,'Services cannot be entered into stock purchases in this pilot.')
    for row in lines:
        product=locked_items[row.item_id]
        if product.kind!='product':continue
        if doc.kind=='purchase':
            new_qty=product.on_hand+row.quantity
            if new_qty>10**9:raise HTTPException(422,'Stock limit exceeded.')
            product.stock_value+=row.total
            product.on_hand=new_qty
            product.avg_cost=product.stock_value//new_qty
            delta=row.quantity
            row.cost_at_post=row.total
        else:
            # Integer-rial moving average with exact residual stock value conservation.
            row.cost_at_post=(product.stock_value*row.quantity)//product.on_hand
            cost_total+=row.cost_at_post
            product.stock_value-=row.cost_at_post
            product.on_hand-=row.quantity
            product.avg_cost=product.stock_value//product.on_hand if product.on_hand else 0
            delta=-row.quantity
        db.add(FinanceStockMovement(organization_id=org,item_id=product.id,document_id=doc.id,quantity=delta,unit_cost=row.cost_at_post//row.quantity))
    ar=account(db,org,'1100','حساب‌های دریافتنی / Receivables','asset')
    inventory=account(db,org,'1200','موجودی کالا / Inventory','asset')
    ap=account(db,org,'2100','حساب‌های پرداختنی / Payables','liability')
    revenue=account(db,org,'4100','فروش / Sales','revenue')
    cogs=account(db,org,'5100','بهای تمام‌شده / COGS','expense')
    if doc.kind=='sale':
        accounting=[(ar,doc.total,0),(revenue,0,doc.total),(cogs,cost_total,0),(inventory,0,cost_total)]
    else:accounting=[(inventory,doc.total,0),(ap,0,doc.total)]
    entry=journal(db,actor,doc.entry_date,f'{doc.kind.upper()} #{doc.id} {doc.memo}',accounting)
    doc.status='posted';doc.ledger_entry_id=entry.id
    log(db,actor,'finance.document.post',f'document:{doc.id}',{'journal_id':entry.id})
    db.commit();return detail(db,doc)

@router.get('/payments')
def payments(db:DB,actor:ActorDep):
    check(actor,'finance')
    return [{'id':p.id,'document_id':p.document_id,'amount':p.amount,'cash_account_id':p.cash_account_id,'entry_date':p.entry_date} for p in db.scalars(select(FinancePayment).where(FinancePayment.organization_id==actor.org.id).order_by(FinancePayment.id.desc()).limit(300)).all()]

@router.post('/payments',status_code=201)
def new_payment(data:PaymentIn,db:DB,actor:ActorDep):
    check(actor,'finance',True);org=actor.org.id
    prior=db.scalar(select(FinancePayment).where(FinancePayment.organization_id==org,FinancePayment.request_key==data.request_key))
    if prior:
        if (prior.document_id,prior.cash_account_id,prior.amount,prior.entry_date)!=(data.document_id,data.cash_account_id,data.amount,str(data.entry_date)):
            raise HTTPException(409,'Idempotency key already used for a different settlement.')
        return {'id':prior.id,'document_id':prior.document_id,'amount':prior.amount}
    doc=db.scalar(select(FinanceDocument).where(FinanceDocument.organization_id==org,FinanceDocument.id==data.document_id).with_for_update())
    if not doc:raise HTTPException(404,'Document not found.')
    if doc.status!='posted':raise HTTPException(409,'Document must be posted before settlement.')
    guard_period(db,org,str(data.entry_date))
    if data.amount>doc.total-doc.paid:raise HTTPException(422,'Payment exceeds outstanding balance.')
    cash=db.scalar(select(LedgerAccount).where(LedgerAccount.organization_id==org,LedgerAccount.id==data.cash_account_id,LedgerAccount.category=='asset',LedgerAccount.active.is_(True)))
    if not cash or not cash.code.startswith('10'):raise HTTPException(422,'Select an active cash/bank account with code starting 10.')
    counterpart=account(db,org,'1100' if doc.kind=='sale' else '2100','حساب‌های دریافتنی / Receivables' if doc.kind=='sale' else 'حساب‌های پرداختنی / Payables','asset' if doc.kind=='sale' else 'liability')
    if doc.kind=='sale':lines=[(cash,data.amount,0),(counterpart,0,data.amount)]
    else:lines=[(counterpart,data.amount,0),(cash,0,data.amount)]
    entry=journal(db,actor,str(data.entry_date),f'{"Receipt" if doc.kind=="sale" else "Payment"} invoice #{doc.id}',lines)
    p=FinancePayment(organization_id=org,request_key=data.request_key,document_id=doc.id,amount=data.amount,cash_account_id=cash.id,journal_entry_id=entry.id,entry_date=str(data.entry_date))
    doc.paid+=data.amount;db.add(p);db.flush()
    log(db,actor,'finance.payment.create',f'payment:{p.id}',{'document_id':doc.id})
    try:db.commit()
    except IntegrityError:
        db.rollback()
        prev=db.scalar(select(FinancePayment).where(FinancePayment.organization_id==org,FinancePayment.request_key==data.request_key))
        if prev:raise HTTPException(409,'Concurrent duplicate settlement; refresh to locate its result.')
        raise HTTPException(409,'Payment could not be saved; please refresh.')
    return {'id':p.id,'document_id':doc.id,'amount':p.amount}

@router.get('/stock-movements')
def movements(db:DB,actor:ActorDep,item_id:int|None=None):
    check(actor,'finance')
    q=select(FinanceStockMovement).where(FinanceStockMovement.organization_id==actor.org.id)
    if item_id:q=q.where(FinanceStockMovement.item_id==item_id)
    return [{'id':r.id,'item_id':r.item_id,'document_id':r.document_id,'quantity':r.quantity,'unit_cost':r.unit_cost,'created_at':r.created_at.isoformat()} for r in db.scalars(q.order_by(FinanceStockMovement.id.desc()).limit(500)).all()]

@router.get('/summary')
def summary(db:DB,actor:ActorDep):
    check(actor,'finance');org=actor.org.id
    docs=db.scalars(select(FinanceDocument).where(FinanceDocument.organization_id==org,FinanceDocument.status=='posted')).all()
    items=db.scalars(select(FinanceItem).where(FinanceItem.organization_id==org,FinanceItem.active.is_(True),FinanceItem.kind=='product')).all()
    spent=sum(e.amount for e in db.scalars(select(FinanceExpense).where(FinanceExpense.organization_id==org)).all())
    cogs=sum(line.cost_at_post for line in db.scalars(select(FinanceDocumentLine).join(FinanceDocument,FinanceDocument.id==FinanceDocumentLine.document_id).where(FinanceDocument.organization_id==org,FinanceDocument.status=='posted',FinanceDocument.kind=='sale')).all())
    return {'expenses':spent,'cost_of_goods_sold':cogs,'gross_profit':sum(d.total for d in docs if d.kind=='sale')-cogs,
            'operating_profit_before_other_items':sum(d.total for d in docs if d.kind=='sale')-cogs-spent,
            'sales':sum(d.total for d in docs if d.kind=='sale'),'purchases':sum(d.total for d in docs if d.kind=='purchase'),
            'receivables':sum(d.total-d.paid for d in docs if d.kind=='sale'),'payables':sum(d.total-d.paid for d in docs if d.kind=='purchase'),
            'stock_quantity':sum(i.on_hand for i in items),'inventory_valuation':sum(i.stock_value for i in items),
            'low_stock_count':sum(i.on_hand<=i.min_stock for i in items),'documents':len(docs)}

class ExpenseIn(BaseModel):
    title:str=Field(min_length=2,max_length=180)
    category:str=Field(default='other',min_length=2,max_length=80)
    amount:int=Field(gt=0,le=LIMIT)
    cash_account_id:int=Field(gt=0)
    entry_date:date
    request_key:str=Field(default_factory=lambda:uuid4().hex,min_length=12,max_length=80)

@router.get('/expenses')
def expenses(db:DB,actor:ActorDep):
    check(actor,'finance')
    return [{'id':e.id,'title':e.title,'category':e.category,'amount':e.amount,'entry_date':e.entry_date,'journal_entry_id':e.journal_entry_id} for e in db.scalars(select(FinanceExpense).where(FinanceExpense.organization_id==actor.org.id).order_by(FinanceExpense.id.desc()).limit(300)).all()]

@router.post('/expenses',status_code=201)
def new_expense(data:ExpenseIn,db:DB,actor:ActorDep):
    check(actor,'finance',True);org=actor.org.id
    existing=db.scalar(select(FinanceExpense).where(FinanceExpense.organization_id==org,FinanceExpense.request_key==data.request_key))
    if existing:
        if (existing.title,existing.category,existing.amount,existing.cash_account_id,existing.entry_date)!=(data.title,data.category,data.amount,data.cash_account_id,str(data.entry_date)):
            raise HTTPException(409,'Idempotency key already used for different expense.')
        return {'id':existing.id,'amount':existing.amount}
    guard_period(db,org,str(data.entry_date))
    cash=db.scalar(select(LedgerAccount).where(LedgerAccount.organization_id==org,LedgerAccount.id==data.cash_account_id,LedgerAccount.category=='asset',LedgerAccount.active.is_(True)))
    if not cash or not cash.code.startswith('10'):raise HTTPException(422,'Select a cash/bank account with code starting 10.')
    expense_account=account(db,org,'5200','هزینه‌های شرکت / Company expenses','expense')
    entry=journal(db,actor,str(data.entry_date),f'Expense {data.title}',[(expense_account,data.amount,0),(cash,0,data.amount)])
    expense=FinanceExpense(organization_id=org,request_key=data.request_key,title=data.title,category=data.category,amount=data.amount,cash_account_id=cash.id,entry_date=str(data.entry_date),journal_entry_id=entry.id)
    db.add(expense);db.flush();log(db,actor,'finance.expense.post',f'expense:{expense.id}')
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Duplicate expense; refresh to locate record.')
    return {'id':expense.id,'amount':expense.amount}

class ChequeIn(BaseModel):
    direction:Literal['received','issued']
    number:str=Field(min_length=2,max_length=64)
    party_id:int=Field(gt=0)
    amount:int=Field(gt=0,le=LIMIT)
    due_date:date
    description:str=Field(default='',max_length=350)

@router.get('/cheques')
def cheques(db:DB,actor:ActorDep,direction:Literal['received','issued']|None=None):
    check(actor,'finance')
    statement=select(FinanceCheque).where(FinanceCheque.organization_id==actor.org.id)
    if direction:statement=statement.where(FinanceCheque.direction==direction)
    return [{'id':c.id,'direction':c.direction,'number':c.number,'party_id':c.party_id,'amount':c.amount,'due_date':c.due_date,'status':c.status,'description':c.description} for c in db.scalars(statement.order_by(FinanceCheque.id.desc()).limit(300)).all()]

@router.post('/cheques',status_code=201)
def new_cheque(data:ChequeIn,db:DB,actor:ActorDep):
    check(actor,'finance',True);party(db,actor.org.id,data.party_id)
    exists=db.scalar(select(FinanceCheque.id).where(FinanceCheque.organization_id==actor.org.id,FinanceCheque.number==data.number,FinanceCheque.direction==data.direction))
    if exists:raise HTTPException(409,'Cheque number already tracked in this direction.')
    cheque=FinanceCheque(organization_id=actor.org.id,**{**data.model_dump(),'due_date':str(data.due_date)})
    db.add(cheque);db.flush();log(db,actor,'finance.cheque.track',f'cheque:{cheque.id}',{'non_posting':True})
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Cheque number already exists.')
    return {'id':cheque.id,'status':'pending','posting':'tracking_only'}

@router.get('/cash-movements')
def cash_movements(db:DB,actor:ActorDep):
    """Read-only cash/bank movements from POSTED journals, per account with running balances."""
    check(actor,'finance');org=actor.org.id
    accounts=db.scalars(select(LedgerAccount).where(LedgerAccount.organization_id==org,LedgerAccount.category=='asset')).all()
    accounts={a.id:a for a in accounts if a.code.startswith('10')}
    if not accounts:return []
    transactions=db.execute(select(JournalLine,JournalEntry).join(JournalEntry,JournalEntry.id==JournalLine.entry_id).where(JournalLine.organization_id==org,JournalEntry.organization_id==org,JournalEntry.posted.is_(True),JournalLine.account_id.in_(list(accounts))).order_by(JournalEntry.entry_date,JournalEntry.id,JournalLine.id)).all()
    running={a:0 for a in accounts};out=[]
    for line,entry in transactions:
        running[line.account_id]+=line.debit-line.credit
        out.append({'account_id':line.account_id,'account_name':accounts[line.account_id].name,'code':accounts[line.account_id].code,'journal_id':entry.id,'date':entry.entry_date,'memo':entry.memo,'debit':line.debit,'credit':line.credit,'balance':running[line.account_id]})
    return out[-500:]
