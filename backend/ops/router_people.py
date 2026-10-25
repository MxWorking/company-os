"""HR personnel and support contact APIs. Never expose national IDs or attachments via list endpoints."""
from typing import Annotated, Literal
from urllib.parse import urlparse
import re
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from .models import Account, Membership
from .models_people import Personnel, SupportContact
from .router import actor_dep, Actor, check, log

router=APIRouter(prefix='/api/v2',tags=['Personnel and support'])
DB=Annotated[Session,Depends(get_db)]
ActorDep=Annotated[Actor,Depends(actor_dep)]

class PersonnelIn(BaseModel):
    account_id:int
    personnel_code:str=Field(min_length=1,max_length=32)
    job_title:str=Field(default='',max_length=120)
    department:str=Field(default='',max_length=120)
    employment_type:Literal['full_time','part_time','contract','intern','temporary']='full_time'
    employment_status:Literal['active','leave','inactive','terminated']='active'
    hired_on:str=Field(default='',max_length=10)
    work_email:str=Field(default='',max_length=254)
    work_phone:str=Field(default='',max_length=32)


def person_json(db,row):
    acc=db.get(Account,row.account_id)
    return {'id':row.id,'account_id':row.account_id,'name':acc.full_name if acc else '', 'username':acc.username if acc else '',
        'personnel_code':row.personnel_code,'job_title':row.job_title,'department':row.department,
        'employment_type':row.employment_type,'employment_status':row.employment_status,
        'hired_on':row.hired_on,'work_email':row.work_email,'work_phone':row.work_phone}

@router.get('/personnel/accounts')
def personnel_accounts(db:DB,actor:ActorDep):
    check(actor,'hr')
    members=db.scalars(select(Membership).where(Membership.organization_id==actor.org.id)).all()
    return [{'account_id':m.account_id,'name':db.get(Account,m.account_id).full_name,'username':db.get(Account,m.account_id).username,'role':m.role} for m in members if db.get(Account,m.account_id) and db.get(Account,m.account_id).active]

@router.get('/personnel')
def list_personnel(db:DB,actor:ActorDep):
    check(actor,'hr')
    rows=db.scalars(select(Personnel).where(Personnel.organization_id==actor.org.id).order_by(Personnel.id.desc())).all()
    return [person_json(db,row) for row in rows]

@router.post('/personnel',status_code=201)
def add_personnel(data:PersonnelIn,db:DB,actor:ActorDep):
    check(actor,'hr',True)
    membership=db.scalar(select(Membership.id).where(Membership.organization_id==actor.org.id,Membership.account_id==data.account_id))
    if not membership:raise HTTPException(422,'Employee needs an organization user account first.')
    row=Personnel(organization_id=actor.org.id,**data.model_dump())
    db.add(row)
    try:log(db,actor,'personnel.create',f'account:{data.account_id}');db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Employee or personnel code already registered.')
    db.refresh(row);return person_json(db,row)

@router.put('/personnel/{account_id}')
def edit_personnel(account_id:int,data:PersonnelIn,db:DB,actor:ActorDep):
    check(actor,'hr',True)
    row=db.scalar(select(Personnel).where(Personnel.organization_id==actor.org.id,Personnel.account_id==account_id))
    if not row:raise HTTPException(404,'Personnel record not found.')
    if data.account_id!=account_id:raise HTTPException(422,'Cannot move a personnel profile to another account.')
    for key,value in data.model_dump().items():setattr(row,key,value)
    try:log(db,actor,'personnel.update',f'account:{account_id}');db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Personnel code already used.')
    return person_json(db,row)

class ContactIn(BaseModel):
    audience:Literal['company','developer']='company'
    kind:Literal['phone','email','telegram','whatsapp','eitaa','instagram','rubika','website']='phone'
    label:str=Field(min_length=1,max_length=100)
    value:str=Field(min_length=3,max_length=400)
    active:bool=True


def href(kind,value):
    if kind=='phone':
        if not re.fullmatch(r'[+0-9\s().-]{5,32}',value):raise HTTPException(422,'Invalid phone number.')
        return 'tel:'+re.sub(r'[^+0-9]','',value)
    if kind=='email':
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise HTTPException(422,'Invalid email address.')
        return 'mailto:'+value
    if value.startswith('http://'):raise HTTPException(422,'Use HTTPS contact URLs.')
    parsed=urlparse(value)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password:
        raise HTTPException(422,'A valid HTTPS URL is required.')
    return value


def contact_json(c):
    return {'id':c.id,'audience':c.audience,'kind':c.kind,'label':c.label,'value':c.value,'href':href(c.kind,c.value),'active':c.active}

@router.get('/support/contacts')
def contacts(db:DB,actor:ActorDep):
    check(actor,'support')
    rows=db.scalars(select(SupportContact).where(SupportContact.organization_id==actor.org.id,SupportContact.active.is_(True)).order_by(SupportContact.id)).all()
    return [contact_json(x) for x in rows]

@router.post('/support/contacts',status_code=201)
def add_contact(data:ContactIn,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin'):raise HTTPException(403,'Only administrators can configure support contacts.')
    href(data.kind,data.value)
    obj=SupportContact(organization_id=actor.org.id,**data.model_dump())
    db.add(obj);db.flush();log(db,actor,'support.contact_add',f'contact:{obj.id}');db.commit();db.refresh(obj)
    return contact_json(obj)

@router.delete('/support/contacts/{contact_id}',status_code=204)
def delete_contact(contact_id:int,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin'):raise HTTPException(403,'Only administrators can configure support contacts.')
    obj=db.scalar(select(SupportContact).where(SupportContact.organization_id==actor.org.id,SupportContact.id==contact_id))
    if not obj:raise HTTPException(404,'Contact not found.')
    db.delete(obj);log(db,actor,'support.contact_remove',f'contact:{contact_id}');db.commit()
    return Response(status_code=204)
