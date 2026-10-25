"""Explicit one-time admin credential reset; does NOT erase the database.

Run with: docker compose run --rm backend python -m ops.reset_admin --apply
For an owner username change add: --rename-to-configured
"""
import argparse
import os
from sqlalchemy import select
from .bootstrap import BootstrapConfigError, validate_bootstrap_env
from .models import Organization, Account, Membership
from .router import make_hash
from database import SessionLocal


def reset_admin(*, username: str | None = None, rename_to_configured: bool = False) -> str:
    validate_bootstrap_env()
    with SessionLocal() as db:
        org = db.scalar(select(Organization).where(Organization.slug == 'company-os'))
        if org is None:
            raise BootstrapConfigError('No company-os organization exists. Start backend normally once to create the initial owner.')
        owners = db.scalars(select(Account).join(Membership, Membership.account_id == Account.id).where(
            Membership.organization_id == org.id, Membership.role == 'owner'
        )).all()
        if username:
            owners = [account for account in owners if account.username == username]
        if len(owners) != 1:
            raise BootstrapConfigError('Cannot unambiguously identify one organization owner. Supply --username EXISTING_OWNER_USERNAME.')
        owner = owners[0]
        new_username = os.environ['ADMIN_USERNAME'].strip()
        if rename_to_configured and owner.username != new_username:
            if db.scalar(select(Account.id).where(Account.username == new_username)):
                raise BootstrapConfigError('ADMIN_USERNAME already belongs to another account. Choose an unused name; no changes were made.')
            owner.username = new_username
        owner.password_hash = make_hash(os.environ['ADMIN_PASSWORD'])
        db.commit()
        return owner.username


def main() -> int:
    parser = argparse.ArgumentParser(description='Explicitly reset the existing organization owner using ADMIN_PASSWORD from Docker .env')
    parser.add_argument('--apply', action='store_true', help='Required confirmation; writes a new password hash to the database')
    parser.add_argument('--username', help='Existing owner username if multiple owner accounts exist')
    parser.add_argument('--rename-to-configured', action='store_true', help='Also rename the existing owner to ADMIN_USERNAME from .env')
    args = parser.parse_args()
    if not args.apply:
        parser.error('No changes made. Pass --apply to explicitly reset the existing owner password.')
    try:
        username = reset_admin(username=args.username, rename_to_configured=args.rename_to_configured)
    except (BootstrapConfigError, ValueError) as exc:
        print('[Company OS] Admin reset refused: '+str(exc))
        return 2
    print('[Company OS] Owner credentials updated for username: '+username+'. Database records were preserved. Restart backend and sign in.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
