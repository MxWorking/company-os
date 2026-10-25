"""Tenant-scoped accounting preparation records.

These are NEVER posted invoices, receipts, stock movements or ledger entries.
Purpose: store non-sensitive drafts while the real accounting engine is developed.
"""
from datetime import datetime,timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Index
from sqlalchemy.orm import Mapped,mapped_column
from models import Base

def utc():return datetime.now(timezone.utc)

class AccountingDraft(Base):
    __tablename__='os_accounting_drafts'
    __table_args__=(Index('ix_aadin_drafts_tenant_kind','organization_id','kind','archived'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),nullable=False,index=True)
    created_by:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),nullable=False)
    kind:Mapped[str]=mapped_column(String(32),nullable=False)
    title:Mapped[str]=mapped_column(String(180),nullable=False)
    details:Mapped[dict]=mapped_column(JSON,default=dict,nullable=False)
    archived:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc,onupdate=utc)
