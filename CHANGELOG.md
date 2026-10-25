## 2.6.0 (Review)

- یکپارچه‌سازی کامپوننت گروه‌های حسابداری با Design Tokens، منوی اصلی و RTL/LTR.
- اضافه‌شدن صفحه‌های عملیاتی یا داده مرجع برای دسته‌ها، واحدها، صندوق/بانک، رویدادها، آمار و تنظیمات.
- خروجی CSV فیلترشده چهارگانه، تبدیل عدد صحیح به حروف و راهنمای قدم بعدی هنگام خالی‌بودن داده.
- حفظ تمام داده‌ها و موتور قبلی؛ رکوردهای داده مرجع اثر قطعی مالی ندارند.
- هنوز Build کامل Next.js یا آزمون امنیتی Production تأیید نشده است.

# Changelog

## 2.5.0 (Accounting operations pilot and responsive navigation)

- Added organization-scoped parties, product/service catalog, multi-line invoice drafts, atomic posting to double-entry ledger with stock and weighted-average inventory value.
- Added partial settlements, paid expenses with posting, tracking-only cheques, cash/bank journal turnover, balances and dashboard summaries.
- Reused accounting taxonomy from Aadin report; connected supported pages to operational API. Other pages remain transparently unfinished.
- Reworked mobile hamburger in consistent Company OS dark/light glass/neon style, user card, close control, focus/scroll helpers, RTL and LTR.
- 52 backend tests passed; TypeScript syntax parsed, full build unverified due to npm registry DNS.
- Read docs/COMPANY-OS-2.5-ACCOUNTING-OPERATIONS-FA.md for limitations and upgrade guidance.

## 2.4.0 (Aadin report navigation integration)

- 5 main finance destinations, 18 groups, 67 named pages mapped from user-supplied Aadin report with FA/EN labels.
- Interactive in-module navigation, search, responsive layouts and theme colors.
- Tenant-scoped preparation-only drafts for 18 categories; no automated financial posting.
- Existing double-entry journal preserved; trial balance accessible.
- 3 new authorization and isolation test cases.
- Details in docs/COMPANY-OS-2.4-AADIN-DELIVERY-FA.md.


## v2.3.0 | Self-registration and accountant workflow (2026-10-12)

- Registration with a requested job title and organization code, pending activation, administrator approval/rejection, resubmission after rejection.
- Dedicated accountant role and finance-only restrictions enforced in FastAPI; regular staff can submit private finance requests and messages.
- Scoped managerial overview and role-filtered finance navigation.
- Added five new tests and updated regressions for the intentional change in finance permission policy.
- No deployment or GitHub changes made.

## 2.2.0 - 2026-10-12 (Authentication, personnel and support review)

- Replaced guest-scroll access with isolated login gate; workspace mounts only after v2 session validation.
- Removed standalone legacy HR menu entry; created unified personnel + encrypted identity interface.
- Added tenant-scoped personnel profiles and extra encrypted legal identity attributes.
- Added configurable tenant-scoped phone/social contacts with safe link schemes and role-guarded management.
- Added user role assignment within Account & Permissions; employee menu remains permission-filtered.
- Disabled predictable/default production authentication and v1 separate admin login.
- Retained staff task/project collaboration, private notes and basic assistant responses.
- Added authorization tests and secure-by-default Docker env contract.
- Reviewed deliverable only; no push/deployment.


## 2.2.1 - 2026-10-12 (Docker env / admin login hotfix)

- Added dedicated Docker environment preflight for administrator credentials and HR encryption key, with actionable errors and without printing secrets.
- Fixed administrator seeding so a change in ADMIN_USERNAME never silently creates another owner; existing passwords never change on restart.
- Added explicit, database-preserving administrator password/username reset command.
- Added backend healthcheck and made frontend wait until backend is healthy.
- Added regression tests for real non-demo login and password reset without clearing data.
- Added docs/FIX-DOCKER-ENV-LOGIN-FA.md for Windows and Docker Compose troubleshooting.

## 2.1.0 — 2026-10-12 (Role-based navigation and project operations review)

- Compact grouped responsive sidebar with per-account module permissions; removed duplicate legacy navigation roots.
- My Tasks nested in Tasks, Help/Knowledge consolidated, account and internal/developer support split.
- Workspace account profile, password change, per-user module permission overrides enforced by FastAPI.
- Project-specific chat, daily updates, invitations, multiple assigned teams, client linking, monthly calendar, private project notes and manager-reviewed change approvals.
- General company chat, personal account notes, internal/developer tickets (stored, not sent).
- Encryption-key-gated private identity store; national ID checksum; capped file upload. OTP deliberately unimplemented without provider.
- Ledger account codes, balanced double-entry draft/post journal, fiscal locks and trial balance (not a certified ERP).
- 32 Python tests pass. TypeScript syntax and CSS parse verified; full Next build unverified (npm unavailable).
- No push/deploy.

# Changelog

## 2.0.0-review — 2026-10-12

- Eight additive operational modules with typed records, organization-scoped v2 API, RBAC basics, multi-account login, membership and auditing.
- Advanced tasks with views, comments, checklists, guarded dependencies, optimistic lock, and My Work.
- Retains legacy v1.3 UI, bilingual theme, original assets, dashboards and employee directory.
- 25 backend tests passed, syntax-level TypeScript verification; Next.js build unverified due network DNS.
- Refer to `docs/COMPANY-OS-2.0-DELIVERY.md` for incomplete functionality, security gates, and deployment limitations.

## 1.3.0 - 2026-10-11 (Complete UI localization & navigation refinement)

- Centralized FA/EN interface localization in `frontend/lib/i18n.ts`, including statuses, seeded sample content, chart month names, system messages, form labels, HR detail views, and numeric/date formatting.
- English layout uses LTR reading direction while Persian remains RTL; employee record values and status codes persisted in the API are unchanged.
- Added English FastAPI deterministic-assistant responses using an optional `language` field, keeping compatibility with older clients.
- Landing navigation now uses a stable responsive grid; it shows full labels on wide screens, icon-only navigation at intermediate widths, and a labelled mobile navigation drawer on small screens.
- Added API/i18n/navigation regression tests and five viewport checks using a standalone CSS navigation probe (not a real Next.js rendering).
- Next.js build remains unverified because registry.npmjs.org DNS was inaccessible in this environment.
- No GitHub push or Vercel deployment pending user review.

## 1.2.1 - 2026-10-11 (Dark landing interactive UI repair)

- Fixed root cause: dark desktop landing no longer replaces the actual interface with a full-page raster screenshot and invisible click regions.
- Restored real, keyboard-accessible React buttons and Lucide icons for entry, mode switching, language, and section navigation in both themes.
- Used the previously prepared dark neon cube environment as a clean decorative backdrop; kept the existing light artwork and styling.
- Improved dark visual contrast, composition, and mobile cube brightness; fixed mobile branding from breaking across lines.
- Kept HR employee management, AI sidebar module, and FastAPI backend unchanged.
- Added source regression tests for landing structure; checked static CSS layout at 1672, 1366 and 390px in Chromium.
- All publication is explicitly deferred pending user approval.


## 1.2.0 - 2026-10-11 (Exact splash + light mode + HR)

- Dark landing uses the **exact previous generated image** as a full-screen visual. Interactive hit targets provide controls.
- Light landing uses a matching bright variant and live, readable HTML controls; mobile and English have responsive live layouts.
- Dedicated personnel CRUD with org-role taxonomy, departments, reporting manager, employment details and data integrity checks.
- Assistant hero robot photograph replaced with an SVG robot icon via Lucide, with neon effects.
- Added 4 CSS Chromium preview captures and extended tests. No GitHub push or Vercel deployment.

## 1.1.0 - 2026-10-11 (Full-screen entrance + separate AI module)

- Added a complete cinematic full-viewport welcome/entrance section above the workspace.
- Integrated optimized neon cube/environment into a 1920×1080 WebP background with real interactive CTA, language/theme controls, and scroll-to-workspace navigation.
- Converted the dashboard header into a full-bleed image hero, removing the small square illustration.
- Moved the AI assistant entirely off the dashboard into its own navigation item and dedicated chat page.
- Reworked recent activity cards to use the freed dashboard space.
- Included responsive RTL/LTR desktop/mobile treatment and motion-reduction support.
- No GitHub push or deployment: waiting for user approval.

## 1.0.2 - 2026-10-11 (Neon artwork cleanup candidate)

- Refined hero and assistant artwork rendering to reduce visible dark-corner framing.
- Added neon-glow presentation using blend, shadow and edge-fade masking tuned to the dark dashboard theme.
- Kept light theme artwork cleaner with softer masking and normal blend mode.
- Prepared updated ZIP for another user test before any GitHub push or Vercel deployment.

## 1.0.1 - 2026-10-11 (UI refinement candidate)

- Replaced CSS background-rendered hero and assistant artwork with `next/image` for cleaner sizing and runtime optimization.
- Refined hero artwork frame, glow, masking, and responsive widths to reduce overlap and distortion.
- Cleaned up assistant card composition, removed spacing hack (`margin-inline-start`), and aligned artwork/text more consistently.
- Tuned bottom dashboard grid proportions and responsive breakpoints to reduce visual clutter / empty-space imbalance.
- Prepared updated ZIP for user re-test before any GitHub push or Vercel deployment.

## 1.0.0 - 2026-10-11 (Review candidate)

- Next.js TypeScript responsive dashboard with FA/EN and light/dark themes.
- Custom design inspired by supplied screenshot (including cropped decorative assets).
- Recharts KPI, pie status, monthly finance chart, attention and activity panels.
- FastAPI + SQLAlchemy + validation + CRUD + SQLite / PostgreSQL support.
- Session-based administrator login for non-demo environments.
- Local Docker compose developer stack and Vercel Services beta configuration.
- Demo seed data and rule-based analytics assistant; no external AI API.
- API integration test coverage for core CRUD and validation.
- Publication held until the user approves the ZIP.
