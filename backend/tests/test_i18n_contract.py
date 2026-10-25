"""UI localization and navigation source contracts (not a Next.js browser build)."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
UI=(ROOT/'frontend/components/CompanyOS.tsx').read_text(encoding='utf-8')
HR=(ROOT/'frontend/components/PersonnelWorkspace.tsx').read_text(encoding='utf-8')
STYLES=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
DICTIONARY=(ROOT/'frontend/lib/i18n.ts').read_text(encoding='utf-8')
API=(ROOT/'frontend/lib/api.ts').read_text(encoding='utf-8')


def test_shared_localization_layer_and_ltr():
    assert "document.documentElement.dir=rtl?'rtl':'ltr'" in UI
    assert 'localize(value,language)' in UI
    assert 'localNumber(v,language)' in UI
    assert 'localDate(language)' in UI
    assert 'function PersonnelWorkspace' in HR
    assert 'language' in HR and 'national_card_front' in HR
    assert 'function localize(' in DICTIONARY
    assert 'function localNumber(' in DICTIONARY
    assert 'data-theme' in STYLES


def test_guest_navigation_is_restricted_to_login_controls():
    guest=(ROOT/'frontend/components/SignInLanding.tsx').read_text(encoding='utf-8')
    assert 'className="landing-topbar guest-topbar"' in guest
    assert 'className="landing-top-enter"' in guest
    assert 'className="landing-language"' in guest
    assert 'setOpen(true)' in guest
    assert "login-gate-overlay" in guest
    assert '.guest-topbar' in STYLES


def test_english_assistant_api_is_language_aware():
    assert "assistant:(question:string,language:'fa'|'en'='fa')" in API
    assert "if payload.language=='en':" in (ROOT/'backend/main.py').read_text(encoding='utf-8')


def test_english_analytics_response():
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        response=client.post('/api/v1/assistant',json={'question':'project status','language':'en'})
        assert response.status_code==200,response.text
        text=response.json()['answer']
        assert 'projects' in text
        assert not any('\u0600'<=char<='\u06ff' for char in text)
        expense=client.post('/api/v1/assistant',json={'question':'expense analysis','language':'en'})
        assert expense.status_code==200
        assert 'IRR' in expense.json()['answer']
