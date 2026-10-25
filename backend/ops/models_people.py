"""Organization-scoped employment profiles and configurable support directory.
Identity vault blobs remain in models_ext and never appear in these ordinary profiles.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models import Base


def now():
    return datetime.now(timezone.utc)


class Personnel(Base):
    __tablename__='os_personnel'
    __table_args__=(UniqueConstraint('organization_id','account_id'),UniqueConstraint('organization_id','personnel_code'))
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    personnel_code:Mapped[str]=mapped_column(String(32),nullable=False)
    job_title:Mapped[str]=mapped_column(String(120),default='')
    department:Mapped[str]=mapped_column(String(120),default='')
    employment_type:Mapped[str]=mapped_column(String(40),default='full_time')
    employment_status:Mapped[str]=mapped_column(String(40),default='active')
    hired_on:Mapped[str]=mapped_column(String(10),default='')
    work_email:Mapped[str]=mapped_column(String(254),default='')
    work_phone:Mapped[str]=mapped_column(String(32),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)


class SupportContact(Base):
    __tablename__='os_support_contacts'
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    audience:Mapped[str]=mapped_column(String(20),nullable=False) # company or developer
    kind:Mapped[str]=mapped_column(String(24),nullable=False) # telegram, whatsapp, instagram, eitaa, phone, email, web, etc
    label:Mapped[str]=mapped_column(String(100),nullable=False)
    value:Mapped[str]=mapped_column(String(400),nullable=False)
    active:Mapped[bool]=mapped_column(Boolean,default=True)

class IdentityDetails(Base):
    """Extended real-world identity form kept encrypted and out of normal roster/API JSON."""
    __tablename__='os_identity_details'
    __table_args__=(UniqueConstraint('organization_id','account_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    organization_id:Mapped[int]=mapped_column(ForeignKey('os_organizations.id'),index=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('os_accounts.id'),index=True)
    encrypted_blob:Mapped[bytes]=mapped_column(__import__('sqlalchemy').LargeBinary,nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
