"""Self-registration (pending approval) and limited staff-to-accounting communication.

No signup endpoint accepts a privileged role. Finance requests are not ledger entries.
"""
from datetime import datetime, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .models import Account, Organization, Membership
from .models_registration import JoinApplication,FinanceRequest,FinanceRequestMessage
from .router import DB, ActorDep, make_hash, verify_hash, log, may

router=APIRouter(prefix='/api/v2',tags=['Self service membership and finance requests'])

class RegisterIn(BaseModel):
    username:str=Field(min_length=3,max_length=80,pattern=r'^[A-Za-z0-9_.@-]+$')
    full_name:str=Field(min_length=2,max_length=160)
    password:str=Field(min_length=12,max_length=200)
    organization_slug:str=Field(min_length=3,max_length=80,pattern=r'^[a-z0-9-]+$')
    requested_job_title:str=Field(min_length=2,max_length=120)
    department:str=Field(default='',max_length=120)

class LoginCheck(BaseModel):
    username:str
    password:str

class ReviewIn(BaseModel):
    decision:Literal['approved','rejected']
    approved_job_title:str=Field(default='',max_length=120)
    assigned_role:Literal['viewer','member','accountant','manager','admin']='member'
    reason:str=Field(default='',max_length=500)


def app_json(row,db):
    acc=db.get(Account,row.account_id)
    return {'id':row.id,'account_id':row.account_id,'username':acc.username,'full_name':acc.full_name,
            'organization_id':row.organization_id,'requested_job_title':row.requested_job_title,
            'approved_job_title':row.approved_job_title,'department':row.department,'status':row.status,
            'assigned_role':row.assigned_role,'reason':row.review_reason,'created_at':row.created_at.isoformat() if row.created_at else None}

@router.post('/auth/register',status_code=201)
def register(data:RegisterIn,db:DB):
    org=db.scalar(select(Organization).where(Organization.slug==data.organization_slug))
    if not org:raise HTTPException(404,'Organization registration is not available. Ask the organization administrator for its workspace code.')
    if db.scalar(select(Account.id).where(Account.username==data.username.strip())):
        raise HTTPException(409,'This username is unavailable. If previously rejected, contact the organization administrator.')
    user=Account(username=data.username.strip(),full_name=data.full_name.strip(),password_hash=make_hash(data.password),active=False)
    db.add(user);db.flush()
    db.add(JoinApplication(organization_id=org.id,account_id=user.id,
        requested_job_title=data.requested_job_title.strip(),department=data.department.strip(),status='pending'))
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'This username is unavailable.')
    return {'status':'pending','message':'Registration submitted. An organization administrator must approve your account and job title before you can sign in.'}

class ReapplyIn(BaseModel):
    username:str
    password:str
    requested_job_title:str=Field(min_length=2,max_length=120)
    department:str=Field(default='',max_length=120)

@router.post('/auth/reapply')
def reapply(data:ReapplyIn,db:DB):
    user=db.scalar(select(Account).where(Account.username==data.username))
    if not user or not verify_hash(data.password,user.password_hash):raise HTTPException(401,'Invalid credentials.')
    row=db.scalar(select(JoinApplication).where(JoinApplication.account_id==user.id))
    if not row or row.status!='rejected' or user.active:raise HTTPException(409,'This account cannot reapply.')
    row.requested_job_title=data.requested_job_title.strip();row.department=data.department.strip()
    row.status='pending';row.review_reason=None;row.reviewer_id=None;row.reviewed_at=None
    row.assigned_role=None;row.approved_job_title=None
    db.commit()
    return {'status':'pending','message':'Reapplication submitted for review.'}

@router.post('/auth/application-status')
def application_status(data:LoginCheck,db:DB):
    """Authenticated by password even before active membership; no private organization details."""
    account=db.scalar(select(Account).where(Account.username==data.username))
    if not account or not verify_hash(data.password,account.password_hash):raise HTTPException(401,'Invalid credentials.')
    row=db.scalar(select(JoinApplication).where(JoinApplication.account_id==account.id))
    return {'status':row.status if row else ('active' if account.active else 'inactive'),
            'message':row.review_reason if row and row.status=='rejected' else None}

@router.get('/membership-applications')
def applications(db:DB,actor:ActorDep,status:str='pending'):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Administrator approval required.')
    if status not in ('pending','approved','rejected','all'):raise HTTPException(422,'Invalid status filter.')
    conditions=[JoinApplication.organization_id==actor.org.id]
    if status!='all':conditions.append(JoinApplication.status==status)
    rows=db.scalars(select(JoinApplication).where(*conditions).order_by(JoinApplication.created_at.desc()).limit(150)).all()
    return [app_json(r,db) for r in rows]

@router.post('/membership-applications/{application_id}/review')
def review_application(application_id:int,data:ReviewIn,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Administrator approval required.')
    row=db.scalar(select(JoinApplication).where(JoinApplication.id==application_id,JoinApplication.organization_id==actor.org.id).with_for_update())
    if not row:raise HTTPException(404,'Application not found.')
    if row.status!='pending':raise HTTPException(409,'Application has already been reviewed.')
    if data.decision=='approved' and data.assigned_role in ('admin','manager') and actor.role not in ('owner','admin'):
        raise HTTPException(403,'Only top-level administrators may approve a privileged access role.')
    user=db.get(Account,row.account_id)
    if not user:raise HTTPException(404,'Account not found.')
    if data.decision=='approved':
        if not data.approved_job_title.strip():raise HTTPException(422,'Approved job title is required.')
        if db.scalar(select(Membership.id).where(Membership.account_id==user.id,Membership.organization_id==actor.org.id)):
            raise HTTPException(409,'Membership already exists.')
        row.approved_job_title=data.approved_job_title.strip()
        row.assigned_role=data.assigned_role
        user.active=True
        db.add(Membership(organization_id=actor.org.id,account_id=user.id,role=data.assigned_role))
    else:
        user.active=False
        row.review_reason=data.reason.strip()
    row.status=data.decision
    row.reviewer_id=actor.user.id
    row.reviewed_at=datetime.now(timezone.utc)
    log(db,actor,'registration.'+data.decision,f'application:{row.id}',{'role':row.assigned_role,'title':row.approved_job_title})
    db.commit()
    return app_json(row,db)

class FinanceRequestIn(BaseModel):
    subject:str=Field(min_length=3,max_length=180)
    description:str=Field(min_length=5,max_length=5000)

class FinanceMessageIn(BaseModel):
    body:str=Field(min_length=1,max_length=5000)

class FinanceStatusIn(BaseModel):
    status:Literal['open','in_review','answered','closed']


def finance_dto(row,db):
    requester=db.get(Account,row.requester_id)
    return {'id':row.id,'subject':row.subject,'description':row.description,'status':row.status,
      'requester_id':row.requester_id,'requester':requester.full_name if requester else 'Unknown',
      'created_at':row.created_at.isoformat() if row.created_at else None}

def finance_authorized(actor):
    return actor.role in {'owner','admin','manager','accountant'} and may(actor,'finance')

def request_allowed(db,actor,id_):
    row=db.scalar(select(FinanceRequest).where(FinanceRequest.id==id_,FinanceRequest.organization_id==actor.org.id))
    if not row:raise HTTPException(404,'Request not found.')
    if not finance_authorized(actor) and row.requester_id!=actor.user.id:
        raise HTTPException(404,'Request not found.')
    return row

@router.post('/finance-requests',status_code=201)
def new_finance_request(data:FinanceRequestIn,db:DB,actor:ActorDep):
    row=FinanceRequest(organization_id=actor.org.id,requester_id=actor.user.id,subject=data.subject.strip(),description=data.description.strip())
    db.add(row);db.flush();log(db,actor,'finance.request.create',f'finance_request:{row.id}');db.commit();db.refresh(row)
    return finance_dto(row,db)

@router.get('/finance-requests')
def list_finance_requests(db:DB,actor:ActorDep):
    conditions=[FinanceRequest.organization_id==actor.org.id]
    if not finance_authorized(actor):conditions.append(FinanceRequest.requester_id==actor.user.id)
    rows=db.scalars(select(FinanceRequest).where(*conditions).order_by(FinanceRequest.id.desc()).limit(150)).all()
    return [finance_dto(row,db) for row in rows]

@router.get('/finance-requests/{request_id}/messages')
def finance_messages(request_id:int,db:DB,actor:ActorDep):
    request_allowed(db,actor,request_id)
    rows=db.scalars(select(FinanceRequestMessage).where(FinanceRequestMessage.request_id==request_id,FinanceRequestMessage.organization_id==actor.org.id).order_by(FinanceRequestMessage.id)).all()
    return [{'id':r.id,'author_id':r.author_id,'author':db.get(Account,r.author_id).full_name,'body':r.body,
     'created_at':r.created_at.isoformat() if r.created_at else None} for r in rows]

@router.post('/finance-requests/{request_id}/messages',status_code=201)
def post_finance_message(request_id:int,data:FinanceMessageIn,db:DB,actor:ActorDep):
    row=request_allowed(db,actor,request_id)
    if row.status=='closed' and not finance_authorized(actor):raise HTTPException(409,'This request is closed.')
    msg=FinanceRequestMessage(organization_id=actor.org.id,request_id=row.id,author_id=actor.user.id,body=data.body.strip())
    db.add(msg);db.flush();log(db,actor,'finance.request.message',f'finance_request:{row.id}');db.commit()
    return {'id':msg.id,'ok':True}

@router.patch('/finance-requests/{request_id}/status')
def set_finance_status(request_id:int,data:FinanceStatusIn,db:DB,actor:ActorDep):
    if not finance_authorized(actor):raise HTTPException(403,'Accounting role required.')
    row=request_allowed(db,actor,request_id)
    row.status=data.status;log(db,actor,'finance.request.status',f'finance_request:{row.id}',{'status':data.status});db.commit()
    return finance_dto(row,db)
