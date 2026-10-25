"""Source-level regression guards against the flattened dark landing bug.

These do not replace a built Next.js browser integration test.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = (ROOT / 'frontend/components/CompanyOS.tsx').read_text(encoding='utf-8')
STYLES = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')


def test_guest_landing_has_live_controls_and_login_form():
    guest=(ROOT/'frontend/components/SignInLanding.tsx').read_text(encoding='utf-8')
    assert 'className="landing guest-landing"' in guest
    assert 'landing-hotspots' not in guest
    assert 'landing-reference-scene' not in guest
    assert 'className="landing-theme-button"' in guest
    assert 'className="landing-primary"' in guest
    assert 'onClick={()=>setTheme(theme===' in guest
    assert 'register?submitRegistration(e):submit(e)' in guest
    assert ':root[data-theme=\'dark\'] .landing:not(.landing-live)' not in STYLES


def test_landing_art_uses_clean_background_not_screenshot_controls():
    assert "url('/assets/landing-cosmos.webp')" in STYLES
    assert "url('/assets/landing-reference-light.webp')" in STYLES
    assert ".landing-scene:after" in STYLES
    assert ".landing-nav-link.active" in STYLES
    assert "landing-reference-dark.png');background-size:100% 100%" not in STYLES


def test_landing_requires_authentication_before_workspace():
    guest=(ROOT/'frontend/components/SignInLanding.tsx').read_text(encoding='utf-8')
    assert "if(auth!=='authenticated'||!currentUser)return <SignInLanding" in COMPONENT
    assert "opsAPI.login(username.trim(),password)" in guest
    assert "const user=await opsAPI.me()" in guest
    assert "onSuccess(user)" in guest
    assert 'id="workspace"' in COMPONENT
    assert 'id="assistant-query"' in COMPONENT
    assert "section==='hr-advanced'?<PersonnelWorkspace" in COMPONENT
