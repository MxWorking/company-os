# COMPANY OS 2.0 — Master Architecture & Delivery Blueprint

**وضعیت:** Design Proposal / Awaiting Explicit User Approval  
**تاریخ:** ۲۰ مهر ۱۴۰۵ / ۱۲ اکتبر ۲۰۲۶  
**مبنای سورس:** `Company-OS-NextJS-FastAPI-Review-v1.3.0.zip` (بازرسی ایستا؛ بدون تغییر)  
**منابع محصول:** اسناد عمومی رسمی میزیتو و تسکولو نسخه ۳؛ فضای خصوصی `office.mizito.ir` و `mrhossein.taskulu.app` به‌صورت کامل قابل مشاهده نبود.  
**قانون انتشار:** هیچ تغییری در سورس، GitHub یا Vercel بدون تأیید جداگانه اجرا نمی‌شود.

## 1. چشم‌انداز، محدوده و اصول

محصول مطلوب: سیستم مدیریت یکپارچه سازمانی با امکانات الهام‌گرفته از ارتباطات/مکاتبات/CRM میزیتو و سازمان/پروژه/صفحه/لیست/کار و نماهای چندگانه تسکولو، با هویت بصری مستقل Company OS. **بازطراحی تجربه کاربری** به‌جای کپی HTML، تصاویر تجاری، لوگوها و دارایی‌های دارای حق نشر رقبا.

انتخاب‌های بنیادی پیشنهادی:

- Frontend: Next.js App Router، TypeScript، React، Design System با توکن‌های تم (Light/Dark)، Bilingual `fa-IR` / `en-US`، RTL/LTR صحیح.
- Backend: Python 3.12+، FastAPI و Pydantic، SQLAlchemy، ساختار Modular Monolith (یک برنامه و پایگاه داده اصلی با مرز دامنه‌ای روشن).
- Persistence: PostgreSQL + Alembic migrations؛ Redis/Queue فقط هنگامی که نیاز پردازش پس‌زمینه یا Real-time به مرحله اجرایی برسد.
- Storage: ذخیره‌سازی شیء با دسترسی خصوصی و لینک امضاشده برای پیوست‌ها؛ عدم اتکا به فایل‌سیستم موقت میزبان.
- Isolation: `organization_id` در تمام رکوردهای کسب‌وکاری و Scope مجوز در query/service. برای تقویت جداسازی در صورت نیاز RLS؛ RLS جایگزین آزمون مجوز اپلیکیشن نیست.
- Deployment: Vercel برای Frontend؛ Backend FastAPI روی گزینه‌ای که پس از آزمون اکانت و Runtime انتخاب می‌شود. Vercel Services در مستندات فعلی *Private Beta / request access* و نمونه کلید رسمی `experimentalServices` دارد؛ فایل کنونی پروژه کلید دیگری به نام `services` دارد و نیازمند بررسی/اصلاح در مرحله اجراست. گزینه جایگزین: Backend Python پایدار و مستقل.
- Chat Real-time: گزینه کم‌ریسک، خدمات Pub/Sub یا سرویس Python با WebSocket و Redis؛ اعلامیه 22 June 2026 از Public Beta WebSocket در Vercel برای Node.js سخن می‌گوید، اما حمایت یکسان از Python FastAPI تأیید نشده است.
- AI: لایه Provider Adapter برای API یا مدل محلی و عملیات مبتنی بر ابزار؛ دستیار فعلی LLM نیست، پاسخ آماری Rule-Based می‌دهد. اشتراک مصرف‌کننده به معنی اعتبار API یا اجازه دسترسی مستقل نیست.

### محدوده مصوب برای **طراحی و برنامه‌ریزی** (نه مجوز اجرا)

1. زیرساخت سازمانی و دسترسی‌ها
2. پروژه‌ها و کارهای من
3. منابع انسانی پیشرفته
4. ارتباطات و همکاری
5. اسناد و مکاتبات
6. مشتریان و فروش
7. مالی و زمان‌های کاری
8. گزارش‌ها و اتوماسیون AI

## 2. بررسی مبتنی بر فایل v1.3.0 (Source-based)

- `frontend/components/CompanyOS.tsx` رابط اصلی یکپارچه و چندبخشی است؛ `HRDirectory.tsx` جدا شده است.
- `frontend/lib/i18n.ts` ترجمه‌ی اولیه دارد، اما ارزیابی نهایی تمامی مسیرهای EN و FA نیازمند اجرای واقعی برنامه است.
- `backend/main.py` اکثر APIها، Session تک‌ادمینی و منطق Rule-based Assistant را در یک فایل نگه می‌دارد.
- `backend/models.py` مدل‌های `Project`, `Task`, `Approval`, `Expense`, `Activity`, `ModuleItem`, `Employee` را دارد. `ModuleItem` سند/خرید/دانش‌نامه را به‌شکل رکورد عمومی نگه می‌دارد.
- `Project.manager`, `Task.assignee`, `Employee.department`, `Project.deadline`, `Task.due_date` رشته‌اند، نه روابط خارجی/نوع تاریخ استاندارد؛ برای همکاری، زمان‌بندی و گزارش‌های معتبر باید با migration تدریجی اصلاح شوند.
- جدول `Employee` ثبت پرونده و اعتبارسنجی مدیر مستقیم را دارد، اما به شناسه حساب کاربری، شرکت و ساختار سازمانی چندسطحی متصل نیست.
- `DB init_database()` از `metadata.create_all` استفاده می‌کند؛ کنترل نسخه تغییرات Schema با Alembic هنوز نیازمند اجراست.
- `APP_ENV=development` ممکن است Demo فعال باشد. **هر داده واقعی منابع انسانی/مالی مستلزم احراز هویت چندکاربری، deny-by-default، audit و نگهداری ایمن است.**
- `vercel.json` موجود مطابق کلید رسمی نمونه فعلی Services (`experimentalServices`) نیست. پیش از هر Deployment کنترل شود.
- ZIP نهایی قبلی Typecheck/Build واقعی Next.js را در محیط آماده‌سازی پاس نکرده بود؛ اجرای کامل در CI پیش‌نیاز هر انتشار است.

## 3. مرزبندی دامنه و پروژه پیشنهادی

```text
company-os/
  apps/
    web/                        # Next.js App Router
      app/[locale]/(marketing)/ # Landing مستقل، CTA ورود و صفحه معرفی
      app/[locale]/(auth)/      # Login / reset / invitations
      app/[locale]/(workspace)/ # Dashboard / modules
      components/ui/            # Reusable primitives
      components/shell/         # Sidebar, Nav, Breadcrumb, Command Menu
      features/{...}/           # Domain UIs, tables, dialogs, hooks
      lib/{api,i18n,permissions}/
    api/                        # FastAPI Modular Monolith
      app/main.py
      app/core/{config,security,db,logging}/
      app/modules/
        identity/
        organizations/
        projects/
        work/
        hr/
        collaboration/
        documents/
        crm/
        finance/
        analytics/
        automation/
        assistant/
      app/common/{events,storage,exceptions}/
      migrations/               # Alembic versioned scripts
      tests/{unit,integration,security,contract}/
  packages/
    ui-tokens/                  # Cross-theme design tokens
    api-contract/               # OpenAPI generated TypeScript client
  infrastructure/
    docker/
    deployment/
    ci/
  docs/{architecture,adr,api,security,ux,qa}/
```

ساختار بالا **مقصد پیشنهادی Refactor** است؛ فایل یا دایرکتوری جدید هنوز ساخته نشده است. در اجرای پروژه Migration باید به‌صورت Incremental انجام شود و APIهای موجود تا زمان مهاجرت سازگار بمانند.

## 4. معماری سازمان و مجوزها (Foundation / Module 1)

### موجودیت‌ها
`organizations`, `users`, `memberships`, `roles`, `permissions`, `role_permissions`, `membership_roles`, `departments`, `positions`, `teams`, `team_members`, `invitations`, `sessions`, `audit_logs`, `notifications`, `notification_preferences`.

- `User` هویت ورود است؛ `Employee` پرونده پرسنلی است؛ `Membership` رابطه کاربر با سازمان است. افراد می‌توانند پرونده پرسنلی داشته باشند ولی حساب ورود نداشته باشند و برعکس.
- `role` با سمت شغلی یکی نیست. «مدیرعامل» می‌تواند یک سمت باشد؛ توانایی دیدن حقوق، سند محرمانه یا تأیید پرداخت فقط از Permission می‌آید.
- ترکیب RBAC + Scope/ownership: `org:manage`, `members:invite`, `projects:create`, `tasks:update`, `hr:read`, `hr:sensitive:read`, `documents:approve`, `finance:approve`, `ai:use` و مجوزهای موردنیاز.
- Default Deny؛ هر Endpoint و هر رکورد سازمانی باید در Server مجوزسنجی شود. منوی مخفی‌شده در UI مجوز امنیتی نیست.
- سیاست‌های ورود پیشنهادی: password hash امن، HTTPS، session expiration، CSRF protection برای cookie، rate limiting، امکان MFA/Passkey/OAuth مرحله بعد.
- حذف حساس: Soft delete/archive، دسترسی‌زدایی، anonymization و retention مطابق نیاز حقوقی.

### صفحات
`/workspace/organization`, `/workspace/members`, `/workspace/teams`, `/workspace/roles`, `/workspace/audit`, `/workspace/invitations`.

### قرارداد API نمونه
`GET/POST /api/v1/organizations`, `GET/POST /api/v1/organizations/{org_id}/members`, `POST /api/v1/invitations`, `GET/PUT /api/v1/roles`, `GET /api/v1/audit-events`.

### معیار پذیرش
کاربر عضو دو سازمان نتواند با دستکاری URL یا ID به داده سازمان دیگر دسترسی یابد؛ تمام APIها مجوز را مستقل از UI بررسی کنند؛ تغییر مجوز در Session فعال اعمال شود؛ تراکنش‌های مدیریتی در Audit ثبت شوند.

## 5. مدیریت پروژه / کارهای من (Module 2)

### موجودیت‌ها
`projects`, `project_members`, `project_pages`, `task_lists`, `task_statuses`, `tasks`, `task_assignees`, `task_checklists`, `task_checklist_items`, `task_dependencies`, `task_comments`, `task_labels`, `task_label_links`, `task_watchers`, `task_activities`, `task_templates`, `task_custom_fields`, `worklogs`.

- هر پروژه متعلق به یک سازمان؛ صفحه ← لیست ← ستون وضعیت ← کار. کار می‌تواند چندمسئولی، فرزند، دارای اولویت، تخمین زمان، تاریخ شروع/سررسید، وابستگی و فایل باشد.
- Views: Kanban با Drag & Drop، Data Table با فیلتر/Sort، Timeline/Gantt، Calendar. نماها روی یک منبع داده کار می‌کنند؛ جابه‌جایی نما داده را کپی نمی‌کند.
- My Work: واگذارشده به من، واگذارشده توسط من، دنبال‌شده، امروز، سررسید نزدیک، دیرکرد، بدون موعد؛ Saved Views.
- Business rules: عدم چرخه در `task_dependencies`؛ جلوگیری از جابه‌جایی غیرمجاز؛ تست timezone و تاریخ شمسی در Presentation.
- پروژه‌ها و وظایف فعلی باید با نگه‌داشت شناسه یا `legacy_id`، قبل از Refactor به ساختار جدید مهاجرت یابند.

### صفحات
`/workspace/my-work`, `/workspace/projects`, `/workspace/projects/{id}/board`, `/table`, `/timeline`, `/calendar`, `/settings` و پنل Task Details با Deep Link.

### API نمونه
`/api/v1/projects/{id}/pages`, `/api/v1/task-lists`, `/api/v1/tasks/{id}/dependencies`, `/api/v1/tasks/{id}/comments`, `/api/v1/my-work`, `/api/v1/saved-views`, `/api/v1/worklogs`.

### معیار پذیرش
ویرایش کار در کانبان فوراً در جدول/تقویم منعکس شود؛ بدون Refresh دستی وضعیت همگام گردد؛ تست تغییر همزمان دو کاربر و تشخیص Conflict داشته باشد؛ بدون اجازه، drag/drop یا edit پذیرفته نشود.

## 6. منابع انسانی پیشرفته (Module 3)

### موجودیت‌ها
`employees` (افزایش تدریجی فیلدها), `employment_contracts`, `employee_positions`, `employee_departments`, `org_reporting_relations`, `employee_documents`, `leave_requests`, `leave_balances`, `attendance_events` (فاز توسعه بعدی), `employee_change_history`, `employee_assets`.

- پرونده افراد با نقش مدیریتی تا کارگر/پیمانکار، و قرارداد، دپارتمان، مدیر مستقیم، وضعیت استخدامی و سوابق تغییر سمت.
- درخت سازمانی و گزارش‌دهی بدون چرخه، جستجو/فیلتر، نمای جدول، کارت پرونده، سوابق همکاری، محدودیت دسترسی به فیلدهای حساس.
- `Employee.user_id` اختیاری است؛ شماره‌پرسنلی در سطح سازمان Unique باشد (`organization_id`, `personnel_code`).
- شماره تماس/ایمیل/یادداشت‌های محرمانه و فایل‌های قرارداد تنها برای افراد مجاز قابل مشاهده شوند.
- ماژول HR در این طرح شامل قرارداد/مرخصی و دارایی کارکنان نیز هست؛ **Payroll کامل و بیومتریک** پروژه مستقل تخصصی است و باید جداگانه تعیین دامنه و مقررات شود.

### صفحات
`/workspace/hr/employees`, `/workspace/hr/employees/{id}`, `/workspace/hr/org-chart`, `/workspace/hr/contracts`, `/workspace/hr/leave`.

### معیار پذیرش
ایجاد پرونده برای شخص بدون حساب ورود ممکن باشد؛ یکتا بودن کد پرسنلی در هر سازمان؛ تاریخچه جابه‌جایی واحد محفوظ؛ چرخه مدیران رد شود؛ کاربر عادی به اسناد حساس دسترسی نداشته باشد.

## 7. ارتباطات و همکاری (Module 4)

### موجودیت‌ها
`conversations`, `conversation_members`, `messages`, `message_edits`, `message_reactions`, `message_reads`, `mentions`, `attachments`, `meetings`, `meeting_participants`, `meeting_minutes`, `announcements`.

- گفتگو مستقیم/گروهی در سطح سازمان با امکان پیوند پیام به پروژه/وظیفه/مشتری/سند؛ ویرایش/حذف با سیاست مشخص؛ اعلان منشن، فایل و جستجو.
- جلسه: زمان، دستور جلسه، شرکت‌کنندگان، صورتجلسه، تصمیم‌ها، Action Item با ایجاد وظیفه مرتبط. تماس ویدیویی از ابتدا الزامی نیست؛ اتصال به Provider اختیاری با بررسی حریم خصوصی و هزینه.
- Delivery: HTTP REST برای تاریخچه، Real-time Transport جداگانه (WebSocket/Managed Realtime) برای رویداد جدید؛ event persistence در DB، Pub/Sub برای fanout و Offline sync.
- MVP بدون RTC و بدون ذخیره ویدیو؛ صدا/فایل صرفاً روی storage خصوصی و با مجوز.

### صفحات
`/workspace/chat`, `/workspace/meetings`, `/workspace/notifications`, پنل گفتگو در صفحات پروژه.

### معیار پذیرش
ارسال پیام، نمایش تاریخچه، مجوز عضویت گفتگو، اعلان، بازیابی پیام پس از reconnect، جلوگیری از نشت پیام بین سازمان‌ها؛ پاسخ real-time در شرایط شبکه ضعیف قابل بازیابی باشد.

## 8. اسناد و مکاتبات (Module 5)

### موجودیت‌ها
`document_folders`, `documents`, `document_versions`, `document_permissions`, `correspondence`, `correspondence_recipients`, `correspondence_referrals`, `document_approvals`, `approval_steps`, `file_objects`, `file_access_logs`.

- سند و نسخه‌بندی با مالک، ارتباط به موجودیت (پروژه/مشتری/شخص)، برچسب و سطح محرمانگی؛ پوشه‌ها، فایل‌های پیوست و پیش‌نمایش امن.
- دبیرخانه: نامه وارده/صادره/داخلی، شماره‌گذاری یکتای سازمانی در تراکنش، ارجاع، کارتابل، مهلت پاسخ، پاراف، چندمرحله‌ای بودن امضا/تأیید (بدون ادعای امضای دیجیتال معتبر حقوقی تا بررسی الزامات).
- ذخیره فایل روی Object Storage، metadata در PostgreSQL؛ ویروس‌اسکن و MIME/size validation، URL کوتاه‌مدت و کنترل مجوز قبل از دسترسی.

### صفحات
`/workspace/documents`, `/workspace/correspondence/inbox`, `/outbox`, `/register`, `/approvals`.

### معیار پذیرش
تاریخچه نسخه سند حذف نشود، شماره نامه در شرایط همزمانی تکراری نشود، پرونده محرمانه با لینک مستقیم قابل خواندن نباشد، ارجاع و تأیید Audit داشته باشد.

## 9. مشتریان و فروش (Module 6)

### موجودیت‌ها
`accounts`/`customers`, `contacts`, `leads`, `opportunities`, `pipelines`, `pipeline_stages`, `crm_activities`, `quotes`, `quote_items`, `sales_orders`, `customer_notes`, `customer_project_links`.

- سرنخ → مشتری بالقوه → فرصت فروش → پیش‌فاکتور/پیشنهاد → قرارداد یا سفارش → پروژه.
- پرونده ۳۶۰ درجه مشتری: تماس‌ها، مکاتبات، پروژه‌ها، فاکتورها، نشست‌ها، فایل‌ها. Duplicate detection و فرایند Merge با Audit.
- Customer-facing portal، ایمیل/SMS و اتوماسیون کمپین در آینده پس از انتخاب سرویس و رضایت/قوانین ارتباطی؛ شماره تلفن مشتری مجوز ارسال تبلیغ نیست.

### صفحات
`/workspace/crm/leads`, `/workspace/crm/opportunities`, `/workspace/crm/customers/{id}`, `/workspace/crm/pipeline`, `/workspace/crm/quotes`.

### معیار پذیرش
هر سرنخ یک مسئول داشته باشد، تغییر stage تاریخچه داشته باشد، تبدیل Opportunity به Project روابط واقعی بسازد و داده دوباره‌کاری نشود؛ کاربران بدون مجوز فروش نتوانند مبلغ‌ها را مشاهده کنند.

## 10. مالی و زمان‌های کاری (Module 7)

### موجودیت‌ها
`currencies`, `cost_centers`, `budgets`, `expenses`, `income_records`, `invoices`, `invoice_lines`, `payments`, `payment_allocations`, `worklogs`, `timesheet_periods`, `timesheet_approvals`, `project_costs`, `project_rates`.

- Amount با `NUMERIC/DECIMAL` یا کوچک‌ترین واحد پول به‌صورت integer، همراه با currency؛ نرخ تبدیل و تاریخ، واحد ریال/تومان واضح. عدم استفاده از floating point برای پول.
- ثبت هزینه/درآمد، بودجه، مرکز هزینه، دسته‌بندی، تخصیص به مشتری/پروژه، تایم‌شیت اعضا، تأیید زمانی و محاسبه هزینه پروژه.
- سیاست اصلاح: تراکنش نهایی audit/void/adjustment داشته باشد، نه حذف خام؛ تفکیک مالی عملیاتی از دفتر کل حسابداری رسمی.
- دسترسی مدیر مالی به داده مجاز؛ مخفی‌شدن مبلغ در UI کافی نیست.

### صفحات
`/workspace/finance/overview`, `/transactions`, `/budgets`, `/invoices`, `/timesheets`, `/project-costs`.

### معیار پذیرش
جمع‌ها در گزارش‌ها با ریزتراکنش برابر باشند، ارز و واحد اشتباه ترکیب نشوند، تأیید/لغو تراکنش Audit داشته باشد، ثبت زمان تکراری یا هم‌پوشان طبق سیاست کنترل شود.

## 11. گزارش‌ها و اتوماسیون AI (Module 8)

### موجودیت‌ها
`report_definitions`, `report_runs`, `saved_dashboards`, `kpi_definitions`, `automation_rules`, `automation_runs`, `assistant_conversations`, `assistant_messages`, `ai_tool_invocations`, `ai_provider_configs`, `ai_usage_records`.

- KPIهای وابسته به Query معتبر و نسخه‌دار؛ گزارش پروژه، HR، فروش، مالی و زمان؛ فیلتر، Drill-down، Export دارای مجوز (CSV/XLSX/PDF فاز ثانویه).
- AI Assistant: **read-only by default**؛ Retrieval با سند مجاز، پاسخ همراه provenance؛ عملیات تغییر دهنده فقط از ابزارهای whitelist و با تأیید انسانی برای اعمال حساس (مثل پرداخت، حذف یا ارسال پیام).
- Provider Adapter: Cloud API با تنظیمات و هزینه و سقف، Local LLM در صورت توان سخت‌افزار، Rule-Based fallback. اتصال اشتراک ChatGPT/Claude به Backend به‌عنوان API رایگان یا دائمی فرض نمی‌شود.
- Automation: `Trigger → Conditions → Authorized Action → Idempotency Key → Log/Retry`; جلوگیری از Loop، Rate Limit و تفکیک سازمان.

### صفحات
`/workspace/reports`, `/workspace/reports/builder`, `/workspace/automations`, `/workspace/assistant`, `/workspace/ai/settings`.

### معیار پذیرش
دستیار هرگز رکورد غیرمجاز در بازیابی دریافت نکند؛ هر اقدام خارجی explicit approval و audit داشته باشد؛ گزارش‌ها Reproducible و دارای بازه زمانی مشخص باشند.

## 12. طراحی تجربه کاربری (UI / UX)

### Design System اختصاصی Company OS
- هویت: cyan / electric blue / violet (Light با زمینه روشن و contrast مناسب، Dark با glows کنترل‌شده). Neon فقط برای تاکید؛ متن، جدول و فرم‌ها ساده و خوانا.
- حفظ Landing نئونی دوتم و دکمه ورود/اسکرول؛ Workspace مستقل با Sidebar جمع‌شونده، Header، Breadcrumb، Global Search، Command Palette، Notifications و Org Switcher.
- منوی ساختارگرا: **خانه؛ کارهای من؛ پروژه‌ها؛ برنامه‌ریزی؛ تیم و منابع انسانی؛ پیام‌ها و جلسات؛ اسناد و مکاتبات؛ مشتریان و فروش؛ مالی و زمان؛ گزارش‌ها؛ دستیار و اتوماسیون؛ مدیریت سازمان/تنظیمات.**
- Patternها: Task Drawer، Detail Page، Table Filters، Kanban Cards، Timeline/Gantt، Org Chart، File Picker، Approval Inbox، Empty/Error/Loading States، Confirmations، Undo برای عمل قابل بازگشت.
- Accessibility: keyboard navigation، focus visible، semantic role، contrast و reduced motion؛ responsive mobile/tablet/desktop.
- i18n: تمام Labelها، Errorهای Server، واحد و تاریخ نمایشی FA/EN؛ DB با Enum/code بی‌طرف نسبت به زبان. داده تایپ‌شده توسط کاربر به‌صورت خودکار ترجمه یا تغییر داده نمی‌شود.
- Bidi: `<html lang dir>`، CSS logical properties، `dir=ltr` برای کد/عددهای فنی/ایمیل، ترجمه کامل Navigation.
- QA: اسکرین‌شات واقعی از اپ Next.js در Dark/Light × FA/EN × desktop/tablet/mobile؛ عدم پذیرش CSS probe به‌عنوان جایگزین Build.

### نگاشت الهام طراحی
- از **میزیتو**: ماژول‌های یکپارچه گفتگو/نامه‌نگاری/CRM/تاییدها و اتصال آن‌ها به پروژه.
- از **تسکولو ۳**: سلسله‌مراتب سازمان/پروژه/صفحه/لیست/کار، نماهای چندگانه، My Work و Permissionهای تیمی.
- از **Company OS**: هویت نئونی و لندینگ، داشبورد داده‌محور، فارسی/انگلیسی و تم دوگانه.

## 13. Data Model + Cross-module Relationships

```text
Organization ──< Membership >── User
     ├────< Department ──< Position
     ├────< Employee ────(optional user_id)──> User
     ├────< Team ─────────< TeamMembership
     ├────< Project ────< Page ────< TaskList ────< Task
     │                  └──< ProjectMembership       ├──< ChecklistItem
     │                                               ├──< TaskAssignee
     │                                               ├──< TaskDependency
     │                                               ├──< Comment
     │                                               └──< Worklog
     ├────< Customer ────< Contact / Opportunity / Quote
     │            └──< Project (customer association)
     ├────< Correspondence ──< Referral / ApprovalStep
     ├────< Document ────< DocumentVersion ──> FileObject
     ├────< Conversation ──< Message ──> FileObject
     ├────< Invoice / Expense / Payment ──> Customer / Project
     ├────< AuditLog
     └────< AutomationRule / ReportDefinition / AIToolInvocation
```

**اصول Schema:** هر رکورد کسب‌وکاری `organization_id`؛ `id` پایدار؛ `created_at`, `updated_at`, `created_by`; indexes ترکیبی `organization_id` و کلیدهای فیلتر؛ FK و حذف محافظه‌کارانه؛ `deleted_at` برای موارد لازم؛ timestamps در UTC و نمایش با locale؛ pagination و cursor.

## 14. API / Integration Contracts

- قراردادها با OpenAPI منتشر و TypeScript client از schema تولید شوند؛ schema دستی فقط برای موقت.
- با `GET/POST/PATCH/DELETE /api/v1/...` ادامه داده شود؛ Endpointهای موجود تا زمان migration با adapter سازگار بمانند. تغییر breaking تنها با `/api/v2` و Deprecation Plan.
- لیست‌ها: `page_size`, `cursor`, `filter`, `sort`; خطا: `code`, `message`, `fields`, `request_id`; optimistic locking برای تغییر همزمان.
- پیوست: `POST /api/v1/files/upload-request` → URL امضاشده → metadata register → scan/verify → link to record.
- Event contract: `organization_id`, `event_type`, `subject_id`, `actor_id`, `occurred_at`, `event_id`, `idempotency_key`, `payload_version`.
- مثال‌ها: `GET /api/v1/my-work`, `POST /api/v1/tasks/{id}/dependencies`, `POST /api/v1/meetings/{id}/minutes`, `POST /api/v1/correspondence/{id}/refer`, `POST /api/v1/opportunities/{id}/convert`, `GET /api/v1/finance/project-costs`, `POST /api/v1/assistant/queries`.
- هر Endpoint فیلتر `organization_id` و permission check در Service اعمال کند؛ client-provided org ID مستقل از Session معتبر شناخته نشود.

## 15. مهاجرت بدون از دست رفتن داده

1. Backup از فایل‌دیتابیس موجود یا PostgreSQL و Export کنترل‌شده؛ ثبت checksum و count.
2. Baseline Migration Alembic از Schema فعلی؛ هیچ `DROP TABLE` در اولین مرحله.
3. Create/Backfill `organization_id` با Default Organization معتبر و ارتباط user/employee؛ نگاشت `legacy_id`.
4. تاریخ‌های متنی (`تعیین نشده`, `۱۴۰۵-...`) به nullable `date` تبدیل شوند؛ رشته منبع تا اعتبارسنجی نهایی نگهداری شود.
5. وضعیت‌ها/اولویت‌ها از متن فارسی به کد پایدار مثل `in_progress`, `high` همراه با render locale انتقال پیدا کنند.
6. مدیر/مسئول متنی به روابط عضویت/شخص Map شوند؛ موارد مبهم در Review Queue قرار گیرند، هرگز با حدس به شخص اشتباه وصل نشوند.
7. `ModuleItem` generic تا آماده شدن مدل تخصصی Document/Procurement/CRM نگه داشته شود؛ سپس migration و dual-read در دوره گذار.
8. Reconciliation: شمار رکوردها، FK، Aggregate sums و نمونه‌گیری دستی؛ Rollback Plan و زمان Freeze انتشار.

## 16. فازبندی و وابستگی‌ها (No invented calendar estimates)

| گام | هدف | وابستگی | تحویل فنی و شرط عبور |
|---|---|---|---|
| 0 | Baseline + QA + Design Freeze | تأیید کاربر | نصب وابستگی، Build واقعی، تصویربرداری واقعی، نسخه پشتیبان، معماری و Design Tokens |
| 1 | Identity + Organization + RBAC | 0 | Multi-user، Tenant Isolation، مجوزهای واقعی، Migration و Audit |
| 2 | Project/Task Engine + My Work | 1 | صفحات/لیست/تسک، کانبان/جدول، جزئیات، تست همزمانی و جستجو |
| 3 | Advanced HR | 1 | پرونده، درخت سازمانی، قرارداد، ارتباط کارمند/حساب و محدودیت داده حساس |
| 4 | Collaboration | 1,2 | پیام، کانال، فایل، اعلان، صورتجلسه، Reconnect test |
| 5 | Documents/Correspondence | 1,4 | Versioning، شماره نامه، ارجاع، کارتابل و چندمرحله‌ای‌بودن تایید |
| 6 | CRM/Sales | 1,2,5 | Leads، Opportunity، پرونده مشتری، تبدیل فروش به پروژه |
| 7 | Finance/Worklogs | 1,2,6 | هزینه، درآمد، بودجه، تایم‌شیت، هزینه پروژه، Numeric precision |
| 8 | Analytics/AI/Automation | 1 تا 7 | KPI معتبر، Reports، مجوز ابزار AI، Audit و Human Approval |
| 9 | Hardening & Deployment | همه | QA امنیتی، Load/Backup/Recovery، CI/CD، Staging، UAT و اجازه جداگانه Push/Deploy |

این گام‌ها زمان تقویمی تعهدشده نیستند؛ بعد از بررسی واقعی Build و نیازهای سازمان، برای هر گام تخمین مبتنی بر اندازه‌گیری ارائه می‌شود.

### Milestones

- **M1 (Operational Core):** فازهای 0–3؛ سازمان، کاربران، کارها، HR و Design System پایدار.
- **M2 (Connected Company):** فازهای 4–7؛ چت، اسناد، CRM، مالی.
- **M3 (Intelligence + Release):** فازهای 8–9؛ BI/AI امن و آماده‌سازی انتشار.

## 17. QA, Security & Performance Acceptance Gates

- `npm ci && npm run typecheck && npm run build` روی نسخه رسمی Node همخوان با پکیج‌ها؛ `pytest`, migration up/down در محیط تست و lint/static checks.
- Playwright E2E روی Next.js واقعی: Auth، سازمان، Drag & Drop، CRUD، Attachment, Approval, Search, Dark/Light، RTL/LTR، responsive در عرض‌های 390/768/1366/1672.
- Contract tests بر اساس OpenAPI برای عدم تغییر ناخواسته DTOها.
- Security tests: unauthorized/forbidden/IDOR/Cross-org، CSRF، XSS، file upload، replay/idempotency، rate limiting، privilege escalation؛ default-deny.
- Audit retention و Mask کردن PII در log؛ backup/restore تمرینی، secret scanning، Dependency vulnerability checks.
- Performance budget: LCP/CLS/INP مطابق معیار مصوب بعد از اندازه‌گیری Baseline؛ صفحه‌های پرتعداد با server pagination/virtualized list؛ بهینه‌سازی واقعی assetها و fonts.
- UX acceptance: No dead button / placeholder module claimed as finished. Dark/Light/Nav در FA/EN به یک اندازه کار کند؛ Hero صرفاً پس‌زمینه باشد، UI از تصویر تزئینی خوانده نشود.
- Deploy gate: دسترسی واقعی مقصد Vercel، DB provider و Storage، دامنه، Secretها، Realtime provider، Backup و بودجه مصرف تأیید شوند.

## 18. ریسک‌ها و تصمیم‌های باز (Decision Log)

| موضوع | پیش‌فرض پیشنهادی | ریسک/تصمیم لازم |
|---|---|---|
| Tenant scope | معماری آماده چندسازمانی؛ فاز اول یک سازمان فعال | آیا فروش SaaS به چند شرکت مدنظر است؟ |
| Identity | ورود کاربران سازمانی با رمز امن، دعوت‌نامه، Session امن | SSO/OAuth/Passkeys مرحله دوم؟ |
| UI fidelity | حفظ هویت Company OS، اقتباس Patterns | دسترسی مستقیم به صفحات خصوصی Mizito/Taskulu وجود ندارد |
| Realtime | سرویس مستقل یا Managed Realtime | Vercel WebSocket Public Beta اعلام‌شده برای Node؛ تطبیق Python و حساب هنوز تأیید نشده |
| Hosting | Frontend در Vercel، Backend مستقل پایدار به‌عنوان fallback | `experimentalServices` Private Beta و تأیید دسترسی حساب لازم است |
| AI Provider | Adapter قابل‌تعویض Local/API، read-only first | هزینه، حریم خصوصی، محل نگهداری داده و مجوز ابزار |
| Payroll | خارج از هسته اولیه | قوانین و داده حساس؛ طراحی ویژه پیش از اجرا |
| Multi-currency | IRR پیش‌فرض با مدل Currency جداگانه | واحد تومان/ریال و گردکردن باید روشن شود |
| Reusable code | Design tokens / reusable shared features | ممنوعیت یکپارچه کردن تمام منطق ماژول‌ها در یک God Component |

## 19. اجرای Codex پس از تأیید رسمی (FA → EN)

**نسخه فارسی Master Prompt (صرفاً پیش‌نویس، نه اجازه اجرا):**

> به‌عنوان Lead Engineer روی مخزن Company OS فعالیت کن. ابتدا `COMPANY-OS-2.0-ARCHITECTURE-BLUEPRINT.md` و نسخه موجود `v1.3.0` را بخوان. قبل از هر تغییر، وضعیت Git، فایل‌های موجود، نسخه پکیج‌ها، داده نمونه، APIها و محدودیت استقرار را بررسی و Baseline ثبت کن. هیچ کد، مسیر API و رکوردی را بدون نقشه Migration حذف یا تخریب نکن. معماری Modular Monolith با ماژول‌های هشت‌گانه، سازمان/مجوز/داده ایزوله، Next.js RTL/LTR + Light/Dark، PostgreSQL/Alembic، انواع داده دقیق و OpenAPI contract را **فقط در فاز صریحاً تأییدشده** پیاده‌سازی کن. برای هر فاز Acceptance Criteria، تست Unit/Integration/E2E/Visual/Security، مستندات و ZIP قابل اجرا را تکمیل و گزارش کن. از TypeSafe/JEV تنها در صورتی استفاده کن که فایل مهارت واقعی در محیط در دسترس و قابل خواندن باشد؛ نصب فرضی نکن. هر Push و Deploy تنها پس از دستور مجزای کاربر مجاز است. در مشکلات محیطی مانند DNS npm یا تأیید نشدن Build، نتیجه نامعتبر را موفق گزارش نکن.

**English Master Prompt (draft only, not execution authorization):**

> Act as the lead engineer for Company OS. Read the approved architecture blueprint and inspect v1.3.0 first. Establish a real build/test baseline, preserve the existing visual design and compatible API/data, and migrate incrementally using PostgreSQL/Alembic. Implement only explicitly approved phases of the eight-module, multi-organization-ready Modular Monolith with enforced server-side authorization, full FA/EN RTL/LTR, Light/Dark, OpenAPI contracts, secure storage, tested task workflows and permission-aware AI. For each phase provide executable tests, real browser screenshots, migration/rollback verification, updated documentation, and a reviewable ZIP. Do not claim a Next.js build passed unless it actually ran. Do not push to GitHub or deploy to Vercel without a separate explicit user instruction.

## 20. منابع رسمی بررسی‌شده

- میزیتو ـ امکانات: https://www.mizito.ir/features
- تسکولو ـ راهنمای نسخه ۳: https://taskulu.com/fa/v3/help
- تسکولو ـ تفاوت نسخه ۲ و ۳: https://taskulu.com/fa/v3/help/migration
- Next.js ـ Internationalization: https://nextjs.org/docs/app/guides/internationalization
- FastAPI ـ Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI ـ OAuth2 Scopes: https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/
- Alembic: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL numeric: https://www.postgresql.org/docs/current/datatype-numeric.html
- PostgreSQL Row Security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- Vercel Services: https://vercel.com/docs/services
- Vercel WebSocket Public Beta (22 Jun 2026): https://vercel.com/changelog/websocket-support-is-now-in-public-beta

**ملاحظات سند:** قابلیت‌های نمای خصوصی مرجع‌ها مستقیماً ممیزی نشده است. قابلیت‌های Product در این سند «طرح پیشنهادی» هستند مگر اینکه صریحاً «موجود در v1.3.0» یا «مستند رسمی» ذکر شده باشد. محدوده پروژه بزرگ است و بدون نیازسنجی تکمیلی، برآورد قطعی زمان/هزینه معتبر نیست. **اجرای هیچ مرحله‌ای تأیید نشده است.**
