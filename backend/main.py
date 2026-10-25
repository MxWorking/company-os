"""Company OS REST API. Session-protected outside local demo mode."""
from contextlib import asynccontextmanager
import hmac
import os
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, init_database
from models import Project, Task, Approval, Expense, Activity, ModuleItem, Employee
from schemas import ProjectIn, ProjectPatch, TaskIn, TaskPatch, ApprovalIn, ApprovalPatch, ModuleItemIn, LoginIn, AssistantIn, EmployeeIn, EmployeePatch
from seed import seed_if_empty
from ops.router import router as v2_router, seed_workspace
from ops.bootstrap import validate_bootstrap_env
from ops.secret_manager import subkey
from ops.router_ext import router as ext_router
from ops.router_people import router as people_router
from ops.router_identity_details import router as identity_details_router
from ops import models_ext, models_people, models_registration, models_accounting_drafts, models_finance25  # register additive tables
from ops.router_registration import router as registration_router
from ops.router_accounting_drafts import router as accounting_drafts_router
from ops.router_finance25 import router as accounting_operations_router

APP_ENV=os.environ.get('APP_ENV','production' if os.environ.get('VERCEL_ENV') in ('production','preview') else 'development').lower()
DEMO_MODE=APP_ENV=='test' and os.environ.get('DEMO_MODE','false').lower()=='true' and 'pytest' in __import__('sys').modules
COOKIE_SIGNING_SECRET=subkey('cookie-session-v1').hex()
ADMIN_USERNAME=os.environ.get('ADMIN_USERNAME','admin')
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','')
ALLOWED_ORIGINS=[x.strip() for x in os.environ.get('ALLOWED_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(',') if x.strip()]

@asynccontextmanager
async def lifespan(app:FastAPI):
    if not DEMO_MODE:
        validate_bootstrap_env()
    init_database()
    with SessionLocal() as db:
        seed_workspace(db)
        if DEMO_MODE:
            seed_if_empty(db)
    yield

app=FastAPI(title='Company OS API',version='2.5.0-review',lifespan=lifespan,docs_url='/docs' if APP_ENV!='production' else None)
app.add_middleware(SessionMiddleware,secret_key=COOKIE_SIGNING_SECRET,session_cookie='company_os_session',https_only=APP_ENV=='production' or os.environ.get('VERCEL_ENV') in ('preview','production'),same_site='lax',max_age=60*60*8)
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Content-Type'])
DB=Annotated[Session,Depends(get_db)]

def require_auth(request:Request,db:DB):
    # Legacy v1 endpoints are unscoped. Do NOT expose them to v2 member/viewer
    # sessions or to members of a different tenant while migration is incomplete.
    v2_id=request.session.get('v2_account_id')
    if isinstance(v2_id,int):
        from ops.models import Membership,Organization
        org=db.scalar(select(Organization).where(Organization.slug=='company-os'))
        member=db.scalar(select(Membership).where(Membership.organization_id==org.id,Membership.account_id==v2_id)) if org else None
        if member and member.role in ('owner','admin') and request.session.get('v2_org_id',org.id)==org.id:
            if not DEMO_MODE and request.method in {'POST','PUT','PATCH','DELETE'}:
                csrf=request.session.get('v2_csrf')
                if not csrf or not hmac.compare_digest(str(csrf),request.headers.get('x-company-csrf','')):
                    raise HTTPException(403,'CSRF token missing or invalid.')
            return True
        raise HTTPException(403,'Legacy workspace requires the primary organization administrator.')
    if DEMO_MODE:
        return True  # isolated local pytest fixture only; never active in development/production
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Sign in to access the organization.')

Auth=Annotated[bool,Depends(require_auth)]

def as_dict(obj):
    return {column.key:getattr(obj,column.key) for column in obj.__table__.columns if column.key!='created_at'}

def locate(db:Session,cls,pk:int):
    record=db.get(cls,pk)
    if record is None:
        raise HTTPException(404,'مورد موردنظر پیدا نشد.')
    return record

def update_record(db:Session,obj,data:dict):
    for key,value in data.items():
        setattr(obj,key,value)
    db.commit();db.refresh(obj)
    return as_dict(obj)

def audit(db:Session,title:str,detail:str='توسط مدیر سازمان'):
    from datetime import datetime
    db.add(Activity(title=title,detail=detail,time=datetime.now().strftime('%H:%M'),icon='file'))

@app.get('/health')
def health():
    return {'status':'ok','service':'Company OS FastAPI','environment':APP_ENV}

@app.get('/api/v1/auth/session')
def session_status(request:Request):
    return {'authenticated': isinstance(request.session.get('v2_account_id'),int) or DEMO_MODE,'demo':DEMO_MODE}

@app.post('/api/v1/auth/login')
def deprecated_login():
    raise HTTPException(410,'Use /api/v2/auth/login. Legacy admin login is disabled.')

@app.post('/api/v1/auth/logout')
def logout(request:Request):
    request.session.clear()
    return {'ok':True}

@app.get('/api/v1/dashboard')
def dashboard(db:DB,_:Auth):
    projects=db.scalars(select(Project).order_by(Project.id)).all()
    tasks=db.scalars(select(Task).order_by(Task.id)).all()
    approvals=db.scalars(select(Approval).where(Approval.status=='در انتظار').order_by(Approval.id)).all()
    expenses=db.scalars(select(Expense).order_by(Expense.id)).all()
    activities=db.scalars(select(Activity).order_by(Activity.id.desc()).limit(4)).all()
    statuses=[{'label':name,'count':sum(1 for p in projects if p.status==name),'color':color} for name,color in [('در حال اجرا','#2889ff'),('تکمیل شده','#28d8c0'),('متوقف شده','#ffa128'),('با ریسک','#ff666d')]]
    statuses[3]['count']=sum(1 for p in projects if 'ریسک' in p.status)
    return {'stats':{'projects':len(projects),'tasks':len(tasks),'approvals':len(approvals),'expenses':sum(x.amount for x in expenses),'project_change':'+۱۲٪','task_change':'+۵٪','approval_change':'-۳٪','expense_change':'+۱۸٪',
      'statuses':statuses,'trend':[dict(month=month,income=income,expense=cost,profit=profit) for month,income,cost,profit in [('فروردین',35,25,38),('اردیبهشت',42,30,45),('خرداد',54,43,58),('تیر',39,44,47),('مرداد',40,36,43),('شهریور',65,57,65)]]},
     'projects':[as_dict(p) for p in projects[:4]],'tasks':[as_dict(x) for x in tasks[:15]],'approvals':[as_dict(a) for a in approvals[:12]],'expenses':[as_dict(x) for x in expenses],'activities':[as_dict(x) for x in activities]}

@app.get('/api/v1/projects')
def get_projects(db:DB,_:Auth):
    return [as_dict(x) for x in db.scalars(select(Project).order_by(Project.id)).all()]

@app.post('/api/v1/projects',status_code=201)
def post_project(data:ProjectIn,db:DB,_:Auth):
    project=Project(**data.model_dump(),initials=''.join(x[:1] for x in data.manager.split()[:2]) or 'OS')
    db.add(project);audit(db,'پروژه جدید ثبت شد');db.commit();db.refresh(project)
    return as_dict(project)

@app.patch('/api/v1/projects/{id}')
def patch_project(id:int,data:ProjectPatch,db:DB,_:Auth):
    return update_record(db,locate(db,Project,id),data.model_dump(exclude_unset=True))

@app.delete('/api/v1/projects/{id}',status_code=204)
def delete_project(id:int,db:DB,_:Auth):
    p=locate(db,Project,id)
    for t in db.scalars(select(Task).where(Task.project_id==id)).all():t.project_id=None
    db.delete(p);db.commit()
    return Response(status_code=204)

@app.get('/api/v1/tasks')
def get_tasks(db:DB,_:Auth):
    return [as_dict(x) for x in db.scalars(select(Task).order_by(Task.id)).all()]

@app.post('/api/v1/tasks',status_code=201)
def post_task(data:TaskIn,db:DB,_:Auth):
    if data.project_id is not None:locate(db,Project,data.project_id)
    record=Task(**data.model_dump());db.add(record);audit(db,'وظیفه جدید ثبت شد');db.commit();db.refresh(record)
    return as_dict(record)

@app.patch('/api/v1/tasks/{id}')
def patch_task(id:int,data:TaskPatch,db:DB,_:Auth):
    updates=data.model_dump(exclude_unset=True)
    if 'project_id' in updates and updates['project_id'] is not None:locate(db,Project,updates['project_id'])
    return update_record(db,locate(db,Task,id),updates)

@app.delete('/api/v1/tasks/{id}',status_code=204)
def delete_task(id:int,db:DB,_:Auth):
    db.delete(locate(db,Task,id));db.commit()
    return Response(status_code=204)

@app.get('/api/v1/approvals')
def get_approvals(db:DB,_:Auth):
    return [as_dict(x) for x in db.scalars(select(Approval).order_by(Approval.id.desc())).all()]

@app.post('/api/v1/approvals',status_code=201)
def post_approval(data:ApprovalIn,db:DB,_:Auth):
    record=Approval(**data.model_dump());db.add(record);db.commit();db.refresh(record)
    return as_dict(record)

@app.patch('/api/v1/approvals/{id}')
def patch_approval(id:int,data:ApprovalPatch,db:DB,_:Auth):
    return update_record(db,locate(db,Approval,id),data.model_dump(exclude_unset=True))

ALLOWED_MODULES={'documents','finance','procurement','hr','knowledge','settings','support'}
def check_module(module:str):
    if module not in ALLOWED_MODULES:raise HTTPException(404,'ماژول پیدا نشد.')

@app.get('/api/v1/modules/{module}')
def get_modules(module:str,db:DB,_:Auth):
    check_module(module)
    return [as_dict(x) for x in db.scalars(select(ModuleItem).where(ModuleItem.module==module).order_by(ModuleItem.id.desc())).all()]

@app.post('/api/v1/modules/{module}',status_code=201)
def post_module(module:str,data:ModuleItemIn,db:DB,_:Auth):
    check_module(module)
    item=ModuleItem(module=module,**data.model_dump());db.add(item);audit(db,'رکورد جدید ثبت شد');db.commit();db.refresh(item)
    return as_dict(item)

@app.patch('/api/v1/modules/{module}/{id}')
def patch_module(module:str,id:int,data:ModuleItemIn,db:DB,_:Auth):
    check_module(module);item=locate(db,ModuleItem,id)
    if item.module!=module:raise HTTPException(404,'مورد پیدا نشد.')
    return update_record(db,item,data.model_dump())

@app.delete('/api/v1/modules/{module}/{id}',status_code=204)
def delete_module(module:str,id:int,db:DB,_:Auth):
    check_module(module);item=locate(db,ModuleItem,id)
    if item.module!=module:raise HTTPException(404,'مورد پیدا نشد.')
    db.delete(item);db.commit();return Response(status_code=204)

@app.get('/api/v1/employees')
def list_employees(db:DB,_:Auth):
    return [as_dict(e) for e in db.scalars(select(Employee).order_by(Employee.id)).all()]


def validate_employee_relation(db:Session, supervisor:int|None, employee_id:int|None=None):
    if supervisor is None:
        return
    if supervisor == employee_id:
        raise HTTPException(422,'هر شخص نمی‌تواند مدیر مستقیم خودش باشد.')
    locate(db,Employee,supervisor)
    # Guard against reporting-chain cycles, even with nested supervisors.
    visited={employee_id} if employee_id is not None else set()
    current=supervisor
    while current is not None:
        if current in visited:
            raise HTTPException(422,'چرخه مدیریتی در ساختار سازمان مجاز نیست.')
        visited.add(current)
        record=db.get(Employee,current)
        current=record.reporting_to_id if record else None


@app.post('/api/v1/employees',status_code=201)
def create_employee(data:EmployeeIn,db:DB,_:Auth):
    from sqlalchemy.exc import IntegrityError
    validate_employee_relation(db,data.reporting_to_id)
    obj=Employee(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'کد پرسنلی قبلاً ثبت شده است.')
    db.refresh(obj)
    return as_dict(obj)


@app.patch('/api/v1/employees/{id}')
def update_employee(id:int,data:EmployeePatch,db:DB,_:Auth):
    from sqlalchemy.exc import IntegrityError
    obj=locate(db,Employee,id)
    validate_employee_relation(db,data.reporting_to_id,id)
    for field,value in data.model_dump().items():
        setattr(obj,field,value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'کد پرسنلی قبلاً ثبت شده است.')
    db.refresh(obj)
    return as_dict(obj)


@app.delete('/api/v1/employees/{id}',status_code=204)
def remove_employee(id:int,db:DB,_:Auth):
    obj=locate(db,Employee,id)
    for direct_report in db.scalars(select(Employee).where(Employee.reporting_to_id==id)).all():
        direct_report.reporting_to_id=None
    db.delete(obj)
    db.commit()
    return Response(status_code=204)


@app.post('/api/v1/assistant')
def assistant(payload:AssistantIn,db:DB,_:Auth):
    """Clearly-labeled deterministic analytics, NOT an LLM integration."""
    text=payload.question
    count_projects=db.scalar(select(func.count()).select_from(Project)) or 0
    count_tasks=db.scalar(select(func.count()).select_from(Task)) or 0
    total=db.scalar(select(func.sum(Expense.amount))) or 0
    pending=db.scalar(select(func.count()).select_from(Approval).where(Approval.status=='در انتظار')) or 0
    if payload.language=='en':
        q=text.lower()
        if any(w in q for w in ('expense','cost','finance','budget')):
            reply=f'Total recorded expenses are {total:,} IRR. Open Finance to see the details.'
        elif any(w in q for w in ('task','to-do','todo')):
            reply=f'There are {count_tasks} tasks in the database. Open Tasks to manage them.'
        elif any(w in q for w in ('approval','pending','request')):
            reply=f'{pending} approval requests are pending review.'
        else:
            reply=f'Current overview: {count_projects} projects, {count_tasks} tasks, and {pending} pending approvals. This is a rule-based response, not an LLM.'
        return {'answer':reply,'mode':'rules-based-demo'}
    if any(w in text for w in ['هزینه','مالی','بودجه']):
        reply=f'جمع هزینه‌های ثبت‌شده {total:,} ریال است. برای بررسی جزئیات به بخش مالی بروید.'
    elif any(w in text for w in ['وظیفه','تسک','کارها']):
        reply=f'{count_tasks} وظیفه در پایگاه داده ثبت شده است. برای مدیریت آن‌ها بخش وظایف را باز کنید.'
    elif any(w in text for w in ['تأیید','درخواست']):
        reply=f'{pending} درخواست تأیید در انتظار بررسی وجود دارد.'
    else:
        reply=f'وضعیت فعلی: {count_projects} پروژه، {count_tasks} وظیفه و {pending} درخواست تأیید باز. این پاسخ با تحلیل ساده داده‌های داخلی تولید شده و به مدل زبانی متصل نیست.'
    return {'answer':reply,'mode':'rules-based-demo'}


# Additive multi-module workspace (legacy /api/v1 remains available during migration).
app.include_router(v2_router)
app.include_router(ext_router)
app.include_router(people_router)
app.include_router(identity_details_router)
app.include_router(registration_router)
app.include_router(accounting_drafts_router)
app.include_router(accounting_operations_router)
