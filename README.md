> **نسخه ۲.۶ (بازبینی):** بازطراحی هماهنگ زیرمنوهای حسابداری، فرم‌های داده مرجع، صندوق/بانک، گردش‌ها و خروجی CSV. راهنما: [`docs/COMPANY-OS-2.6-ACCOUNTING-UI-AND-TOOLS-FA.md`](docs/COMPANY-OS-2.6-ACCOUNTING-UI-AND-TOOLS-FA.md). به‌معنای تکمیل همه فرآیندهای مالی نیست.

# Company OS 2.5 | Accounting Operations Review

**تغییرات اصلی:** [راهنمای حسابداری عملیاتی ۲.۵](docs/COMPANY-OS-2.5-ACCOUNTING-OPERATIONS-FA.md). حفظ زیرساخت موجود؛ فروش/خرید با سند دوبل و اثر موجودی، دریافت و پرداخت، هزینه نقدی، چک پیگیری و همبرگری یکپارچه. **پایلوت، نه حسابداری قانونی آماده Production.**

# Company OS 2.4 | Aadin accounting navigation integration

**NEW:** [راهنمای تغییرات حسابداری ۲.۴](docs/COMPANY-OS-2.4-AADIN-DELIVERY-FA.md) | [نقشه عنوان‌های آدین](docs/research/aadin-menu-mapping.md)


## Company OS 2.3 (Review)

Self-registration and approval have been added. New accounts remain inactive until a manager approves a job title and assigns an access role. Standard staff can create private finance requests, while the accounting ledger remains restricted to the accountant and approved management roles.

See `docs/COMPANY-OS-2.3-DELIVERY-FA.md` for upgrade instructions, API list, security limitations and test status. This is not production-ready for public signup until anti-abuse controls, account recovery and operational security reviews are implemented.

> **Company OS v2.2.1:** برای نصب و رفع مشکل ورود با Docker ابتدا [docs/FIX-DOCKER-ENV-LOGIN-FA.md](docs/FIX-DOCKER-ENV-LOGIN-FA.md) را بخوانید. بخش‌های قدیمی README برای تاریخچه نسخه‌های اولیه نگهداری شده‌اند و دستورالعمل اصلی اجرای امن نسخهٔ ۲.۲.۱ نیستند.

# Company OS 2.2 Review

**New security & HR update:** Read [`docs/COMPANY-OS-2.2-DELIVERY-FA.md`](docs/COMPANY-OS-2.2-DELIVERY-FA.md) first. Version 2.2 requires configured administrator credentials before using the app. Guest scrolling does not unlock the workspace. HR documents require a separate encryption key. This archive is not yet production certified.

---

# Company OS 2.1 — Role-aware Workspace Review

> **NEW** Compact collapsible sidebar, personalized access, project chat/teams/calendar/approvals, private notes, encrypted identity vault, support tickets, and double-entry journal core. Review build; not production-ready. **Read [the full Persian delivery report](docs/COMPANY-OS-2.1-DELIVERY-FA.md).**
>
> No GitHub push or Vercel deployment was performed. Real HR data must not be uploaded in unverified deployments.

# Company OS 2.0 — Integration MVP (Review)

> **New in this release:** Eight organization-scoped operational modules and a permissioned `/api/v2` workspace alongside the preserved v1.3 UI. **Not production ready**. برای ویندوز: [آموزش فارسی اجرا](docs/QUICKSTART-FA.md). Start with [Implementation and limits](docs/COMPANY-OS-2.0-DELIVERY.md) and [Architecture blueprint](docs/ARCHITECTURE-2.0.md).

> **Version 1.3.0 review note:** UI strings, demo data display, HR management controls and rule-based AI responses are localized to Persian/English. Language switching never translates or edits arbitrary user-created records in the database; those remain as authored. The landing navbar is responsive with an icon compact mode and mobile menu. No production build was possible in this environment due to npm DNS restrictions. See `docs/I18N-QA.md` before approving publication.

# Company OS | سامانه جامع مدیریت سازمان

> **نسخه 1.2.0، بسته پیش‌نمایش برای تأیید کارفرما.** تا پیش از تأیید، این پروژه نباید Push یا Deploy شود.

این کد یک پیاده‌سازی قابل توسعه از ویترین ورود و داشبورد فارسی **Company OS** بر اساس اسکرین‌شات مرجع در `docs/reference-dashboard.png` است. نمای روشن و تاریک، RTL فارسی، EN/LTR، کارت‌های آماری، چارت‌ها، پروژه‌ها، وظایف، درخواست‌های تأیید، مالی، اسناد و دیگر ماژول‌ها را شامل می‌شود.

**محدودیت مهم:** تصویر مرجع فقط یک صفحه از محصول را نشان می‌دهد و اطلاعاتی از قواعد تجاری کامل، فرایند تأیید سازمان، سطوح دسترسی یا دیتابیس واقعی نمی‌دهد. داده‌های اولیه صرفاً Sample هستند. این نسخه یک محصول سازمانی تکمیل‌شده و ممیزی‌شده برای ورود داده حساس نیست. داشبورد و CRUD پایه کار می‌کنند؛ سایر ماژول‌ها فعلاً مدل رکورد عمومی دارند.

## ساختار

```text
company-os/
├── frontend/                   Next.js 16 + React 19 + TypeScript + Recharts
│   ├── app/                     App Router, RTL styling, SEO metadata
│   ├── components/CompanyOS.tsx UI و تعاملات
│   ├── lib/                     Demo data, types, API client
│   └── public/assets/           Optimized cinematic backgrounds + robot artwork
├── backend/                    Python 3.12+ / FastAPI / SQLAlchemy
│   ├── main.py                  API, session auth, CRUD
│   ├── models.py                SQLAlchemy tables
│   ├── schemas.py               Pydantic validation
│   ├── seed.py                  Development fixtures
│   └── tests/test_api.py        API integration tests
├── docs/reference-dashboard.png
├── docker-compose.yml          Local containerized development
└── vercel.json                 Vercel Services configuration (Beta)
```

## اجرای سریع: Docker

نیازمند Docker و Docker Compose؛ از پوشه ریشه:

```bash
docker compose up --build
```

Frontend: http://localhost:3000

FastAPI documentation: http://localhost:8000/docs

PostgreSQL locally persisted in named Docker volume. Container settings are **only for local development**.

## اجرای دستی ویندوز یا لینوکس

ترمینال اول، پوشه `backend/`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
# For local demo APP_ENV defaults to development, DEMO_MODE defaults to true.
uvicorn main:app --reload --port 8000
```

ترمینال دوم، پوشه `frontend/`:

```bash
npm install
npm run dev
```

رابط در http://localhost:3000 باز می‌شود. در توسعه، Next.js مسیر `/api/*` را به FastAPI در `http://127.0.0.1:8000` منتقل می‌کند. بعد از نصب وابستگی‌ها، ابزارها را بررسی کنید:

```bash
cd backend && python -m pytest -q
cd ../frontend && npm run typecheck && npm run build
```

اگر بک‌اند خاموش باشد، UI نمونه پیش‌نمایش داده را نشان می‌دهد اما نوشتن داده روی سرور **غیرفعال است**.

## تجربه ورود و مسیر کاربر (v1.2.1)

- **اصلاح 1.2.1:** در هر دو حالت Light و Dark، منو، آیکون‌های Lucide، سوییچ تم، انتخاب زبان و دکمه‌های Hero عناصر واقعی React/HTML هستند. باگ نسخه 1.2.0 که در دسکتاپِ تاریک رابط را مخفی و به‌جای آن یک تصویر رابط کامل با دکمه‌های نامرئی نشان می‌داد برطرف شد. تصویر صحنه نئونی `landing-cosmos.webp` فقط پس‌زمینه تزئینی Dark Mode است و نباید دکمه و متن رابط از عکس خوانده شوند.
- دکمه‌های «ورود به سامانه»، «مشاهده داشبورد» و فلش پایین صفحه، به بخش `#workspace` اسکرول می‌کنند و صفحه Dashboard / خانه مدیریت را نشان می‌دهند.
- اسکرول طبیعی کاربر به پایین نیز همان بخش را آشکار می‌کند؛ این یک صفحه پیوسته (single-page entrance + workspace) است، نه یک ریدایرکت یا مسیر مجزا.
- حالت روشن ویترین واقعاً زمینه روشن دارد و تصویر روشن مستقل خود را حفظ کرده است. برای زبان انگلیسی، دسکتاپ و موبایل نیز چیدمان زنده و واکنش‌گرا استفاده می‌شود. فایل PNG تولیدشده قبلی در `frontend/public/assets/landing-reference-dark.png` فقط برای مقایسه و بایگانی باقی مانده و به‌عنوان رابط کاربری رندر نمی‌شود.
- بنر کوچک داخل Dashboard اکنون **پس‌زمینه تصویر تمام‌عرض** دارد و تصویر مکعب جداگانه با گوشه‌های تیره حذف شده است.
- دستیار از Dashboard حذف و در منوی مستقل «دستیار هوشمند» قرار گرفته است؛ عکس ربات حذف و با **آیکون برداری نئون** جایگزین شده است. پاسخ‌ها همچنان آماری و قاعده‌محورند و مدل زبانی واقعی متصل نشده است.
- کاور ورود عمومی است و در حالت نیازمند ورود، احراز هویت فعلی FastAPI هنگام ورود به فضای مدیریت نمایش داده می‌شود. این موضوع جایگزین ممیزی امنیتی کامل Production نیست.

## قابلیت‌های رابط

- تم روشن و تاریک با نگهداری تنظیم در مرورگر.
- سایدبار متناسب با رفرنس و سازگار با موبایل، فارسی RTL و انگلیسی LTR.
- سرچ آنی پروژه‌ها و وظایف؛ میانبر Ctrl+K؛ اعلان‌ها؛ دیالوگ‌های ثبت و ویرایش.
- نمودارهای زنده Recharts، کارت‌های آماری، دسته‌بندی وضعیت پروژه‌ها، گزارش ۳ و ۶ ماهه.
- API واقعی برای پروژه‌ها، وظایف، تأییدها، پرونده‌های پرسنلی و CRUD ماژول‌های عمومی.
- **منابع انسانی اختصاصی:** ثبت/ویرایش/حذف/جستجو/فیلتر/جزئیات پرسنل، کد پرسنلی، نام و نام خانوادگی، نقش از رئیس هیئت‌مدیره تا کارگر و پیمانکار، عنوان شغلی، واحد، مدیر مستقیم، نوع و وضعیت همکاری، شماره تماس، ایمیل، محل کار، تاریخ‌های شروع/پایان و یادداشت. داده در جدول مستقل `employees` ذخیره می‌شود و تکرار کد پرسنلی و چرخه مدیریتی اعتبارسنجی می‌شوند. سایر ماژول‌ها (اسناد، خرید، دانش‌نامه و پشتیبانی) فعلاً CRUD عمومی دارند.
- صفحه اختصاصی دستیار **آماری و قاعده‌محور** متصل به داده‌های FastAPI؛ **مدل LLM واقعی هنوز متصل نشده است**. پاسخ‌های هوش مصنوعی مستقل تولید نمی‌کند.

## API

| Route | Methods | Purpose |
|---|---|---|
| `/health` | GET | Liveness |
| `/api/v1/auth/session` | GET | Session status |
| `/api/v1/auth/login` | POST | Admin sign-in |
| `/api/v1/auth/logout` | POST | Sign-out |
| `/api/v1/dashboard` | GET | Dashboard aggregation |
| `/api/v1/projects` | GET, POST | Project collection |
| `/api/v1/projects/{id}` | PATCH, DELETE | Project item |
| `/api/v1/tasks` | GET, POST | Task collection |
| `/api/v1/tasks/{id}` | PATCH, DELETE | Task item |
| `/api/v1/approvals` | GET, POST | Approval collection |
| `/api/v1/approvals/{id}` | PATCH | Approval item |
| `/api/v1/modules/{module}` | GET, POST | Supported generic modules |
| `/api/v1/modules/{module}/{id}` | PATCH, DELETE | Module item |
| `/api/v1/employees` | GET, POST | Personnel directory and registration |
| `/api/v1/employees/{id}` | PATCH, DELETE | Edit/delete individual personnel |
| `/api/v1/assistant` | POST | Deterministic data summary |

## امنیت و محیط Production

**قبل از ورود اطلاعات واقعی:**

1. در Vercel متغیرهای `APP_ENV=production`، `DEMO_MODE=false`، `DATABASE_URL=postgresql://...`، `ADMIN_USERNAME`، `ADMIN_PASSWORD`، `SESSION_SECRET` (حداقل ۳۲ کاراکتر تصادفی)، `ALLOWED_ORIGINS=https://YOUR_DOMAIN` را تنظیم کنید.
2. **SQLite روی فایل‌سیستم Vercel پایدار نیست.** PostgreSQL مدیریت‌شده (مثلاً Supabase/Neon) الزامی است.
3. در Production، برنامه از startup بدون PostgreSQL و Admin Secret معتبر خودداری می‌کند. Session cookie با `HttpOnly`، `SameSite=Lax` و `Secure` (برای production) تنظیم شده است؛ سرویس باید فقط روی HTTPS در دسترس باشد.
4. این نسخه ورود تک‌ادمینی دارد؛ **پرونده منابع انسانی به حساب کاربری/ورود اختصاصی هر کارمند وصل نیست.** Payroll، حضور و غیاب، ارزیابی عملکرد، اسناد هویتی و امور حقوق و دستمزد نیز هنوز پیاده‌سازی نشده‌اند. **RBAC، Audit trail کامل، مهاجرت دیتابیس (Alembic)، CSRF token اختصاصی، Rate limiting، بازیابی رمز عبور و SSO** هنوز باید پیش از استفاده سازمانی پیاده‌سازی/بررسی شوند.
5. تصاویر تزئینی از تصویر مرجع خود درخواست‌دهنده برش داده شده‌اند. فونت Vazirmatn از Google Fonts دریافت می‌شود و در صورت دسترسی‌نداشتن شبکه روی فونت‌های سیستم fallback دارد.

## انتشار در Vercel، فقط پس از تأیید ZIP

`vercel.json` از **Vercel Services** با `frontend/` (Next.js) و `backend/` (FastAPI) استفاده می‌کند. مستندات رسمی: [Services](https://vercel.com/docs/services)، [Next.js + FastAPI Starter](https://vercel.com/templates/fast-api/next-js-fastapi-starter).

این قابلیت در اکتبر ۲۰۲۶ در حالت Beta ارائه می‌شود و **فعال‌بودن آن برای اکانت مقصد و نتیجه Deployment هنوز تأیید نشده است**. قبل از انتشار، دسترسی و Build واقعی در حساب مقصد باید بررسی شود. در صورت عدم دسترسی، جایگزین عملی دو Vercel Project با Next.js frontend و Python FastAPI backend یا یک سرویس Python مستقل است.

در انتشار، مسیر `/api/:path*` به backend و سایر مسیرها به frontend Route می‌شوند. مقدارهای production در Variables Settings باید به پروژه اضافه شوند. **در این مرحله هیچ Push یا Deploy انجام نشده است.**

## وضعیت QA فعلی

آزمون‌های API با Pytest در محیط آماده‌سازی پاس شده‌اند. parse نحوی TypeScript/TSX انجام شده است. **به علت عدم دسترسی DNS به registry.npmjs.org در محیط آماده‌سازی، `npm install`، `next build`، TypeScript typecheck وابسته به پکیج‌ها و تست مرورگری خود Next.js هنوز اجرا نشده‌اند. پیش‌نمایش مستقل CSS با Chromium روی چهار حالت (روشن/تاریک × دسکتاپ/موبایل) و تست اسکرول انجام شده است؛ این معادل Build واقعی برنامه نیست.** اینها در `docs/QA.md` جزئیات دارند و قبل از اعلام Production-ready باید انجام شوند.

## تغییرات 1.2.0 و معیار پذیرش

- تصویر تاریک اکنون صحنه پس‌زمینهٔ برگرفته از همان طراحی نئونی است؛ برخلاف v1.2.0، کل رابط به‌صورت تصویر ثابت رندر نمی‌شود.
- تغییر تم از دکمه‌های ویترین و داشبورد، متغیر `data-theme` یکسان را تغییر می‌دهد. Light Mode ویترین پس‌زمینه و نوشته‌های خوانای مستقل دارد.
- صفحه دستیار آیکون ربات برداری دارد.
- ماژول پرسنل با FastAPI و جدول Employee مستقل است. در حالت Demo بدون API امکان مشاهده نمونه وجود دارد، اما عملیات ذخیره روی سرور نیازمند FastAPI فعال است.
- پیش از استفاده از پرونده‌های واقعی منابع انسانی، مجوزهای دسترسی ریزدانه، سیاست حفظ حریم خصوصی، رمزنگاری لازم، پشتیبان‌گیری و انطباق با مقررات مربوط باید اجرا و ارزیابی شوند.

## اصلاح Dark Mode در 1.2.1

- حل ناپدیدشدن المان‌های Hero تاریک در دسکتاپ: منوی واقعی React و دکمه‌های قابل‌کلیک جای Screenshot و hotspot را گرفتند.
- افزودن ناوبری واقعی با آیکون Lucide در هدر دسکتاپ، با حالت فشرده در لپ‌تاپ و چیدمان موبایل.
- تقویت روشنایی مکعب در موبایل Dark و جلوگیری از شکسته‌شدن عنوان انگلیسی Hero.
- نتایج کنترل‌های مستقل CSS در `docs/landing-v1.2.1-*.png` ثبت شده‌اند؛ این تصاویر خروجی Build کامپایل‌شده Next.js نیستند.
- همچنان **هیچ Push یا Deploy انجام نشده است** و قبل از Production باید `npm install && npm run build` و تست مرورگر روی Next.js واقعی اجرا شوند.
