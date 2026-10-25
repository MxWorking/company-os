"""Self-service registration and finance requests, additive to v2.2 database."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models import Base


def now():return datetime.now(timezone.utc)

class JoinApplication(Base):
    __tablename__='os_join_applications'
    __table_args__=(UniqueConstraint('account_id',name='uq_os_join_account'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True,nullable=False)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True,nullable=False)
    requested_job_title:Mapped[str]=mapped_column(String(120),nullable=False)
    approved_job_title:Mapped[str|None]=mapped_column(String(120),nullable=True)
    department:Mapped[str]=mapped_column(String(120),default='')
    status:Mapped[str]=mapped_column(String(16),default='pending',index=True)
    assigned_role:Mapped[str|None]=mapped_column(String(24),nullable=True)
    reviewer_id:Mapped[int|None]=mapped_column(ForeignKey('os_accounts.id'),nullable=True)
    reviewed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    review_reason:Mapped[str|None]=mapped_column(String(500),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class FinanceRequest(Base):
    __tablename__='os_finance_requests'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True,nullable=False)
    requester_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),nullable=False,index=True)
    subject:Mapped[str]=mapped_column(String(180),nullable=False)
    description:Mapped[str]=mapped_column(Text,nullable=False)
    status:Mapped[str]=mapped_column(String(20),default='open',index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)

class FinanceRequestMessage(Base):
    __tablename__='os_finance_request_messages'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True,nullable=False)
    request_id:Mapped[int]=mapped_column(ForeignKey('os_finance_requests.id'),index=True,nullable=False)
    author_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
