# Company OS v1.3.0 | Localization and Navigation QA

## Updates

- Persian mode: RTL, Persian numbers and Solar Hijri date in the dashboard header.
- English mode: LTR, localized navigation, tables, settings, modal forms, notification UI, HR records, seeded sample text, chart month names, and English number / Gregorian date formatting for the header.
- FastAPI assistant now responds in English when the frontend sends `language: "en"`.
- UI labels are translations. User-authored free text remains as originally recorded: automatic translation of private employee names or arbitrary custom notes is not implemented.
- All backend database codes remain the same regardless of UI language.
- Landing navigation: desktop text tabs, compact icon tabs, mobile expandable nav with accessible button.

## Validation

- `cd backend && python -m pytest -q`: **18 tests passed**.
- TypeScript/TSX parser check for front-end files: passed.
- TypeScript standalone type check of `lib/i18n.ts`: passed.
- Browser CSS **navigation-only mockup**: inspected at 1672, 1366, 1024, 768, 390 px. No horizontal document overflow observed.

## Still not verified

- `npm install`, full Next.js `build`, real browser rendering and interaction of the React application (DNS resolution to npm registry failed).
- Pixel-level screenshot matching of the complete application or all UI workflows.
- Production deployment and production-security assessment.

No code has been pushed or deployed. Awaiting user approval.
