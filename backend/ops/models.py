"""Company OS 2.0 additive domain tables. Legacy v1 tables remain intact."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from models import Base


def now():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = 'os_organizations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Account(Base):
    __tablename__ = 'os_accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Membership(Base):
    __tablename__ = 'os_memberships'
    __table_args__ = (UniqueConstraint('organization_id','account_id',name='uq_os_membership_org_account'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('os_accounts.id'),nullable=False,index=True)
    role: Mapped[str] = mapped_column(String(24),nullable=False,default='member')


class Record(Base):
    """Flexible, organization-scoped MVP entity; catalog validates its kind and payload."""
    __tablename__ = 'os_records'
    __table_args__ = (Index('ix_os_records_org_kind_status','organization_id','kind','status'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    kind: Mapped[str] = mapped_column(String(40),nullable=False,index=True)
    title: Mapped[str] = mapped_column(String(200),nullable=False)
    status: Mapped[str] = mapped_column(String(40),nullable=False,default='new')
    payload: Mapped[dict] = mapped_column(JSON,default=dict,nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('os_accounts.id'),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    version: Mapped[int] = mapped_column(Integer,default=1,nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean,default=False)


class RecordLink(Base):
    __tablename__ = 'os_record_links'
    __table_args__ = (UniqueConstraint('organization_id','from_id','to_id','relation',name='uq_os_link'),)
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    from_id: Mapped[int] = mapped_column(ForeignKey('os_records.id'),nullable=False)
    to_id: Mapped[int] = mapped_column(ForeignKey('os_records.id'),nullable=False)
    relation: Mapped[str] = mapped_column(String(40),nullable=False,default='related')


class Note(Base):
    __tablename__ = 'os_notes'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey('os_records.id'),nullable=False,index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('os_accounts.id'),nullable=False)
    body: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class Checklist(Base):
    __tablename__ = 'os_checklist_items'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('os_records.id'),nullable=False,index=True)
    title: Mapped[str] = mapped_column(String(160),nullable=False)
    done: Mapped[bool] = mapped_column(Boolean,default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('os_accounts.id'),nullable=False)


class AuditEvent(Base):
    __tablename__ = 'os_audit_events'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('os_accounts.id'),nullable=False)
    action: Mapped[str] = mapped_column(String(90),nullable=False)
    target: Mapped[str] = mapped_column(String(130),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
    detail: Mapped[dict] = mapped_column(JSON,default=dict)
