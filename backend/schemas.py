"""Public API request schemas; validation is on the backend, not only in the UI."""
from pydantic import BaseModel, ConfigDict, Field


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    manager: str = Field(default="", max_length=100)
    progress: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="در حال اجرا", max_length=40)
    deadline: str = Field(default="تعیین نشده", max_length=40)
    description: str = Field(default="", max_length=5000)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    manager: str | None = Field(default=None, max_length=100)
    progress: int | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, max_length=40)
    deadline: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=5000)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    project_id: int | None = None
    assignee: str = Field(default="", max_length=100)
    status: str = Field(default="در انتظار", max_length=40)
    priority: str = Field(default="متوسط", max_length=40)
    due_date: str = Field(default="تعیین نشده", max_length=40)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    project_id: int | None = None
    assignee: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=40)
    due_date: str | None = Field(default=None, max_length=40)


class ApprovalIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    subtitle: str = Field(default="", max_length=200)
    severity: str = Field(default="medium", max_length=16)
    status: str = Field(default="در انتظار", max_length=40)


class ApprovalPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    subtitle: str | None = Field(default=None, max_length=200)
    severity: str | None = Field(default=None, max_length=16)
    status: str | None = Field(default=None, max_length=40)


class ModuleItemIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    subtitle: str = Field(default="", max_length=200)
    status: str = Field(default="جدید", max_length=40)
    amount: int | None = Field(default=None, ge=0)


class LoginIn(BaseModel):
    username: str
    password: str


class AssistantIn(BaseModel):
    question: str = Field(min_length=1, max_length=1200)
    language: str = Field(default='fa', pattern='^(fa|en)$')


from typing import Literal

PersonnelRole = Literal['رئیس هیئت‌مدیره','مدیرعامل','مدیر ارشد','مدیر','سرپرست','کارمند','کارگر','پیمانکار','کارآموز']
EmploymentType = Literal['تمام‌وقت','پاره‌وقت','قراردادی','پروژه‌ای','کارآموزی']
EmploymentStatus = Literal['فعال','مرخصی','غیرفعال','خاتمه همکاری']

class EmployeeIn(BaseModel):
    personnel_code: str = Field(min_length=1, max_length=32)
    first_name: str = Field(min_length=1, max_length=90)
    last_name: str = Field(min_length=1, max_length=90)
    role: PersonnelRole = 'کارمند'
    job_title: str = Field(default='', max_length=120)
    department: str = Field(default='', max_length=120)
    reporting_to_id: int | None = Field(default=None, ge=1)
    employment_type: EmploymentType = 'تمام‌وقت'
    employment_status: EmploymentStatus = 'فعال'
    phone: str = Field(default='', max_length=32)
    email: str = Field(default='', max_length=254)
    work_location: str = Field(default='', max_length=120)
    start_date: str = Field(default='', max_length=24)
    end_date: str = Field(default='', max_length=24)
    notes: str = Field(default='', max_length=3000)

class EmployeePatch(EmployeeIn):
    pass
