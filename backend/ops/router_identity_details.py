"""Encrypted, per-tenant optional identity information. Does not establish authenticity."""
from typing import Annotated
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from .router import actor_dep, Actor, log
from .router_ext import identity_target,seal,unseal,crypto
from .models_people import IdentityDetails

router=APIRouter(prefix='/api/v2',tags=['Protected identity'])
DB=Annotated[Session,Depends(get_db)]
ActorDep=Annotated[Actor,Depends(actor_dep)]

class LegalIdentity(BaseModel):
    first_name:str=Field(default='',max_length=90)
    last_name:str=Field(default='',max_length=90)
    father_name:str=Field(default='',max_length=90)
    birth_date:str=Field(default='',max_length=10)
    birth_place:str=Field(default='',max_length=120)
    certificate_number:str=Field(default='',max_length=32)
    certificate_serial:str=Field(default='',max_length=32)
    issue_place:str=Field(default='',max_length=120)
    postal_code:str=Field(default='',max_length=10)
    address:str=Field(default='',max_length=500)

@router.get('/identity/{account_id}/details')
def read_details(account_id:int,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    row=db.scalar(select(IdentityDetails).where(IdentityDetails.organization_id==actor.org.id,IdentityDetails.account_id==account_id))
    if not row:return {'exists':False,'data':{}}
    crypto()
    result=json.loads(unseal(row.encrypted_blob,f'identity-details:{actor.org.id}:{account_id}'.encode()))
    log(db,actor,'identity.details_read',f'account:{account_id}');db.commit()
    return {'exists':True,'data':result}

@router.put('/identity/{account_id}/details')
def write_details(account_id:int,info:LegalIdentity,db:DB,actor:ActorDep):
    identity_target(db,actor,account_id)
    crypto()  # fail closed
    row=db.scalar(select(IdentityDetails).where(IdentityDetails.organization_id==actor.org.id,IdentityDetails.account_id==account_id))
    if not row:
        row=IdentityDetails(organization_id=actor.org.id,account_id=account_id,encrypted_blob=b'')
        db.add(row)
    row.encrypted_blob=seal(json.dumps(info.model_dump(),ensure_ascii=False).encode('utf-8'),f'identity-details:{actor.org.id}:{account_id}'.encode())
    log(db,actor,'identity.details_updated',f'account:{account_id}');db.commit()
    return {'ok':True,'encrypted':True,'identity_verified':False}
