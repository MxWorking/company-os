"""Company OS v2 modular workspace API: tenant-scoped, permission-checked MVP.

Not a payroll, storage service, real-time chat, external AI or workflow execution engine.
"""
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from typing import Annotated, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from .models import Organization, Account, Membership, Record, RecordLink, Note, Checklist, AuditEvent
from .models_ext import ModuleGrant
from .catalog import CATALOG, MODULES, STATUSES, checked_payload

router=APIRouter(prefix='/api/v2',tags=['Company OS 2.0 Workspace'])
DB=Annotated[Session,Depends(get_db)]
DEMO_MODE=os.environ.get('APP_ENV','development')=='test' and os.environ.get('DEMO_MODE','false').lower()=='true' and 'pytest' in __import__('sys').modules
REFERENCE_KINDS={
    ('project','customer'):'customer',('board','project'):'project',('task','project'):'project',('task','board'):'board',
    ('message','channel'):'channel',('message','reply_to'):'message',
    ('referral','letter'):'letter',('contact','customer'):'customer',
    ('lead','customer'):'customer',('opportunity','customer'):'customer',
    ('invoice','customer'):'customer',('invoice','project'):'project',
    ('payment','invoice'):'invoice',('cost','project'):'project',('worklog','task'):'task',
}
ALLOWED_ROLES={'owner','admin','manager','accountant','member','viewer'}
MANAGE_ROLES={'owner','admin'}
WRITE_ROLES={'owner','admin','manager'}


def make_hash(password:str)->str:
    if len(password)<10:raise ValueError('Password must have at least 10 characters')
    salt=secrets.token_bytes(16)
    key=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
    return 'scrypt:'+salt.hex()+':'+key.hex()


def verify_hash(password:str,stored:str)->bool:
    if not stored.startswith('scrypt:'):return False
    try:
        _,salt,key=stored.split(':')
        actual=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=2**14,r=8,p=1)
        return hmac.compare_digest(actual,bytes.fromhex(key))
    except (ValueError,TypeError):return False


def seed_workspace(db:Session):
    """Bootstrap ONLY the first organization owner; never rotate credentials on restart."""
    org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
    if org is None:
        org=Organization(name='Company OS',slug='company-os');db.add(org);db.flush()
    username=os.environ.get('ADMIN_USERNAME','admin').strip()
    existing_owner=db.scalar(select(Account).join(Membership,Membership.account_id==Account.id).where(
        Membership.organization_id==org.id,Membership.role=='owner').order_by(Membership.id))
    if existing_owner:
        # Opt-in for hosted deployments where the owner explicitly manages credentials
        # in server-side environment variables. Never create a second owner, and never
        # modify staff, organizations, projects, or accounting records.
        env_sync=os.environ.get('ADMIN_ENV_SYNC','false').strip().lower() in ('true','1','yes')
        if env_sync and not DEMO_MODE:
            from .bootstrap import validate_bootstrap_env, BootstrapConfigError
            validate_bootstrap_env()
            owners=db.scalars(select(Account).join(Membership,Membership.account_id==Account.id).where(
                Membership.organization_id==org.id,Membership.role=='owner').order_by(Membership.id)).all()
            if len(owners)!=1:
                raise BootstrapConfigError('ADMIN_ENV_SYNC requires exactly one company-os owner; no account was modified.')
            if existing_owner.username != username:
                username_taken=db.scalar(select(Account.id).where(Account.username==username))
                if username_taken is not None:
                    raise BootstrapConfigError('ADMIN_USERNAME belongs to another account; owner sync refused without changes.')
                existing_owner.username=username
            if not verify_hash(os.environ['ADMIN_PASSWORD'],existing_owner.password_hash):
                existing_owner.password_hash=make_hash(os.environ['ADMIN_PASSWORD'])
            # Preserve the owner account ID, memberships, active flag and all tenant data.
        elif not DEMO_MODE:
            import logging
            logger=logging.getLogger('companyos.bootstrap')
            if existing_owner.username != username:
                logger.warning(
                    'ADMIN_USERNAME differs from the EXISTING owner account. Existing owner login remains active. '
                    'To manage owner credentials automatically from server environment variables, set ADMIN_ENV_SYNC=true. '
                    'Or use the explicit admin reset command.'
                )
            elif not verify_hash(os.environ.get('ADMIN_PASSWORD',''),existing_owner.password_hash):
                logger.warning(
                    'ADMIN_PASSWORD differs from the SAVED owner password hash. '
                    'Set ADMIN_ENV_SYNC=true to opt into env-managed owner credentials, or explicitly reset the account.'
                )
        db.commit()
    else:
        account=db.scalar(select(Account).where(Account.username==username))
        if account is not None and not DEMO_MODE:
            raise RuntimeError('Configured ADMIN_USERNAME already exists without owner membership. Refusing automatic privilege elevation.')
        if account is None:
            password=os.environ.get('ADMIN_PASSWORD','')
            if not DEMO_MODE and len(password)<12:
                raise RuntimeError('ADMIN_PASSWORD must be at least 12 characters. Check .env next to docker-compose.yml.')
            account=Account(username=username,full_name='Organization Administrator',password_hash=make_hash(password if password else secrets.token_urlsafe(24)))
            db.add(account);db.flush()
        db.add(Membership(organization_id=org.id,account_id=account.id,role='owner'))
        db.commit()
    if DEMO_MODE and not db.scalar(select(Record.id).where(Record.organization_id==org.id)):
        seeds=[
          ('department','Design & Development','open',{'code':'DEV','manager':'Hossein'}),
          ('team','Product Team','open',{'department':'Design & Development','lead':'Hossein'}),
          ('project','Website Renewal','in_progress',{'owner':'Hossein','progress':65,'description':'Example project for exploring multi-view management'}),
          ('board','Delivery Board','open',{'view':'kanban'}),
          ('task','Prepare UI components','in_progress',{'assignee':'Hossein','assignee_id':account.id if not existing_owner else existing_owner.id,'priority':'high','description':'Demo task; drag through workflow statuses'}),
          ('task','Review acceptance criteria','planned',{'assignee':'Product Team','priority':'medium'}),
          ('contract','Sample employment agreement','in_review',{'employee_code':'EMP-001','type':'full_time'}),
          ('leave','Holiday request','open',{'employee_code':'EMP-001','reason':'Example leave request'}),
          ('channel','General','open',{'description':'Team discussion'}),
          ('meeting','Weekly planning','planned',{'participants':'Product Team'}),
          ('document','Brand Guidelines','approved',{'code':'DOC-001','category':'policy','revision':1}),
          ('letter','Design approval memo','in_review',{'direction':'internal','recipient':'Management'}),
          ('customer','Acme Demo','open',{'company':'Acme Ltd','email':'team@example.com'}),
          ('opportunity','Platform Redesign','in_progress',{'stage':'proposal','value':25000000,'owner':'Hossein'}),
          ('invoice','Demo invoice','planned',{'amount':12000000,'currency':'IRR'}),
          ('cost','Hosting services','approved',{'amount':1500000,'currency':'IRR'}),
          ('worklog','UI research time','approved',{'worker':'Hossein','minutes':120}),
          ('report','Project activity','open',{'metric':'projects','range':'month'}),
          ('automation','Task completion notice','planned',{'trigger':'task_completed','action':'notify','enabled':False}),
        ]
        creator_id=existing_owner.id if existing_owner else account.id
        db.add_all(Record(organization_id=org.id,kind=kind,title=title,status=status,payload=payload,created_by=creator_id) for kind,title,status,payload in seeds)
        db.commit()


@dataclass
class Actor:
    user:Account
    org:Organization
    role:str
    grants:dict


def actor_dep(request:Request, db:DB)->Actor:
    account_id=request.session.get('v2_account_id')
    account=db.get(Account,account_id) if isinstance(account_id,int) else None
    if account_id is None and DEMO_MODE:
        account=db.scalar(select(Account).where(Account.username==os.environ.get('ADMIN_USERNAME','admin')))
    if not account or not account.active:raise HTTPException(401,'Sign in to access Company OS.')
    org_id=request.session.get('v2_org_id')
    if org_id is None:
        member=db.scalar(select(Membership).where(Membership.account_id==account.id).order_by(Membership.id))
    else:
        member=db.scalar(select(Membership).where(Membership.account_id==account.id,Membership.organization_id==org_id))
    if not member:raise HTTPException(403,'Not a member of the requested organization.')
    org=db.get(Organization,member.organization_id)
    if not org:raise HTTPException(403,'Organization does not exist.')
    if not DEMO_MODE and request.method in {'POST','PATCH','PUT','DELETE'} and not request.url.path.endswith('/auth/login'):
        # CSRF token in a custom header; ensures cross-site HTML forms cannot mutate workspace data.
        token=request.session.get('v2_csrf')
        if not token or not hmac.compare_digest(str(token),request.headers.get('x-company-csrf','')):
            raise HTTPException(403,'CSRF token missing or invalid.')
    grants={g.module:{"read":g.can_read,"write":g.can_write} for g in db.scalars(select(ModuleGrant).where(ModuleGrant.organization_id==org.id,ModuleGrant.account_id==account.id)).all()}
    return Actor(account,org,member.role,grants)

ActorDep=Annotated[Actor,Depends(actor_dep)]


MODULE_ACCESS={
  'owner':{'*':'write'},'admin':{'*':'write'},
  'manager':{'*':'write'},
  'accountant':{'work':'read','collaboration':'write','finance':'write','notes':'write','support':'write'},
  'member':{'work':'write','collaboration':'write','notes':'write','support':'write'},
  'viewer':{'work':'read','notes':'write','support':'write'},
}

def may(actor:Actor,module:str,write:bool=False)->bool:
    if actor.role in MANAGE_ROLES | {'manager'}:return True
    # Accounting cannot be unlocked by an arbitrary staff grant.
    if module=='finance' and actor.role!='accountant':return False
    if module in actor.grants:
        g=actor.grants[module]
        return bool(g['write'] if write else g['read'] or g['write'])
    mode=MODULE_ACCESS.get(actor.role,{}).get(module,MODULE_ACCESS.get(actor.role,{}).get('*','none'))
    return mode=='write' if write else mode in ('read','write')

def check(actor:Actor,module:str,write:bool=False):
    if not may(actor,module,write):raise HTTPException(403,'Permission denied for this module.')


def log(db:Session,actor:Actor,action:str,target:str,detail:dict|None=None):
    db.add(AuditEvent(organization_id=actor.org.id,actor_id=actor.user.id,action=action,target=target,detail=detail or {}))


def dto(record:Record)->dict:
    return {'id':record.id,'organization_id':record.organization_id,'kind':record.kind,'title':record.title,'status':record.status,
            'payload':record.payload,'version':record.version,'created_at':record.created_at.isoformat() if record.created_at else None}


def record_or_404(db:Session,actor:Actor,record_id:int)->Record:
    record=db.scalar(select(Record).where(Record.id==record_id,Record.organization_id==actor.org.id,Record.archived.is_(False)))
    if not record:raise HTTPException(404,'Record not found.')
    check(actor,CATALOG[record.kind][0])
    if record.kind=='project' and actor.role not in MANAGE_ROLES|{'manager'}:
        from .models_ext import ProjectMember
        allowed=db.scalar(select(ProjectMember.id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==record.id,ProjectMember.account_id==actor.user.id))
        if not allowed:raise HTTPException(403,'Not a participant in this project.')
    if record.kind=='task' and actor.role not in MANAGE_ROLES|{'manager'}:
        from .models_ext import ProjectMember
        proj=record.payload.get('project')
        allowed=bool(db.scalar(select(ProjectMember.id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==int(proj),ProjectMember.account_id==actor.user.id))) if proj and str(proj).isdigit() else False
        if not allowed and record.created_by!=actor.user.id and record.payload.get('assignee_id')!=actor.user.id:
            raise HTTPException(403,'Task is not assigned to you.')
    return record


def check_record_write(actor:Actor,record:Record):
    check(actor,CATALOG[record.kind][0],True)
    if actor.role=='member' and not actor.grants.get(CATALOG[record.kind][0],{}).get('write',False):
        if record.kind not in {'task','message','meeting'}:
            raise HTTPException(403,'Members can modify only assigned tasks or their collaboration records.')
        if record.kind=='task' and record.created_by!=actor.user.id and record.payload.get('assignee_id')!=actor.user.id:
            raise HTTPException(403,'Not assigned to this task.')
        if record.kind in {'message','meeting'} and record.created_by!=actor.user.id:
            raise HTTPException(403,'Cannot modify another member content.')

def validated_references(db:Session,actor:Actor,kind:str,payload:dict):
    if kind=='task' and payload.get('assignee_id') is not None:
        assignee=db.scalar(select(Membership.id).where(Membership.organization_id==actor.org.id,Membership.account_id==payload['assignee_id']))
        if not assignee:raise HTTPException(422,'Task assignee must be a member of this organization.')
    for name,type_ in CATALOG[kind][1].items():
        if type_!='ref' or not payload.get(name):continue
        value=payload[name]
        try:identifier=int(value)
        except (TypeError,ValueError):raise HTTPException(422,f'{name}: expected record ID')
        referenced=record_or_404(db,actor,identifier)
        expected=REFERENCE_KINDS.get((kind,name))
        if expected and referenced.kind!=expected:raise HTTPException(422,f'{name}: reference must be a {expected} record')


class Login(BaseModel):
    username:str
    password:str

class OrgCreate(BaseModel):
    name:str=Field(min_length=2,max_length=160)
    slug:str=Field(min_length=3,max_length=80,pattern=r'^[a-z0-9-]+$')

class AccountCreate(BaseModel):
    username:str=Field(min_length=3,max_length=120,pattern=r'^[a-zA-Z0-9_.@-]+$')
    full_name:str=Field(min_length=2,max_length=160)
    password:str=Field(min_length=10,max_length=200)
    role:str='member'

class RecordCreate(BaseModel):
    title:str=Field(min_length=1,max_length=200)
    status:str='new'
    payload:dict[str,Any]=Field(default_factory=dict)

class RecordChange(BaseModel):
    title:str|None=Field(default=None,min_length=1,max_length=200)
    status:str|None=None
    payload:dict[str,Any]|None=None
    version:int=Field(ge=1)

class NoteInput(BaseModel):
    body:str=Field(min_length=1,max_length=4000)

class ChecklistInput(BaseModel):
    title:str=Field(min_length=1,max_length=160)

class LinkInput(BaseModel):
    target_id:int
    relation:str=Field(default='related',min_length=1,max_length=40)

@router.post('/auth/login')
def user_login(data:Login,request:Request,db:DB):
    account=db.scalar(select(Account).where(Account.username==data.username))
    if not account or not verify_hash(data.password,account.password_hash):raise HTTPException(401,'Invalid credentials.')
    if not account.active:
        from .models_registration import JoinApplication
        application=db.scalar(select(JoinApplication).where(JoinApplication.account_id==account.id))
        raise HTTPException(403,'Registration is '+application.status+'. Wait for administrator approval.' if application else 'Account inactive.')
    membership=db.scalar(select(Membership).where(Membership.account_id==account.id).order_by(Membership.id))
    if not membership:raise HTTPException(403,'Account has no organization membership.')
    request.session.clear()
    request.session.update({'v2_account_id':account.id,'v2_org_id':membership.organization_id,'v2_csrf':secrets.token_urlsafe(24),'authenticated':True})
    return {'ok':True,'role':membership.role}

@router.get('/me')
def me(request:Request,db:DB,actor:ActorDep):
    memberships=db.scalars(select(Membership).where(Membership.account_id==actor.user.id)).all()
    if not request.session.get('v2_csrf'):
        request.session['v2_csrf']=secrets.token_urlsafe(24)
    from .models_registration import JoinApplication
    application=db.scalar(select(JoinApplication).where(JoinApplication.account_id==actor.user.id,JoinApplication.organization_id==actor.org.id))
    return {'id':actor.user.id,'username':actor.user.username,'name':actor.user.full_name,'role':actor.role,
      'job_title':application.approved_job_title if application else None,
      'organization':{'id':actor.org.id,'name':actor.org.name,'slug':actor.org.slug},
      'organizations':[{'id':m.organization_id,'name':db.get(Organization,m.organization_id).name,'role':m.role} for m in memberships],
      'csrf':request.session.get('v2_csrf'),'demo':DEMO_MODE,
      'permissions':{mod:{'read':may(actor,mod),'write':may(actor,mod,True)} for mod in list(MODULES)+['notes','support','identity']}}

@router.post('/organizations',status_code=201)
def create_org(data:OrgCreate,db:DB,actor:ActorDep):
    if actor.role not in MANAGE_ROLES:raise HTTPException(403,'Admin only.')
    if db.scalar(select(Organization.id).where(Organization.slug==data.slug)):
        raise HTTPException(409,'Organization slug already used.')
    org=Organization(name=data.name,slug=data.slug)
    db.add(org);db.flush()
    db.add(Membership(organization_id=org.id,account_id=actor.user.id,role='owner'))
    db.add(AuditEvent(organization_id=org.id,actor_id=actor.user.id,action='organization.create',target=f'organization:{org.id}',detail={}))
    db.commit();db.refresh(org)
    return {'id':org.id,'name':org.name,'slug':org.slug}

@router.post('/organizations/switch')
def switch_org(org_id:int,request:Request,db:DB,actor:ActorDep):
    member=db.scalar(select(Membership).where(Membership.account_id==actor.user.id,Membership.organization_id==org_id))
    if not member:raise HTTPException(403,'You are not a member of this organization.')
    request.session['v2_org_id']=org_id
    return {'ok':True,'organization_id':org_id}

@router.get('/members')
def members(db:DB,actor:ActorDep):
    check(actor,'organization')
    out=[]
    for member in db.scalars(select(Membership).where(Membership.organization_id==actor.org.id)).all():
        user=db.get(Account,member.account_id)
        out.append({'id':member.id,'account_id':user.id,'username':user.username,'full_name':user.full_name,'role':member.role,'active':user.active})
    return out

@router.post('/members',status_code=201)
def add_member(data:AccountCreate,db:DB,actor:ActorDep):
    if actor.role not in MANAGE_ROLES:raise HTTPException(403,'Admin only.')
    if data.role not in ALLOWED_ROLES or data.role=='owner':raise HTTPException(422,'Invalid assignable role.')
    if db.scalar(select(Account.id).where(Account.username==data.username)):raise HTTPException(409,'Username already exists.')
    user=Account(username=data.username,full_name=data.full_name,password_hash=make_hash(data.password))
    db.add(user);db.flush();db.add(Membership(organization_id=actor.org.id,account_id=user.id,role=data.role))
    log(db,actor,'member.add',f'account:{user.id}',{'role':data.role});db.commit()
    return {'id':user.id,'username':user.username,'role':data.role}

@router.patch('/members/{account_id}/role')
def change_role(account_id:int,role:str,db:DB,actor:ActorDep):
    if actor.role not in MANAGE_ROLES:raise HTTPException(403,'Admin only.')
    if role not in ALLOWED_ROLES or role=='owner':raise HTTPException(422,'Invalid role')
    member=db.scalar(select(Membership).where(Membership.organization_id==actor.org.id,Membership.account_id==account_id))
    if not member:raise HTTPException(404,'Member not found.')
    if account_id==actor.user.id:raise HTTPException(422,'Cannot change your own role.')
    member.role=role;log(db,actor,'member.role',f'account:{account_id}',{'role':role});db.commit()
    return {'ok':True,'role':role}

@router.get('/catalog')
def catalog(actor:ActorDep):
    modules={module:list(kinds) for module,kinds in MODULES.items() if may(actor,module)}
    return {'modules':modules,
            'kinds':{kind:{'module':value[0],'fields':value[1]} for kind,value in CATALOG.items() if may(actor,value[0])},
            'statuses':STATUSES}

@router.get('/my-work')
def my_work(db:DB,actor:ActorDep):
    check(actor,'work')
    tasks=db.scalars(select(Record).where(Record.organization_id==actor.org.id,Record.kind=='task',Record.archived.is_(False))).all()
    mine=[r for r in tasks if r.payload.get('assignee_id')==actor.user.id or (not r.payload.get('assignee_id') and r.created_by==actor.user.id)]
    return {'items':[dto(x) for x in mine],'total':len(mine)}

@router.get('/records/{kind}')
def list_records(kind:str,db:DB,actor:ActorDep,q:str='',status:str='',limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0)):
    if kind not in CATALOG:raise HTTPException(404,'Unknown record type.')
    check(actor,CATALOG[kind][0])
    clause=[Record.organization_id==actor.org.id,Record.kind==kind,Record.archived.is_(False)]
    if status:clause.append(Record.status==status)
    if q:clause.append(Record.title.ilike('%'+q.replace('%','')[:100]+'%'))
    # For team members, never return every project/task just because they know the kind.
    if kind in ('project','task') and actor.role not in MANAGE_ROLES|{'manager'}:
        from .models_ext import ProjectMember
        memberships=set(db.scalars(select(ProjectMember.project_id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.account_id==actor.user.id)).all())
        candidates=db.scalars(select(Record).where(*clause).order_by(Record.id.desc())).all()
        rows=[r for r in candidates if (r.id in memberships if kind=='project' else r.created_by==actor.user.id or r.payload.get('assignee_id')==actor.user.id or (str(r.payload.get('project','')).isdigit() and int(r.payload['project']) in memberships))]
        count=len(rows);rows=rows[offset:offset+limit]
    else:
        count=db.scalar(select(func.count(Record.id)).where(*clause)) or 0
        rows=db.scalars(select(Record).where(*clause).order_by(Record.id.desc()).limit(limit).offset(offset)).all()
    return {'items':[dto(x) for x in rows],'total':count,'limit':limit,'offset':offset}

@router.post('/records/{kind}',status_code=201)
def add_record(kind:str,data:RecordCreate,db:DB,actor:ActorDep):
    if kind not in CATALOG:raise HTTPException(404,'Unknown record type.')
    check(actor,CATALOG[kind][0],True)
    if actor.role=='member' and not actor.grants.get(CATALOG[kind][0],{}).get('write',False) and kind not in {'task','message','meeting'}:raise HTTPException(403,'Member cannot create this record type.')
    if data.status not in STATUSES:raise HTTPException(422,'Invalid status.')
    payload=checked_payload(kind,data.payload)
    validated_references(db,actor,kind,payload)
    if actor.role=='member' and not actor.grants.get('work',{}).get('write',False) and kind=='task' and payload.get('assignee_id') not in (None,actor.user.id):raise HTTPException(403,'Cannot assign a task to someone else.')
    if actor.role=='member' and kind=='task' and payload.get('project'):
        from .models_ext import ProjectMember
        if not db.scalar(select(ProjectMember.id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==int(payload['project']),ProjectMember.account_id==actor.user.id)):
            raise HTTPException(403,'Not a participant in this project.')
    obj=Record(organization_id=actor.org.id,kind=kind,title=data.title,status=data.status,payload=payload,created_by=actor.user.id)
    db.add(obj);db.flush();log(db,actor,'record.create',f'{kind}:{obj.id}');db.commit();db.refresh(obj)
    return dto(obj)

@router.get('/record/{record_id}')
def one_record(record_id:int,db:DB,actor:ActorDep):
    return dto(record_or_404(db,actor,record_id))

@router.patch('/record/{record_id}')
def update_record(record_id:int,data:RecordChange,db:DB,actor:ActorDep):
    obj=record_or_404(db,actor,record_id)
    check_record_write(actor,obj)
    if obj.version!=data.version:raise HTTPException(409,'Record changed by another user. Reload before saving.')
    if data.status is not None:
        if data.status not in STATUSES:raise HTTPException(422,'Invalid status.')
        if data.status in {'approved','rejected'} and actor.role not in WRITE_ROLES:raise HTTPException(403,'Approval requires manager permission.')
        obj.status=data.status
    if data.title is not None:obj.title=data.title
    if data.payload is not None:
        payload=checked_payload(obj.kind,data.payload)
        validated_references(db,actor,obj.kind,payload)
        if actor.role=='member' and not actor.grants.get('work',{}).get('write',False) and obj.kind=='task' and payload.get('assignee_id',actor.user.id)!=actor.user.id:raise HTTPException(403,'Cannot reassign a task.')
        obj.payload={**obj.payload,**payload}
    obj.version+=1
    log(db,actor,'record.update',f'{obj.kind}:{obj.id}',{'version':obj.version});db.commit();db.refresh(obj)
    return dto(obj)

@router.delete('/record/{record_id}',status_code=204)
def archive_record(record_id:int,db:DB,actor:ActorDep):
    obj=record_or_404(db,actor,record_id);check_record_write(actor,obj)
    obj.archived=True;obj.version+=1;log(db,actor,'record.archive',f'{obj.kind}:{obj.id}');db.commit()
    return Response(status_code=204)

@router.get('/record/{record_id}/notes')
def list_notes(record_id:int,db:DB,actor:ActorDep):
    record_or_404(db,actor,record_id)
    return [{'id':n.id,'body':n.body,'author':db.get(Account,n.author_id).full_name,'created_at':n.created_at.isoformat()} for n in db.scalars(select(Note).where(Note.organization_id==actor.org.id,Note.record_id==record_id).order_by(Note.id)).all()]

@router.post('/record/{record_id}/notes',status_code=201)
def add_note(record_id:int,data:NoteInput,db:DB,actor:ActorDep):
    obj=record_or_404(db,actor,record_id);check_record_write(actor,obj)
    note=Note(organization_id=actor.org.id,record_id=obj.id,author_id=actor.user.id,body=data.body)
    db.add(note);db.flush();log(db,actor,'note.create',f'{obj.kind}:{obj.id}');db.commit()
    return {'id':note.id,'body':note.body}

@router.get('/record/{record_id}/checklist')
def list_checklist(record_id:int,db:DB,actor:ActorDep):
    obj=record_or_404(db,actor,record_id)
    if obj.kind!='task':raise HTTPException(422,'Checklists require a task.')
    return [{'id':item.id,'title':item.title,'done':item.done} for item in db.scalars(select(Checklist).where(Checklist.organization_id==actor.org.id,Checklist.task_id==record_id).order_by(Checklist.id)).all()]

@router.post('/record/{record_id}/checklist',status_code=201)
def add_checklist(record_id:int,data:ChecklistInput,db:DB,actor:ActorDep):
    obj=record_or_404(db,actor,record_id)
    if obj.kind!='task':raise HTTPException(422,'Checklists require a task.')
    check_record_write(actor,obj)
    item=Checklist(organization_id=actor.org.id,task_id=record_id,title=data.title,created_by=actor.user.id)
    db.add(item);db.commit();db.refresh(item);return {'id':item.id,'title':item.title,'done':item.done}

@router.patch('/checklist/{item_id}')
def check_item(item_id:int,done:bool,db:DB,actor:ActorDep):
    check(actor,'work',True)
    item=db.scalar(select(Checklist).where(Checklist.id==item_id,Checklist.organization_id==actor.org.id))
    if not item:raise HTTPException(404,'Checklist item not found.')
    task=record_or_404(db,actor,item.task_id)
    check_record_write(actor,task)
    item.done=done;db.commit();return {'id':item.id,'done':item.done}

@router.post('/record/{record_id}/links',status_code=201)
def link_record(record_id:int,data:LinkInput,db:DB,actor:ActorDep):
    source=record_or_404(db,actor,record_id);target=record_or_404(db,actor,data.target_id)
    check_record_write(actor,source)
    if source.id==target.id:raise HTTPException(422,'A record cannot reference itself.')
    if source.kind=='task' and target.kind=='task' and data.relation=='depends_on':
        # Reject cycles by following the dependency graph.
        visited=set();queue=[target.id]
        while queue:
            current=queue.pop()
            if current==source.id:raise HTTPException(422,'Circular task dependency.')
            if current in visited:continue
            visited.add(current)
            queue.extend(db.scalars(select(RecordLink.to_id).where(RecordLink.organization_id==actor.org.id,RecordLink.from_id==current,RecordLink.relation=='depends_on')).all())
    existing=db.scalar(select(RecordLink.id).where(RecordLink.organization_id==actor.org.id,RecordLink.from_id==source.id,RecordLink.to_id==target.id,RecordLink.relation==data.relation))
    if existing:raise HTTPException(409,'Link already exists.')
    db.add(RecordLink(organization_id=actor.org.id,from_id=source.id,to_id=target.id,relation=data.relation));db.commit()
    return {'ok':True}

@router.get('/record/{record_id}/links')
def links(record_id:int,db:DB,actor:ActorDep):
    record_or_404(db,actor,record_id)
    return [{'to_id':e.to_id,'relation':e.relation} for e in db.scalars(select(RecordLink).where(RecordLink.organization_id==actor.org.id,RecordLink.from_id==record_id)).all()]

@router.get('/analytics/summary')
def analytics(db:DB,actor:ActorDep):
    result={}
    for module,kinds in MODULES.items():
        if not may(actor,module):continue
        rows=db.execute(select(Record.kind,func.count(Record.id)).where(Record.organization_id==actor.org.id,Record.archived.is_(False),Record.kind.in_(kinds)).group_by(Record.kind)).all()
        result[module]={kind:count for kind,count in rows}
    totals={'finance_irr_cost':0,'finance_irr_invoiced':0,'worklog_minutes':0}
    if may(actor,"finance"):
        for kind,key,field in [('cost','finance_irr_cost','amount'),('invoice','finance_irr_invoiced','amount'),('worklog','worklog_minutes','minutes')]:
            entries=db.scalars(select(Record).where(Record.organization_id==actor.org.id,Record.kind==kind,Record.archived.is_(False))).all()
            totals[key]=sum(int(row.payload.get(field,0) or 0) for row in entries if kind=='worklog' or row.payload.get('currency','IRR')=='IRR')
    return {'organization_id':actor.org.id,'counts':result,'totals':totals,'computed_at':datetime.now().astimezone().isoformat(),'source':'organization-scoped operational records'}

@router.get('/audit')
def audit_events(db:DB,actor:ActorDep,limit:int=Query(40,ge=1,le=100)):
    if actor.role not in MANAGE_ROLES:raise HTTPException(403,'Admin only.')
    events=db.scalars(select(AuditEvent).where(AuditEvent.organization_id==actor.org.id).order_by(AuditEvent.id.desc()).limit(limit)).all()
    return [{'id':e.id,'action':e.action,'target':e.target,'actor_id':e.actor_id,'at':e.created_at.isoformat()} for e in events]

@router.post('/assistant/query')
def assistant_query(data:NoteInput,db:DB,actor:ActorDep):
    """Permission-scoped deterministic summary, not an LLM."""
    check(actor,'work')
    from .models_ext import ProjectMember
    tasks=db.scalars(select(Record).where(Record.organization_id==actor.org.id,Record.kind=='task',Record.archived.is_(False))).all()
    if actor.role not in MANAGE_ROLES|{'manager'}:
        projects=set(db.scalars(select(ProjectMember.project_id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.account_id==actor.user.id)).all())
        tasks=[r for r in tasks if r.created_by==actor.user.id or r.payload.get('assignee_id')==actor.user.id or (str(r.payload.get('project','')).isdigit() and int(r.payload['project']) in projects)]
    counts={'my_visible_tasks':len(tasks)}
    return {'mode':'permission-scoped-statistical','answer':f"Tasks visible to you: {len(tasks)}. This assistant is not connected to an LLM.",'counts':counts,'actions_executed':0}

@router.post('/auth/logout')
def user_logout(request:Request):
    request.session.clear()
    return {'ok':True}
