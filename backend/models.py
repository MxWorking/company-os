"""Persistence model definitions for Company OS."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    manager: Mapped[str] = mapped_column(String(100), default="")
    initials: Mapped[str] = mapped_column(String(12), default="")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="در حال اجرا")
    deadline: Mapped[str] = mapped_column(String(40), default="تعیین نشده")
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(32), default="#477af3")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    assignee: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(40), default="در انتظار")
    priority: Mapped[str] = mapped_column(String(40), default="متوسط")
    due_date: Mapped[str] = mapped_column(String(40), default="تعیین نشده")


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(200), default="")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    status: Mapped[str] = mapped_column(String(40), default="در انتظار")


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(60), default="عمومی")
    paid_at: Mapped[str] = mapped_column(String(40), default="")


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str] = mapped_column(String(200), default="")
    time: Mapped[str] = mapped_column(String(40), default="")
    icon: Mapped[str] = mapped_column(String(40), default="file")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ModuleItem(Base):
    __tablename__ = "module_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(40), default="جدید")
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Employee(Base):
    """Organization personnel directory. Sensitive payroll/identity documents belong in a separate secured subsystem."""
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personnel_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(90), nullable=False)
    last_name: Mapped[str] = mapped_column(String(90), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="کارمند")
    job_title: Mapped[str] = mapped_column(String(120), default="")
    department: Mapped[str] = mapped_column(String(120), default="")
    reporting_to_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(40), default="تمام‌وقت")
    employment_status: Mapped[str] = mapped_column(String(40), default="فعال")
    phone: Mapped[str] = mapped_column(String(32), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    work_location: Mapped[str] = mapped_column(String(120), default="")
    start_date: Mapped[str] = mapped_column(String(24), default="")
    end_date: Mapped[str] = mapped_column(String(24), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
