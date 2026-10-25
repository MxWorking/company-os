"""Additive Organization OS 2.1 tables. No legacy data is rewritten.

Encrypted identity data is intentionally isolated from generic JSON record payloads.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models import Base


def utc():return datetime.now(timezone.utc)

class ModuleGrant(Base):
    __tablename__='os_module_grants'
    __table_args__=(UniqueConstraint('organization_id','account_id','module'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    module:Mapped[str]=mapped_column(String(40))
    can_read:Mapped[bool]=mapped_column(Boolean,default=True)
    can_write:Mapped[bool]=mapped_column(Boolean,default=False)

class ProjectMember(Base):
    __tablename__='os_project_members'
    __table_args__=(UniqueConstraint('organization_id','project_id','account_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    project_id:Mapped[int]=mapped_column(ForeignKey('os_records.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    project_role:Mapped[str]=mapped_column(String(30),default='contributor')

class ProjectMessage(Base):
    __tablename__='os_project_messages'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    project_id:Mapped[int|None]=mapped_column(ForeignKey('os_records.id'),nullable=True,index=True)
    author_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))
    category:Mapped[str]=mapped_column(String(22),default='chat') # chat,daily,change,decision,announcement
    body:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class ProjectEvent(Base):
    __tablename__='os_project_events'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    project_id:Mapped[int]=mapped_column(ForeignKey('os_records.id'),index=True)
    title:Mapped[str]=mapped_column(String(180))
    event_type:Mapped[str]=mapped_column(String(30),default='milestone')
    starts_on:Mapped[str]=mapped_column(String(10))
    ends_on:Mapped[str|None]=mapped_column(String(10),nullable=True)
    description:Mapped[str]=mapped_column(Text,default='')
    created_by:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))

class PrivateNote(Base):
    __tablename__='os_private_notes'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    owner_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    project_id:Mapped[int|None]=mapped_column(ForeignKey('os_records.id'),nullable=True,index=True)
    title:Mapped[str]=mapped_column(String(180))
    body:Mapped[str]=mapped_column(Text,default='')
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc,onupdate=utc)

class SupportTicket(Base):
    __tablename__='os_support_tickets'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    author_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))
    audience:Mapped[str]=mapped_column(String(20)) # internal/developer
    title:Mapped[str]=mapped_column(String(180))
    message:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(20),default='open')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class IdentityProfile(Base):
    __tablename__='os_identity_profiles'
    __table_args__=(UniqueConstraint('organization_id','account_id'),UniqueConstraint('organization_id','national_id_hmac'))
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    national_id_cipher:Mapped[bytes|None]=mapped_column(LargeBinary,nullable=True)
    national_id_hmac:Mapped[str|None]=mapped_column(String(64),nullable=True)
    phone_cipher:Mapped[bytes|None]=mapped_column(LargeBinary,nullable=True)
    phone_verified:Mapped[bool]=mapped_column(Boolean,default=False)

class IdentityDocument(Base):
    __tablename__='os_identity_documents'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    kind:Mapped[str]=mapped_column(String(24))
    mime_type:Mapped[str]=mapped_column(String(50))
    original_name:Mapped[str]=mapped_column(String(180))
    encrypted_bytes:Mapped[bytes]=mapped_column(LargeBinary)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class LedgerAccount(Base):
    __tablename__='os_ledger_accounts'
    __table_args__=(UniqueConstraint('organization_id','code'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    code:Mapped[str]=mapped_column(String(24))
    name:Mapped[str]=mapped_column(String(180))
    category:Mapped[str]=mapped_column(String(20))
    active:Mapped[bool]=mapped_column(Boolean,default=True)

class FiscalPeriod(Base):
    __tablename__='os_fiscal_periods'
    __table_args__=(UniqueConstraint('organization_id','period'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    period:Mapped[str]=mapped_column(String(7)) # YYYY-MM
    locked:Mapped[bool]=mapped_column(Boolean,default=False)

class JournalEntry(Base):
    __tablename__='os_journal_entries'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    entry_date:Mapped[str]=mapped_column(String(10))
    memo:Mapped[str]=mapped_column(String(350))
    posted:Mapped[bool]=mapped_column(Boolean,default=False)
    created_by:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class JournalLine(Base):
    __tablename__='os_journal_lines'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    entry_id:Mapped[int]=mapped_column(ForeignKey('os_journal_entries.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_ledger_accounts.id'))
    debit:Mapped[int]=mapped_column(Integer,default=0)
    credit:Mapped[int]=mapped_column(Integer,default=0)

class ProjectApproval(Base):
    __tablename__='os_project_approvals'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    project_id:Mapped[int]=mapped_column(ForeignKey('os_records.id'),index=True)
    requester_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))
    title:Mapped[str]=mapped_column(String(180))
    description:Mapped[str]=mapped_column(Text,default='')
    status:Mapped[str]=mapped_column(String(20),default='pending')
    reviewer_id:Mapped[int|None]=mapped_column(ForeignKey('os_accounts.id'),nullable=True)
    reviewed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)

class ProjectTeamAssignment(Base):
    __tablename__='os_project_teams'
    __table_args__=(UniqueConstraint('organization_id','project_id','team_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    project_id:Mapped[int]=mapped_column(ForeignKey('os_records.id'),index=True)
    team_id:Mapped[int]=mapped_column(ForeignKey('os_records.id'),index=True)
