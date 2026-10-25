"""Static guardrails for the entrance/assistant UI contract.

These checks do NOT replace a compiled Next.js browser test.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "frontend" / "components" / "CompanyOS.tsx"
ASSETS = ROOT / "frontend" / "public" / "assets"


def test_guest_landing_isolated_from_private_workspace():
    text=COMPONENT.read_text(encoding='utf-8')
    gate=(COMPONENT.parent/'SignInLanding.tsx').read_text(encoding='utf-8')
    assert "if(auth!=='authenticated'||!currentUser)return <SignInLanding" in text
    assert 'id="workspace"' in text
    assert 'onSuccess={handleSignIn}' in text
    assert 'setOpen(true)' in gate
    assert 'scrollIntoView' not in gate


def test_assistant_is_a_separate_navigation_module():
    text = COMPONENT.read_text(encoding="utf-8")
    assert "key:'assistant',fa:'دستیار هوشمند'" in text
    assert "section==='assistant'?<section className=\"ai-page\"" in text
    dashboard_fragment = text.split("section==='dashboard'&&", 1)[1].split("</>:section==='dashboard'&&currentUser?.role==='manager'", 1)[0]
    assert 'className="assistant-panel"' not in dashboard_fragment
    assert 'id="assistant-query"' not in dashboard_fragment


def test_optimized_cinematic_backgrounds_are_present():
    for name in ("landing-cosmos.webp", "dashboard-neon.webp"):
        blob = (ASSETS / name).read_bytes()
        assert blob[:4] == b"RIFF" and blob[8:12] == b"WEBP"
        assert len(blob) < 250_000


def test_original_generated_artwork_is_preserved_and_light_variant_exists():
    from hashlib import sha256
    dark = ASSETS / 'landing-reference-dark.png'
    light = ASSETS / 'landing-reference-light.webp'
    assert dark.read_bytes().startswith(b'\x89PNG')
    assert light.read_bytes()[:4] == b'RIFF'
    assert len(dark.read_bytes()) > 1_000_000
    assert len(light.read_bytes()) > 100_000


def test_personnel_is_merged_into_hr_and_has_identity_editor():
    component=COMPONENT.read_text(encoding='utf-8')
    personnel=(COMPONENT.parent/'PersonnelWorkspace.tsx').read_text(encoding='utf-8')
    assert "section==='hr-advanced'?<PersonnelWorkspace" in component
    assert "فهرست پرسنل قدیمی" not in component
    assert '/identity/${selected}' in personnel
    assert '/personnel' in personnel
    assert 'national_card_front' in personnel

def test_robot_uses_vector_emblem_not_photo():
    component = COMPONENT.read_text(encoding='utf-8')
    ai = component.split("section==='assistant'?",1)[1].split('section className="module-page"',1)[0]
    assert 'ai-robot-emblem' in ai
    assert 'ai-bot-image' not in ai
