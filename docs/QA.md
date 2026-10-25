# Company OS | QA and Reference Fidelity

## Completed in preparation environment (2026-10-11)

- [x] GitHub repo MxWorking/company-os checked read-only; default branch `main`; no code pushed.
- [x] Screenshot reference preserved (`reference-dashboard.png`).
- [x] Light and Dark theme structure implemented in CSS, including background / borders / typography / art / sidebar.
- [x] Pydantic validation and FastAPI CRUD integration tests: **3 passed** (`python -m pytest -q`).
- [x] All seven TypeScript/TSX files passed syntax parsing via `typescript.transpileModule`.
- [x] Backend source syntax verified via Python bytecode compilation.
- [x] Service split and routing based on published Vercel Services documentation.
- [x] 1.0.1 UI refinement applied: hero/assistant images moved to `next/image`, image framing cleaned up, and spacing/alignment improved in the lower dashboard area.
- [x] 1.0.2 neon artwork cleanup applied: dark-theme assets now use edge-fade masking + glow/blend treatment to visually suppress black corners and integrate with the neon UI.

## Not verified in preparation environment

- [ ] `npm install` / `npm run build` because registry.npmjs.org DNS resolution was unavailable.
- [ ] `npm run typecheck` with Next.js / React / Recharts declaration files installed.
- [ ] Browser-based visual comparison, pixel-level fidelity at 1440/1280/768/390 widths.
- [ ] Deployment to Vercel (explicitly deferred until user approval).
- [ ] Database migrations, RBAC, security and penetration checks for production.

## Suggested acceptance protocol before approval

1. Run `docker compose up --build` locally or start backend/frontend manually as README describes.
2. Compare screenshot at desktop and laptop widths for both Light and Dark themes. Test RTL/EN, sidebar, search Ctrl+K, charts, new project, edit project, task actions, notifications, mobile menu.
3. Run `python -m pytest -q` and `npm run typecheck && npm run build`.
4. Verify data persists across FastAPI restarts (Postgres or local SQLite volume), no credentials in source, and session login in production configuration.
5. Confirm source & ZIP quality, then **separately authorize GitHub push and Vercel deploy**.

## Pixel accuracy statement

Layout aims to follow the supplied reference closely but **pixel-perfect visual equivalence is NOT yet established**, since a rendered screenshot could not be captured in this environment. Reference shows one dashboard image, not module-specific pages or business specifications. Non-dashboard pages are functional starter implementations inspired by that visual system, not claimed to be exact unseen pages.

## 1.1.0 acceptance notes (2026-10-11)

- [x] Full-screen entrance and new dark neon background authored.
- [x] Dashboard hero converted from small framed illustration to full-bleed background image.
- [x] Assistant removed from dashboard and placed in its own navigation/page.
- [x] Landing and dashboard kept on one scrollable page; CTA selects Dashboard and scrolls to `#workspace`.
- [x] WebP background dimensions: 1920×1080; file size approximately 110 KB each.
- [x] All 7 TypeScript/TSX source files passed parse check with global TypeScript.
- [x] CSS parser validation performed (0 errors).
- [x] Backend and static frontend contracts: **6 pytest tests passed**.
- [x] CSS-only browser layout probe at 1440×900 and 390×844; CTA scrolled exactly one viewport to `#workspace`. Screenshots are in `docs/landing-css-probe-*.png`. This is NOT a compiled Next.js app test.
- [ ] React/Next integration build and browser screenshot **not verified** because npm registry DNS resolution fails (`EAI_AGAIN`).
- [ ] Exact pixel-level comparison and backend-connected AI UI must be retested locally after `npm install`.
- [ ] No publication has occurred.

### 1.1.0 testing steps

1. Run the backend and frontend as documented in README.
2. On initial load, verify the immersive 100svh welcome image and no sidebar until scrolling.
3. Test CTA and manual scrolling into Dashboard, including on mobile.
4. Verify dark/light mode, FA/EN, and the dedicated «دستیار هوشمند» navigation item.
5. Check that the dashboard no longer contains the assistant card and the hero backdrop has no square/corner framing.
6. Test FastAPI-backed chat replies and authentication after entering the dashboard.
7. Run `npm run typecheck && npm run build` before approving a release.

## 1.2.0 verification and known limitations

- [x] Original generated dark splash PNG included byte-for-byte (`landing-reference-dark.png`).
- [x] Separate light visual asset generated from the same source composition; real light-mode live content/controls added.
- [x] Independent CSS Chromium screenshots at 1672×941 and 390×844 in both modes (`landing-v1.2-*.png`).
- [x] Dark-mode reference at native resolution visually matches the prior generated artwork.
- [x] In independent browser CSS probe, primary CTA scrolled to `#workspace` at 941 px on 941 px viewport.
- [x] Personnel CRUD, duplicate code conflicts, hierarchy integrity/cycle protection, authentication gating tested with pytest.
- [x] Source TS/TSX syntax parsed via global TypeScript.
- [ ] **Not a compiled Next.js visual QA run**; npm registry DNS is unavailable (`EAI_AGAIN`) so `npm install`, `npm run typecheck` and `npm run build` could not execute.
- [ ] RBAC, identity-linked employee accounts, secure handling of high-sensitivity HR fields, attendance, payroll, auditing, and schema migrations remain outside the implemented scope.
- [ ] No push/deployment until explicit user approval.

## 1.2.1 dark landing correction (2026-10-11)

- **Root cause identified:** v1.2.0 at dark desktop breakpoints explicitly hid `.landing-topbar`, `.landing-inner`, and `.landing-scroll`, showing a flattened `landing-reference-dark.png` with transparent hotspot buttons instead.
- **Fix:** dark and light now share a single set of real header/navigation/buttons/icons, and only their backgrounds and color tokens change. Dark uses `landing-cosmos.webp`, an environment derived from the neon scene rather than a screenshot of the interface.
- Verified that the dark desktop DOM has actual visible theme buttons, language buttons, and navigation. Transparent hotspots have been removed from the component.
- Independent HTML/CSS Playwright visual probe (NOT a compiled Next.js app) at 1672×941, 1366×768 and 390×844: theme toggles to light; CTA scrolls by one viewport height; no horizontal overflow observed.
- Evidence images: `docs/landing-v1.2.1-{dark,light}-{1672,1366,390}.png`.
- Remaining limitation: Next.js dependencies cannot be installed in this environment due to `EAI_AGAIN` from registry.npmjs.org, so a true built-application visual regression and `next build` remain unverified.
- GitHub push and Vercel deploy deferred until user approval.
