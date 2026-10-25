"""Company OS 2.1: scoped collaboration, personal notes, permissions, identity vault, accounting.

This is an implementable core, NOT a certified accounting / e-sign / SMS / video platform.
"""
import hashlib, hmac, os, re
from datetime import date
from io import BytesIO
from typing import Literal
from fastapi import APIRouter, HTTPException, UploadFile, File, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .router import Actor, ActorDep, DB, check, may, log, verify_hash, make_hash
from .models import Account, Membership, Record
from .models_ext import (ModuleGrant,ProjectMember,ProjectMessage,ProjectEvent,PrivateNote,SupportTicket,
    IdentityProfile,IdentityDocument,LedgerAccount,JournalEntry,JournalLine,FiscalPeriod)

router=APIRouter(prefix='/api/v2', tags=['Company OS 2.1 Extensions'])
MODULES_GRANTABLE={'organization','work','hr','collaboration','documents','crm','finance','intelligence','notes','support','identity'}

class GrantIn(BaseModel):
    module:str
    read:bool=True
    write:bool=False

@router.get('/members/{account_id}/grants')
def get_grants(account_id:int, db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin'):raise HTTPException(403,'Admin only.')
    member=db.scalar(select(Membership).where(Membership.organization_id==actor.org.id,Membership.account_id==account_id))
    if not member:raise HTTPException(404,'Not a member.')
    return [{'module':p.module,'read':p.can_read,'write':p.can_write} for p in db.scalars(select(ModuleGrant).where(ModuleGrant.organization_id==actor.org.id,ModuleGrant.account_id==account_id)).all()]

@router.put('/members/{account_id}/grants')
def set_grant(account_id:int,data:GrantIn,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin'):raise HTTPException(403,'Admin only.')
    if data.module not in MODULES_GRANTABLE:raise HTTPException(422,'Invalid module.')
    member=db.scalar(select(Membership).where(Membership.organization_id==actor.org.id,Membership.account_id==account_id))
    if not member:raise HTTPException(404,'Not a member.')
    if data.module=='finance' and member.role!='accountant' and (data.read or data.write):
        raise HTTPException(422,'Finance access is restricted to accountants and organizational managers.')
    if member.role in ('owner','admin'):raise HTTPException(403,'Cannot override an administrator; change role instead.')
    if account_id==actor.user.id:raise HTTPException(403,'Cannot edit your own grant.')
    grant=db.scalar(select(ModuleGrant).where(ModuleGrant.organization_id==actor.org.id,ModuleGrant.account_id==account_id,ModuleGrant.module==data.module))
    if not grant:
        grant=ModuleGrant(organization_id=actor.org.id,account_id=account_id,module=data.module)
        db.add(grant)
    grant.can_read=data.read or data.write;grant.can_write=data.write
    log(db,actor,'permission.update',f'account:{account_id}',{'module':data.module,'read':grant.can_read,'write':data.write})
    db.commit();return {'ok':True,'module':data.module,'read':grant.can_read,'write':grant.can_write}

class PasswordChange(BaseModel):
    old_password:str
    new_password:str=Field(min_length=12,max_length=200)

@router.put('/account/password')
def change_password(data:PasswordChange,db:DB,actor:ActorDep):
    if not verify_hash(data.old_password,actor.user.password_hash):raise HTTPException(403,'Incorrect current password.')
    if hmac.compare_digest(data.old_password,data.new_password):raise HTTPException(422,'Use a different password.')
    actor.user.password_hash=make_hash(data.new_password)
    log(db,actor,'password.changed',f'account:{actor.user.id}')
    db.commit();return {'ok':True,'message':'Password updated. Other sessions have not yet been revoked.'}

class ProfileName(BaseModel):
    full_name:str=Field(min_length=2,max_length=160)

@router.put('/account/profile')
def change_profile(data:ProfileName,db:DB,actor:ActorDep):
    actor.user.full_name=data.full_name
    log(db,actor,'profile.changed',f'account:{actor.user.id}')
    db.commit();return {'ok':True,'name':data.full_name}


def project_access(db,actor:Actor,project_id:int,write:bool=False):
    check(actor,'work',write)
    obj=db.scalar(select(Record).where(Record.id==project_id,Record.kind=='project',Record.organization_id==actor.org.id,Record.archived.is_(False)))
    if not obj:raise HTTPException(404,'Project not found.')
    if actor.role in ('owner','admin','manager') and may(actor,'work',write):return obj
    assigned=db.scalar(select(ProjectMember.id).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==project_id,ProjectMember.account_id==actor.user.id))
    if not assigned:raise HTTPException(403,'You are not assigned to this project.')
    return obj

class ProjectInvite(BaseModel):
    account_id:int
    project_role:Literal['manager','contributor','viewer']='contributor'

@router.get('/projects/{project_id}/members')
def project_members(project_id:int,db:DB,actor:ActorDep):
    project_access(db,actor,project_id)
    members=db.scalars(select(ProjectMember).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==project_id)).all()
    return [{'account_id':m.account_id,'name':db.get(Account,m.account_id).full_name,'project_role':m.project_role} for m in members]

@router.post('/projects/{project_id}/members',status_code=201)
def invite_project_member(project_id:int,data:ProjectInvite,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Project assignment requires manager role.')
    project_access(db,actor,project_id,True)
    member=db.scalar(select(Membership.id).where(Membership.organization_id==actor.org.id,Membership.account_id==data.account_id))
    if not member:raise HTTPException(422,'Account must belong to this organization.')
    exists=db.scalar(select(ProjectMember).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==project_id,ProjectMember.account_id==data.account_id))
    if exists:raise HTTPException(409,'Already a project member.')
    db.add(ProjectMember(organization_id=actor.org.id,project_id=project_id,account_id=data.account_id,project_role=data.project_role))
    log(db,actor,'project.invite',f'project:{project_id}',{'account_id':data.account_id})
    db.commit();return {'ok':True}

@router.delete('/projects/{project_id}/members/{account_id}',status_code=204)
def remove_project_member(project_id:int,account_id:int,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Manager required.')
    project_access(db,actor,project_id,True)
    membership=db.scalar(select(ProjectMember).where(ProjectMember.organization_id==actor.org.id,ProjectMember.project_id==project_id,ProjectMember.account_id==account_id))
    if not membership:raise HTTPException(404,'Project member not found.')
    db.delete(membership);log(db,actor,'project.remove_member',f'project:{project_id}',{'account_id':account_id});db.commit()
    return Response(status_code=204)

class MessageIn(BaseModel):
    body:str=Field(min_length=1,max_length=5000)
    category:Literal['chat','daily','change','decision','announcement']='chat'

@router.get('/messages')
def messages(db:DB,actor:ActorDep,project_id:int|None=None,limit:int=Query(100,ge=1,le=200)):
    check(actor,'collaboration')
    if project_id is not None:project_access(db,actor,project_id)
    records=db.scalars(select(ProjectMessage).where(ProjectMessage.organization_id==actor.org.id,ProjectMessage.project_id==project_id).order_by(ProjectMessage.id.desc()).limit(limit)).all()
    return [{'id':m.id,'body':m.body,'category':m.category,'author':db.get(Account,m.author_id).full_name,'author_id':m.author_id,'created_at':m.created_at.isoformat()} for m in reversed(records)]

@router.post('/messages',status_code=201)
def write_message(data:MessageIn,db:DB,actor:ActorDep,project_id:int|None=None):
    check(actor,'collaboration',True)
    if project_id is not None:project_access(db,actor,project_id,True)
    if data.category in ('decision','announcement') and actor.role not in ('owner','admin','manager'):
        raise HTTPException(403,'Decisions/announcements require manager access.')
    msg=ProjectMessage(organization_id=actor.org.id,project_id=project_id,author_id=actor.user.id,body=data.body.strip(),category=data.category)
    db.add(msg);log(db,actor,'message.post',f'project:{project_id}' if project_id else 'global',{'category':data.category});db.commit();db.refresh(msg)
    return {'id':msg.id,'body':msg.body,'category':msg.category}

class ProjectEventIn(BaseModel):
    title:str=Field(min_length=1,max_length=180)
    starts_on:date
    ends_on:date|None=None
    event_type:Literal['milestone','delivery','purchase','meeting','work','deadline']='milestone'
    description:str=Field(default='',max_length=1500)

@router.get('/projects/{project_id}/events')
def events(project_id:int,db:DB,actor:ActorDep):
    project_access(db,actor,project_id)
    rows=db.scalars(select(ProjectEvent).where(ProjectEvent.organization_id==actor.org.id,ProjectEvent.project_id==project_id).order_by(ProjectEvent.starts_on,ProjectEvent.id)).all()
    return [{'id':x.id,'title':x.title,'starts_on':x.starts_on,'ends_on':x.ends_on,'event_type':x.event_type,'description':x.description} for x in rows]

@router.post('/projects/{project_id}/events',status_code=201)
def add_event(project_id:int,data:ProjectEventIn,db:DB,actor:ActorDep):
    project_access(db,actor,project_id,True)
    if data.ends_on and data.ends_on<data.starts_on:raise HTTPException(422,'End date must not precede start date.')
    event=ProjectEvent(organization_id=actor.org.id,project_id=project_id,created_by=actor.user.id,starts_on=str(data.starts_on),ends_on=str(data.ends_on) if data.ends_on else None,title=data.title,event_type=data.event_type,description=data.description)
    db.add(event);log(db,actor,'project.event',f'project:{project_id}',{'type':event.event_type});db.commit();db.refresh(event)
    return {'id':event.id,'title':event.title}

@router.delete('/projects/{project_id}/events/{event_id}',status_code=204)
def delete_event(project_id:int,event_id:int,db:DB,actor:ActorDep):
    project_access(db,actor,project_id,True)
    event=db.scalar(select(ProjectEvent).where(ProjectEvent.id==event_id,ProjectEvent.project_id==project_id,ProjectEvent.organization_id==actor.org.id))
    if not event:raise HTTPException(404,'Event not found.')
    if event.created_by!=actor.user.id and actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Owner or manager only.')
    db.delete(event);db.commit();return Response(status_code=204)

class PersonalNoteIn(BaseModel):
    title:str=Field(min_length=1,max_length=180)
    body:str=Field(default='',max_length=15000)
    project_id:int|None=None

@router.get('/private-notes')
def private_notes(db:DB,actor:ActorDep,project_id:int|None=None):
    check(actor,'notes')
    if project_id is not None:project_access(db,actor,project_id)
    rows=db.scalars(select(PrivateNote).where(PrivateNote.organization_id==actor.org.id,PrivateNote.owner_id==actor.user.id,PrivateNote.project_id==project_id).order_by(PrivateNote.id.desc())).all()
    return [{'id':x.id,'title':x.title,'body':x.body,'project_id':x.project_id,'updated_at':x.updated_at.isoformat()} for x in rows]

@router.post('/private-notes',status_code=201)
def create_private_note(data:PersonalNoteIn,db:DB,actor:ActorDep):
    check(actor,'notes',True)
    if data.project_id is not None:project_access(db,actor,data.project_id)
    note=PrivateNote(organization_id=actor.org.id,owner_id=actor.user.id,project_id=data.project_id,title=data.title,body=data.body)
    db.add(note);db.commit();db.refresh(note);return {'id':note.id,'title':note.title}

@router.put('/private-notes/{note_id}')
def edit_private_note(note_id:int,data:PersonalNoteIn,db:DB,actor:ActorDep):
    check(actor,'notes',True)
    note=db.scalar(select(PrivateNote).where(PrivateNote.id==note_id,PrivateNote.organization_id==actor.org.id,PrivateNote.owner_id==actor.user.id))
    if not note:raise HTTPException(404,'Note not found.')
    if data.project_id!=note.project_id:raise HTTPException(422,'Cannot move note across contexts.')
    note.title=data.title;note.body=data.body;db.commit();return {'ok':True}

@router.delete('/private-notes/{note_id}',status_code=204)
def delete_private_note(note_id:int,db:DB,actor:ActorDep):
    check(actor,'notes',True)
    note=db.scalar(select(PrivateNote).where(PrivateNote.id==note_id,PrivateNote.organization_id==actor.org.id,PrivateNote.owner_id==actor.user.id))
    if not note:raise HTTPException(404,'Note not found.')
    db.delete(note);db.commit();return Response(status_code=204)

class TicketIn(BaseModel):
    audience:Literal['internal','developer']='internal'
    title:str=Field(min_length=2,max_length=180)
    message:str=Field(min_length=4,max_length=4000)

@router.get('/support/tickets')
def tickets(db:DB,actor:ActorDep):
    check(actor,'support')
    rows=db.scalars(select(SupportTicket).where(SupportTicket.organization_id==actor.org.id).order_by(SupportTicket.id.desc())).all()
    if actor.role not in ('owner','admin','manager'):
        rows=[r for r in rows if r.author_id==actor.user.id]
    return [{'id':x.id,'title':x.title,'message':x.message,'audience':x.audience,'status':x.status,'created_at':x.created_at.isoformat()} for x in rows]

@router.post('/support/tickets',status_code=201)
def add_ticket(data:TicketIn,db:DB,actor:ActorDep):
    check(actor,'support',True)
    ticket=SupportTicket(organization_id=actor.org.id,author_id=actor.user.id,audience=data.audience,title=data.title,message=data.message)
    db.add(ticket);db.commit();db.refresh(ticket);return {'id':ticket.id,'status':ticket.status,'delivery':'local-ticket-only'}

@router.get('/support/config')
def support_config(actor:ActorDep):
    check(actor,'support')
    return {'developer_email':os.getenv('DEVELOPER_SUPPORT_EMAIL',''), 'internal_contact':os.getenv('INTERNAL_SUPPORT_CONTACT',''), 'tickets_are_local_only':True}

# Identity vault: crypto key must be configured, never silent plaintext fallback.
def crypto()->AESGCM:
    raw=os.environ.get('HR_ENCRYPTION_KEY','')
    try:
        key=bytes.fromhex(raw)
        if len(key)!=32:raise ValueError()
    except ValueError:
        raise HTTPException(503,'Configure HR_ENCRYPTION_KEY (64 hex digits) before processing identity data.')
    return AESGCM(key)

def seal(value:bytes,aad:bytes)->bytes:
    from secrets import token_bytes
    nonce=token_bytes(12)
    return nonce+crypto().encrypt(nonce,value,aad)

def unseal(value:bytes,aad:bytes)->bytes:
    return crypto().decrypt(value[:12],value[12:],aad)

def ascii_digits(value:str)->str:
    return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'))

def national_id_valid(value:str)->bool:
    s=ascii_digits(value)
    if not re.fullmatch(r'\d{10}',s) or len(set(s))==1:return False
    result=sum(int(s[i])*(10-i) for i in range(9))%11
    return int(s[-1])==(result if result<2 else 11-result)

def identity_target(db,actor,account_id:int):
    check(actor,'identity',True)
    member=db.scalar(select(Membership.id).where(Membership.organization_id==actor.org.id,Membership.account_id==account_id))
    if not member:raise HTTPException(404,'Account is not an organization member.')

class IdentityIn(BaseModel):
    national_id:str=Field(min_length=10,max_length=10)
    phone:str=Field(min_length=10,max_length=16)

@router.put('/identity/{account_id}')
def update_identity(account_id:int,data:IdentityIn,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    nid=ascii_digits(data.national_id)
    if not national_id_valid(nid):raise HTTPException(422,'Invalid Iranian national ID checksum.')
    phone=ascii_digits(data.phone).replace(' ','').replace('-','')
    if not re.fullmatch(r'(?:\+98|0098|0)?9\d{9}',phone):raise HTTPException(422,'Invalid Iranian mobile format.')
    normalized='+98'+phone[-10:]
    aad=f'{actor.org.id}:{account_id}'.encode()
    key=crypto() # fail closed, before any mutation
    digest=hmac.new(bytes.fromhex(os.environ['HR_ENCRYPTION_KEY']),f'{actor.org.id}:{nid}'.encode(),hashlib.sha256).hexdigest()
    match=db.scalar(select(IdentityProfile).where(IdentityProfile.organization_id==actor.org.id,IdentityProfile.national_id_hmac==digest,IdentityProfile.account_id!=account_id))
    if match:raise HTTPException(409,'National ID is already registered in this organization.')
    profile=db.scalar(select(IdentityProfile).where(IdentityProfile.organization_id==actor.org.id,IdentityProfile.account_id==account_id))
    if not profile:
        profile=IdentityProfile(organization_id=actor.org.id,account_id=account_id)
        db.add(profile)
    profile.national_id_cipher=seal(nid.encode(),aad+b':national_id')
    profile.national_id_hmac=digest
    profile.phone_cipher=seal(normalized.encode(),aad+b':phone')
    profile.phone_verified=False
    log(db,actor,'identity.updated',f'account:{account_id}')
    db.commit()
    return {'ok':True,'phone_verified':False,'message':'Saved encrypted. Phone verification requires SMS provider integration.'}

@router.get('/identity/{account_id}')
def read_identity(account_id:int,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    p=db.scalar(select(IdentityProfile).where(IdentityProfile.organization_id==actor.org.id,IdentityProfile.account_id==account_id))
    if not p:return {'exists':False}
    aad=f'{actor.org.id}:{account_id}'.encode()
    log(db,actor,'identity.view',f'account:{account_id}');db.commit()
    return {'exists':True,'national_id':unseal(p.national_id_cipher,aad+b':national_id').decode() if p.national_id_cipher else None,
            'phone':unseal(p.phone_cipher,aad+b':phone').decode() if p.phone_cipher else None,'phone_verified':p.phone_verified}

@router.post('/identity/{account_id}/verify-phone')
def verify_phone_unavailable(account_id:int,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    raise HTTPException(501,'SMS OTP provider is not configured. Phone is not verified.')

@router.post('/identity/{account_id}/documents',status_code=201)
async def upload_identity_document(account_id:int,kind:Literal['national_card_front','national_card_back','birth_certificate','other'],db:DB,actor:ActorDep,file:UploadFile=File(...)):
    identity_target(db,actor,account_id)
    crypto()
    if file.content_type not in {'image/png','image/jpeg','application/pdf'}:raise HTTPException(415,'Only PNG, JPEG and PDF are accepted.')
    data=await file.read(5*1024*1024+1)
    if not data or len(data)>5*1024*1024:raise HTTPException(413,'File must be 1 byte to 5 MB.')
    mime=('application/pdf' if data.startswith(b'%PDF-') else 'image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if data.startswith(b'\xff\xd8\xff') else '')
    if mime!=file.content_type:raise HTTPException(415,'File signature does not match declared type.')
    from pathlib import PurePath
    title=PurePath((file.filename or 'document').replace('\\','/')).name[:180]
    item=IdentityDocument(organization_id=actor.org.id,account_id=account_id,kind=kind,mime_type=mime,original_name=title,
        encrypted_bytes=seal(data,f'{actor.org.id}:{account_id}:{kind}'.encode()))
    db.add(item);db.flush();log(db,actor,'identity.document_upload',f'document:{item.id}',{'kind':kind});db.commit()
    return {'id':item.id,'kind':kind,'size':len(data),'encrypted':True}

@router.get('/identity/{account_id}/documents')
def list_identity_documents(account_id:int,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    return [{'id':d.id,'kind':d.kind,'name':d.original_name,'created_at':d.created_at.isoformat()} for d in db.scalars(select(IdentityDocument).where(IdentityDocument.organization_id==actor.org.id,IdentityDocument.account_id==account_id)).all()]

@router.get('/identity/{account_id}/documents/{document_id}')
def download_identity_document(account_id:int,document_id:int,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    doc=db.scalar(select(IdentityDocument).where(IdentityDocument.id==document_id,IdentityDocument.organization_id==actor.org.id,IdentityDocument.account_id==account_id))
    if not doc:raise HTTPException(404,'Document not found.')
    contents=unseal(doc.encrypted_bytes,f'{actor.org.id}:{account_id}:{doc.kind}'.encode())
    log(db,actor,'identity.document_download',f'document:{document_id}');db.commit()
    return StreamingResponse(BytesIO(contents),media_type=doc.mime_type,headers={'Content-Disposition':'attachment; filename="identity-document"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

# Accounting core: immutable posted double-entry journal, tenant scoped, integer IRR units.
class LedgerAccountIn(BaseModel):
    code:str=Field(pattern=r'^[0-9A-Za-z._-]{2,24}$')
    name:str=Field(min_length=2,max_length=180)
    category:Literal['asset','liability','equity','revenue','expense']

class LedgerLineIn(BaseModel):
    account_id:int
    debit:int=Field(default=0,ge=0,le=10**13)
    credit:int=Field(default=0,ge=0,le=10**13)

class JournalIn(BaseModel):
    entry_date:date
    memo:str=Field(min_length=3,max_length=350)
    lines:list[LedgerLineIn]=Field(min_length=2,max_length=40)

@router.get('/ledger/accounts')
def ledger_accounts(db:DB,actor:ActorDep):
    check(actor,'finance')
    return [{'id':a.id,'code':a.code,'name':a.name,'category':a.category,'active':a.active} for a in db.scalars(select(LedgerAccount).where(LedgerAccount.organization_id==actor.org.id).order_by(LedgerAccount.code)).all()]

@router.post('/ledger/accounts',status_code=201)
def create_ledger_account(data:LedgerAccountIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    if db.scalar(select(LedgerAccount.id).where(LedgerAccount.organization_id==actor.org.id,LedgerAccount.code==data.code)):
        raise HTTPException(409,'Account code already exists.')
    acc=LedgerAccount(organization_id=actor.org.id,**data.model_dump())
    db.add(acc);log(db,actor,'ledger.account_create',f'account:{data.code}');db.commit();db.refresh(acc)
    return {'id':acc.id,'code':acc.code}

@router.get('/ledger/entries')
def journal_entries(db:DB,actor:ActorDep):
    check(actor,'finance')
    entries=db.scalars(select(JournalEntry).where(JournalEntry.organization_id==actor.org.id).order_by(JournalEntry.id.desc())).all()
    out=[]
    for e in entries:
        lines=db.scalars(select(JournalLine).where(JournalLine.organization_id==actor.org.id,JournalLine.entry_id==e.id)).all()
        out.append({'id':e.id,'date':e.entry_date,'memo':e.memo,'posted':e.posted,'lines':[{'account_id':l.account_id,'debit':l.debit,'credit':l.credit} for l in lines]})
    return out

@router.post('/ledger/entries',status_code=201)
def create_journal(data:JournalIn,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    if sum(l.debit for l in data.lines)!=sum(l.credit for l in data.lines) or sum(l.debit for l in data.lines)==0:
        raise HTTPException(422,'Debits and credits must match and be positive.')
    for line in data.lines:
        if (line.debit==0)==(line.credit==0):raise HTTPException(422,'Each line must have only one positive side.')
        acc=db.scalar(select(LedgerAccount).where(LedgerAccount.id==line.account_id,LedgerAccount.organization_id==actor.org.id,LedgerAccount.active.is_(True)))
        if not acc:raise HTTPException(422,'Account not found or inactive.')
    period=db.scalar(select(FiscalPeriod).where(FiscalPeriod.organization_id==actor.org.id,FiscalPeriod.period==str(data.entry_date)[:7]))
    if period and period.locked:raise HTTPException(409,'Fiscal period is locked.')
    entry=JournalEntry(organization_id=actor.org.id,entry_date=str(data.entry_date),memo=data.memo,created_by=actor.user.id)
    db.add(entry);db.flush()
    for l in data.lines:db.add(JournalLine(organization_id=actor.org.id,entry_id=entry.id,account_id=l.account_id,debit=l.debit,credit=l.credit))
    log(db,actor,'ledger.draft',f'entry:{entry.id}');db.commit();return {'id':entry.id,'posted':False}

@router.post('/ledger/entries/{entry_id}/post')
def post_journal(entry_id:int,db:DB,actor:ActorDep):
    check(actor,'finance',True)
    entry=db.scalar(select(JournalEntry).where(JournalEntry.id==entry_id,JournalEntry.organization_id==actor.org.id))
    if not entry:raise HTTPException(404,'Entry not found.')
    if entry.posted:raise HTTPException(409,'Entry already posted.')
    period=db.scalar(select(FiscalPeriod).where(FiscalPeriod.organization_id==actor.org.id,FiscalPeriod.period==entry.entry_date[:7]))
    if period and period.locked:raise HTTPException(409,'Period locked.')
    lines=db.scalars(select(JournalLine).where(JournalLine.entry_id==entry.id,JournalLine.organization_id==actor.org.id)).all()
    if len(lines)<2 or not sum(x.debit for x in lines) or sum(x.debit for x in lines)!=sum(x.credit for x in lines):raise HTTPException(422,'Unbalanced entry.')
    entry.posted=True;log(db,actor,'ledger.post',f'entry:{entry_id}');db.commit();return {'posted':True}

class PeriodLock(BaseModel):
    period:str=Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    locked:bool

@router.put('/ledger/periods')
def fiscal_lock(data:PeriodLock,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin'):raise HTTPException(403,'Owner/admin only.')
    period=db.scalar(select(FiscalPeriod).where(FiscalPeriod.organization_id==actor.org.id,FiscalPeriod.period==data.period))
    if not period:
        period=FiscalPeriod(organization_id=actor.org.id,period=data.period)
        db.add(period)
    period.locked=data.locked;log(db,actor,'ledger.period_lock',data.period,{'locked':data.locked});db.commit()
    return {'period':data.period,'locked':data.locked}

@router.get('/ledger/reports/trial-balance')
def trial_balance(db:DB,actor:ActorDep):
    check(actor,'finance')
    accounts=db.scalars(select(LedgerAccount).where(LedgerAccount.organization_id==actor.org.id).order_by(LedgerAccount.code)).all()
    totals={a.id:{'id':a.id,'code':a.code,'name':a.name,'category':a.category,'debit':0,'credit':0,'balance':0} for a in accounts}
    lines=db.execute(select(JournalLine,JournalEntry).join(JournalEntry,JournalEntry.id==JournalLine.entry_id).where(JournalLine.organization_id==actor.org.id,JournalEntry.organization_id==actor.org.id,JournalEntry.posted.is_(True))).all()
    for line,entry in lines:
        if line.account_id in totals:
            totals[line.account_id]['debit']+=line.debit
            totals[line.account_id]['credit']+=line.credit
    for item in totals.values():item['balance']=item['debit']-item['credit']
    return {'currency':'IRR','accounts':list(totals.values()),'debits':sum(i['debit'] for i in totals.values()),'credits':sum(i['credit'] for i in totals.values()),'balanced':sum(i['balance'] for i in totals.values())==0,
      'profit_loss':sum((i['credit']-i['debit']) if i['category']=='revenue' else (i['debit']-i['credit'])*-1 if i['category']=='expense' else 0 for i in totals.values())}

class ApprovalRequest(BaseModel):
    title:str=Field(min_length=2,max_length=180)
    description:str=Field(default='',max_length=3000)

@router.get('/projects/{project_id}/approvals')
def project_approvals(project_id:int,db:DB,actor:ActorDep):
    project_access(db,actor,project_id)
    from .models_ext import ProjectApproval
    rows=db.scalars(select(ProjectApproval).where(ProjectApproval.organization_id==actor.org.id,ProjectApproval.project_id==project_id).order_by(ProjectApproval.id.desc())).all()
    return [{'id':r.id,'title':r.title,'description':r.description,'status':r.status,'requester_id':r.requester_id,'reviewer_id':r.reviewer_id} for r in rows]

@router.post('/projects/{project_id}/approvals',status_code=201)
def request_approval(project_id:int,data:ApprovalRequest,db:DB,actor:ActorDep):
    project_access(db,actor,project_id,True)
    from .models_ext import ProjectApproval
    obj=ProjectApproval(organization_id=actor.org.id,project_id=project_id,requester_id=actor.user.id,title=data.title,description=data.description)
    db.add(obj);db.flush();log(db,actor,'project.approval_requested',f'approval:{obj.id}')
    db.commit();return {'id':obj.id,'status':'pending'}

@router.post('/projects/{project_id}/approvals/{request_id}/decide')
def decide_approval(project_id:int,request_id:int,decision:Literal['approved','rejected'],db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Manager approval required.')
    project_access(db,actor,project_id,True)
    from .models_ext import ProjectApproval
    obj=db.scalar(select(ProjectApproval).where(ProjectApproval.id==request_id,ProjectApproval.organization_id==actor.org.id,ProjectApproval.project_id==project_id))
    if not obj:raise HTTPException(404,'Approval request not found.')
    if obj.status!='pending':raise HTTPException(409,'Request already decided.')
    from .models_ext import utc
    obj.status=decision;obj.reviewer_id=actor.user.id;obj.reviewed_at=utc()
    log(db,actor,'project.approval_decided',f'approval:{request_id}',{'decision':decision})
    db.commit();return {'id':obj.id,'status':decision}

class TeamAssign(BaseModel):
    team_id:int

@router.get('/projects/{project_id}/teams')
def project_teams(project_id:int,db:DB,actor:ActorDep):
    project_access(db,actor,project_id)
    from .models_ext import ProjectTeamAssignment
    rows=db.scalars(select(ProjectTeamAssignment).where(ProjectTeamAssignment.organization_id==actor.org.id,ProjectTeamAssignment.project_id==project_id)).all()
    result=[]
    for r in rows:
        team=db.scalar(select(Record).where(Record.id==r.team_id,Record.organization_id==actor.org.id,Record.kind=='team',Record.archived.is_(False)))
        if team:result.append({'team_id':team.id,'name':team.title})
    return result

@router.post('/projects/{project_id}/teams',status_code=201)
def add_project_team(project_id:int,data:TeamAssign,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Manager only.')
    project_access(db,actor,project_id,True)
    from .models_ext import ProjectTeamAssignment
    team=db.scalar(select(Record).where(Record.id==data.team_id,Record.kind=='team',Record.organization_id==actor.org.id,Record.archived.is_(False)))
    if not team:raise HTTPException(422,'Team must belong to the organization.')
    exists=db.scalar(select(ProjectTeamAssignment.id).where(ProjectTeamAssignment.organization_id==actor.org.id,ProjectTeamAssignment.project_id==project_id,ProjectTeamAssignment.team_id==data.team_id))
    if exists:raise HTTPException(409,'Team already linked.')
    db.add(ProjectTeamAssignment(organization_id=actor.org.id,project_id=project_id,team_id=team.id));log(db,actor,'project.team_add',f'project:{project_id}',{'team_id':team.id});db.commit()
    return {'ok':True}

@router.delete('/projects/{project_id}/teams/{team_id}',status_code=204)
def remove_project_team(project_id:int,team_id:int,db:DB,actor:ActorDep):
    if actor.role not in ('owner','admin','manager'):raise HTTPException(403,'Manager only.')
    project_access(db,actor,project_id,True)
    from .models_ext import ProjectTeamAssignment
    obj=db.scalar(select(ProjectTeamAssignment).where(ProjectTeamAssignment.organization_id==actor.org.id,ProjectTeamAssignment.project_id==project_id,ProjectTeamAssignment.team_id==team_id))
    if not obj:raise HTTPException(404,'Team is not linked.')
    db.delete(obj);db.commit();return Response(status_code=204)
