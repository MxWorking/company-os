"""Backend-owned catalog: a purposeful validated schema for each domain entity."""
from typing import Any

# Supported editable fields: short strings, date-ISO strings, integer amounts, booleans, entity references.
# This is an MVP catalog; specialized business rules and regulatory features need dedicated modules.
CATALOG={
 'department':('organization',{'code':'text','manager':'text','description':'long'}),
 'team':('organization',{'department':'text','lead':'text','description':'long'}),
 'position':('organization',{'department':'text','level':'text','description':'long'}),
 'project':('work',{'owner':'text','customer':'ref','start_date':'date','due_date':'date','progress':'percent','budget':'money','description':'long'}),
 'board':('work',{'project':'ref','view':'select:kanban,table,timeline','description':'long'}),
 'task':('work',{'project':'ref','board':'ref','assignee':'text','assignee_id':'number','priority':'select:low,medium,high,urgent','due_date':'date','estimate_hours':'decimal','description':'long'}),
 'contract':('hr',{'employee_code':'text','type':'select:full_time,part_time,contractor','start_date':'date','end_date':'date','description':'long'}),
 'leave':('hr',{'employee_code':'text','from_date':'date','to_date':'date','reason':'long'}),
 'asset':('hr',{'employee_code':'text','serial':'text','issued_on':'date','description':'long'}),
 'channel':('collaboration',{'description':'long','visibility':'select:team,organization'}),
 'message':('collaboration',{'channel':'ref','body':'long','reply_to':'ref'}),
 'meeting':('collaboration',{'starts_at':'datetime','meeting_url':'url','participants':'text','minutes':'long','description':'long'}),
 'document':('documents',{'code':'text','category':'select:general,contract,policy,technical','revision':'number','url':'text','description':'long'}),
 'letter':('documents',{'serial':'text','direction':'select:inbound,outbound,internal','recipient':'text','body':'long','due_date':'date'}),
 'referral':('documents',{'letter':'ref','to':'text','note':'long','due_date':'date'}),
 'customer':('crm',{'company':'text','email':'email','phone':'text','city':'text','description':'long'}),
 'contact':('crm',{'customer':'ref','email':'email','phone':'text','position':'text'}),
 'lead':('crm',{'customer':'ref','source':'text','owner':'text','expected_value':'money','description':'long'}),
 'opportunity':('crm',{'customer':'ref','stage':'select:lead,qualified,proposal,won,lost','value':'money','owner':'text','description':'long'}),
 'invoice':('finance',{'customer':'ref','project':'ref','amount':'money','currency':'select:IRR,USD,EUR','due_date':'date','description':'long'}),
 'payment':('finance',{'invoice':'ref','amount':'money','currency':'select:IRR,USD,EUR','paid_at':'date','description':'long'}),
 'cost':('finance',{'project':'ref','category':'text','amount':'money','currency':'select:IRR,USD,EUR','spent_at':'date','description':'long'}),
 'worklog':('finance',{'task':'ref','worker':'text','minutes':'number','work_date':'date','description':'long'}),
 'report':('intelligence',{'metric':'select:projects,tasks,finance,hr,crm','range':'select:week,month,quarter,year','description':'long'}),
 'automation':('intelligence',{'trigger':'select:task_created,task_completed,invoice_overdue,lead_created','action':'select:notify,create_task','description':'long','enabled':'boolean'}),
}
MODULES={
 'organization':['department','team','position'],
 'work':['project','board','task'],
 'hr':['contract','leave','asset'],
 'collaboration':['channel','message','meeting'],
 'documents':['document','letter','referral'],
 'crm':['customer','contact','lead','opportunity'],
 'finance':['invoice','payment','cost','worklog'],
 'intelligence':['report','automation'],
}
STATUSES=['new','planned','open','in_progress','in_review','blocked','approved','rejected','done','archived']


def checked_payload(kind:str, payload:dict[str,Any])->dict:
    from fastapi import HTTPException
    schema=CATALOG[kind][1]
    unknown=set(payload)-set(schema)
    if unknown:
        raise HTTPException(422,f'Unsupported fields for {kind}: {sorted(unknown)}')
    cleaned={}
    for field,val in payload.items():
        type_=schema[field]
        if type_=='boolean':
            if not isinstance(val,bool):raise HTTPException(422,f'{field}: expected boolean')
        elif type_ in {'money','decimal','number','percent'}:
            if type(val) not in {int,float}:raise HTTPException(422,f'{field}: expected number')
            if type_ in ('money','number','percent') and (type(val) is not int): raise HTTPException(422,f'{field}: expected integer')
            if type_=='money' and (val<0 or val>10**13):raise HTTPException(422,f'{field}: out of range')
            if type_=='percent' and not 0<=val<=100:raise HTTPException(422,f'{field}: out of range')
            if type_=='number' and not 0<=val<=10**7:raise HTTPException(422,f'{field}: out of range')
        else:
            if not isinstance(val,str) or len(val)>2000:raise HTTPException(422,f'{field}: invalid string')
            if type_.startswith('select:') and val not in type_.split(':',1)[1].split(','):raise HTTPException(422,f'{field}: invalid option')
            if type_=='url' and val:
                from urllib.parse import urlparse
                url=urlparse(val)
                if url.scheme not in ('https','http') or not url.hostname:raise HTTPException(422,f'{field}: expected a valid http(s) URL')
            if type_=='email' and val and ('@' not in val or len(val)>254):raise HTTPException(422,f'{field}: invalid email')
            if type_=='date' and val:
                from datetime import date
                try: date.fromisoformat(val)
                except ValueError:raise HTTPException(422,f'{field}: expected ISO 8601 date')
            if type_=='datetime' and val:
                from datetime import datetime
                try: datetime.fromisoformat(val.replace('Z','+00:00'))
                except ValueError:raise HTTPException(422,f'{field}: expected ISO 8601 date-time')
        cleaned[field]=val
    return cleaned
