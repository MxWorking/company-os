"""Strictly non-posting preparation records based on Aadin navigation research.
All endpoints enforce authenticated tenant membership and finance permissions.
These are NOT a financial journal, payment or inventory engine.
"""
from typing import Any
import math
from datetime import date
from fastapi import APIRouter,HTTPException,Query
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import select,func
from .router import DB,ActorDep,check,log
from .models_accounting_drafts import AccountingDraft

router=APIRouter(prefix='/api/v2/accounting/preparations',tags=['Accounting preparations (non-posting)'])
# These categories must not be mistaken for accounting postings.
KINDS={
 'person','item','service','invoice_charge','sales_quote','sales_invoice','purchase_invoice',
 'sales_return','purchase_return','receipt','disbursement','cashbox','bank_account',
 'expense','cheque_in','cheque_out','customer_order','catalog',
 'party_group','item_group','item_tag','item_unit','expense_group',
 'sales_setting','purchase_setting','appearance_setting','currency_setting',
 'invoice_template_setting','message_template_setting'
}
# Only non-sensitive generic identity fields. No credentials, legal documents or bank numbers.
DETAIL_FIELDS={'reference','date','party','group','item_code','unit','quantity','unit_price',
 'amount','due_date','description','contact','price_level','related_document',
 'ratio','sort_order','value','note','currency','calendar','tax_percent'}
TEXT_FIELDS=DETAIL_FIELDS-{'quantity','unit_price','amount','ratio','sort_order','tax_percent'}

class DraftIn(BaseModel):
    kind:str=Field(min_length=1,max_length=32)
    title:str=Field(min_length=2,max_length=180)
    details:dict[str,Any]=Field(default_factory=dict)
    @field_validator('kind')
    @classmethod
    def valid_kind(cls,v):
        if v not in KINDS:raise ValueError('Unknown preparation category')
        return v
    @field_validator('title')
    @classmethod
    def valid_title(cls,v):
        if not v.strip():raise ValueError('Title is required')
        return v
    @field_validator('details')
    @classmethod
    def valid_details(cls,v):
        if len(v)>len(DETAIL_FIELDS) or set(v)-DETAIL_FIELDS:raise ValueError('Unsupported detail fields')
        for key,value in v.items():
            if key in TEXT_FIELDS:
                if not isinstance(value,str) or len(value)>500:raise ValueError(f'{key} must be a short string')
                if key in ('date','due_date') and value:
                    try:date.fromisoformat(value)
                    except ValueError:raise ValueError(f'{key} must be YYYY-MM-DD') from None
            else:
                if type(value) not in (int,float) or not math.isfinite(value) or value<0 or value>10**13:raise ValueError(f'{key} is out of range')
        return v

def out(row:AccountingDraft):
    return {'id':row.id,'kind':row.kind,'title':row.title,'details':row.details,'status':'preparation_only',
            'created_at':row.created_at.isoformat() if row.created_at else None}

@router.get('')
def list_drafts(db:DB,actor:ActorDep,kind:str|None=None,limit:int=Query(100,ge=1,le=200)):
    check(actor,'finance')
    if kind is not None and kind not in KINDS:raise HTTPException(422,'Unknown category')
    statement=select(AccountingDraft).where(AccountingDraft.organization_id==actor.org.id,AccountingDraft.archived.is_(False))
    if kind:statement=statement.where(AccountingDraft.kind==kind)
    return {'items':[out(r) for r in db.scalars(statement.order_by(AccountingDraft.id.desc()).limit(limit)).all()]}

@router.post('',status_code=201)
def create_draft(data:DraftIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    row=AccountingDraft(organization_id=actor.org.id,created_by=actor.user.id,kind=data.kind,
                        title=data.title.strip(),details=data.details)
    db.add(row);db.flush();log(db,actor,'accounting.preparation.create',f'preparation:{row.id}',{'kind':data.kind})
    db.commit();db.refresh(row);return out(row)

@router.patch('/{draft_id}')
def update_draft(draft_id:int,data:DraftIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    row=db.scalar(select(AccountingDraft).where(AccountingDraft.id==draft_id,
      AccountingDraft.organization_id==actor.org.id,AccountingDraft.archived.is_(False)))
    if row is None:raise HTTPException(404,'Preparation not found')
    if row.kind!=data.kind:raise HTTPException(422,'Category cannot be changed')
    row.title=data.title.strip();row.details=data.details
    log(db,actor,'accounting.preparation.update',f'preparation:{row.id}')
    db.commit();db.refresh(row);return out(row)

@router.delete('/{draft_id}',status_code=204)
def archive_draft(draft_id:int,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    row=db.scalar(select(AccountingDraft).where(AccountingDraft.id==draft_id,
        AccountingDraft.organization_id==actor.org.id,AccountingDraft.archived.is_(False)))
    if row is None:raise HTTPException(404,'Preparation not found')
    row.archived=True;log(db,actor,'accounting.preparation.archive',f'preparation:{row.id}')
    db.commit()
