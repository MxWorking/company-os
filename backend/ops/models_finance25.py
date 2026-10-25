"""Additive, organization-scoped transaction tables for the 2.5 accounting pilot.
All monetary values are integer IRR. Do not use for statutory filings.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models import Base

def utc():return datetime.now(timezone.utc)

class FinanceParty(Base):
    __tablename__='os_finance_parties'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    name:Mapped[str]=mapped_column(String(180))
    role:Mapped[str]=mapped_column(String(15),default='both')
    phone:Mapped[str]=mapped_column(String(40),default='')
    description:Mapped[str]=mapped_column(String(500),default='')
    active:Mapped[bool]=mapped_column(Boolean,default=True)

class FinanceItem(Base):
    __tablename__='os_finance_items'
    __table_args__=(UniqueConstraint('organization_id','sku'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    sku:Mapped[str]=mapped_column(String(64))
    name:Mapped[str]=mapped_column(String(180))
    kind:Mapped[str]=mapped_column(String(10),default='product')
    unit:Mapped[str]=mapped_column(String(32),default='عدد')
    sale_price:Mapped[int]=mapped_column(Integer,default=0)
    purchase_price:Mapped[int]=mapped_column(Integer,default=0)
    on_hand:Mapped[int]=mapped_column(Integer,default=0)
    avg_cost:Mapped[int]=mapped_column(Integer,default=0)
    stock_value:Mapped[int]=mapped_column(Integer,default=0)
    min_stock:Mapped[int]=mapped_column(Integer,default=0)
    active:Mapped[bool]=mapped_column(Boolean,default=True)

class FinanceDocument(Base):
    __tablename__='os_finance_documents'
    __table_args__=(UniqueConstraint('organization_id','request_key'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    request_key:Mapped[str]=mapped_column(String(80))
    kind:Mapped[str]=mapped_column(String(10))
    status:Mapped[str]=mapped_column(String(10),default='draft')
    party_id:Mapped[int]=mapped_column(ForeignKey('os_finance_parties.id'))
    entry_date:Mapped[str]=mapped_column(String(10))
    memo:Mapped[str]=mapped_column(String(350),default='')
    total:Mapped[int]=mapped_column(Integer,default=0)
    paid:Mapped[int]=mapped_column(Integer,default=0)
    ledger_entry_id:Mapped[int|None]=mapped_column(ForeignKey('os_journal_entries.id'),nullable=True)
    created_by:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class FinanceDocumentLine(Base):
    __tablename__='os_finance_document_lines'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    document_id:Mapped[int]=mapped_column(ForeignKey('os_finance_documents.id'),index=True)
    item_id:Mapped[int]=mapped_column(ForeignKey('os_finance_items.id'))
    quantity:Mapped[int]=mapped_column(Integer)
    price:Mapped[int]=mapped_column(Integer)
    discount:Mapped[int]=mapped_column(Integer,default=0)
    total:Mapped[int]=mapped_column(Integer)
    cost_at_post:Mapped[int]=mapped_column(Integer,default=0)

class FinanceStockMovement(Base):
    __tablename__='os_finance_stock_movements'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    item_id:Mapped[int]=mapped_column(ForeignKey('os_finance_items.id'),index=True)
    document_id:Mapped[int]=mapped_column(ForeignKey('os_finance_documents.id'),index=True)
    quantity:Mapped[int]=mapped_column(Integer)
    unit_cost:Mapped[int]=mapped_column(Integer)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class FinancePayment(Base):
    __tablename__='os_finance_payments'
    __table_args__=(UniqueConstraint('organization_id','request_key'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    request_key:Mapped[str]=mapped_column(String(80))
    document_id:Mapped[int]=mapped_column(ForeignKey('os_finance_documents.id'),index=True)
    amount:Mapped[int]=mapped_column(Integer)
    cash_account_id:Mapped[int]=mapped_column(ForeignKey('os_ledger_accounts.id'))
    journal_entry_id:Mapped[int]=mapped_column(ForeignKey('os_journal_entries.id'))
    entry_date:Mapped[str]=mapped_column(String(10))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class FinanceExpense(Base):
    __tablename__='os_finance_expenses'
    __table_args__=(UniqueConstraint('organization_id','request_key'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    request_key:Mapped[str]=mapped_column(String(80))
    title:Mapped[str]=mapped_column(String(180))
    category:Mapped[str]=mapped_column(String(80),default='other')
    amount:Mapped[int]=mapped_column(Integer)
    cash_account_id:Mapped[int]=mapped_column(ForeignKey('os_ledger_accounts.id'))
    entry_date:Mapped[str]=mapped_column(String(10))
    journal_entry_id:Mapped[int]=mapped_column(ForeignKey('os_journal_entries.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)

class FinanceCheque(Base):
    """Tracking only: no accounting effect until separate validated clearing workflow."""
    __tablename__='os_finance_cheques'
    __table_args__=(UniqueConstraint('organization_id','number','direction'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    direction:Mapped[str]=mapped_column(String(10))
    number:Mapped[str]=mapped_column(String(64))
    party_id:Mapped[int]=mapped_column(ForeignKey('os_finance_parties.id'))
    amount:Mapped[int]=mapped_column(Integer)
    due_date:Mapped[str]=mapped_column(String(10))
    status:Mapped[str]=mapped_column(String(16),default='pending')
    description:Mapped[str]=mapped_column(String(350),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc)
