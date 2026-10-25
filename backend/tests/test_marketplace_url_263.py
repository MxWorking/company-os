"""Check that Supabase Marketplace's supa metadata can be removed safely."""
from sqlalchemy.engine import make_url


def test_supabase_marketplace_connection_metadata():
    original=make_url('postgresql+psycopg://tester:secret@db.example.com:6543/app?sslmode=require&supa=integration-info&connect_timeout=8')
    sanitized=original.difference_update_query(['supa'])
    assert 'supa' not in sanitized.query
    assert sanitized.query['sslmode']=='require'
    assert sanitized.query['connect_timeout']=='8'
    assert sanitized.host==original.host and sanitized.password==original.password
