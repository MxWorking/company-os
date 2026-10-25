# Company OS v2.2.1 — رفع خطای Docker / .env / ورود مدیر

**علت خطای نشان‌داده‌شده:** Backend هنگام راه‌اندازی با `ValueError: Password must have at least 10 characters` متوقف شده است. این خطا از `ops/router.py -> seed_workspace() -> make_hash()` می‌آمد. در نسخه اصلاحی، حداقل رمز مدیر **۱۲ کاراکتر** است و پیش از راه‌اندازی سرور، بررسی واضح انجام می‌شود. هیچ رمز پیش‌فرض قابل‌حدسی در محصول فعال نیست.

## ۱) فایل `.env` باید کجا باشد؟

```text
company-os/
├── .env                 ← این فایل را خودت بساز
├── .env.example
├── docker-compose.yml
├── backend/
└── frontend/
```

از پوشه `company-os` (دقیقاً جایی که `docker-compose.yml` قرار دارد) دستورهای Docker را اجرا کن. فایل `backend/.env` **به‌صورت پیش‌فرض فایل اصلی Docker Compose نیست**. فایل واقعی `.env` در این ZIP عمداً وجود ندارد.

ابتدا فایل نمونه را کپی کن:

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Bash:**
```bash
cp .env.example .env
```

محتوای فایل را با مقادیر تصادفی **خودت** تکمیل کن:

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YOUR_UNIQUE_STRONG_PASSWORD_12_PLUS
SESSION_SECRET=RANDOM_SECRET_AT_LEAST_32_CHARACTERS
HR_ENCRYPTION_KEY=64_RANDOM_HEX_CHARACTERS
```

مقدارهای نمونه را **عیناً استفاده نکن**. برای رمز مدیر حداقل ۱۲ کاراکتر، بهتر است ۱۶+ کاراکتر تصادفی و منحصربه‌فرد انتخاب کنی. نام کاربری فقط شامل حروف لاتین، رقم، نقطه، خط تیره و زیرخط باشد. از گذاشتن `#`، `$` یا `=` بدون رعایت قواعد quoting در `.env` خودداری کن تا Compose مقدار را غیرمنتظره تفسیر نکند. برای مدیر بهتر است از Password Manager استفاده کنی.

برای تولید دو کلید امن (این دستورها کلیدها را روی صفحه **سیستم خودت** نشان می‌دهند، آن‌ها را فقط در `.env` قرار بده):

```bash
python -c "import secrets; print('SESSION_SECRET='+secrets.token_urlsafe(48)); print('HR_ENCRYPTION_KEY='+secrets.token_hex(32))"
```

**مهم:** اگر فایل‌های هویتی قبلاً رمزنگاری و ذخیره شده‌اند، تغییر یا گم‌شدن `HR_ENCRYPTION_KEY` قدیمی باعث غیرقابل‌بازیابی‌شدن آن‌ها می‌شود. این کلید را با احتیاط بکاپ امن بگیر. `SESSION_SECRET` با تغییرش نشست‌های قبلی را نامعتبر می‌کند.

## ۲) اجرای پروژه و بررسی واقعی env داخل کانتینر

دستور زیر فقط **اعتبار تنظیمات** را بررسی می‌کند و نه رمز را نمایش می‌دهد و نه به دیتابیس وصل می‌شود:

```bash
docker compose run --rm --no-deps backend python -m ops.bootstrap
```

در صورت موفقیت، پیام `Configuration preflight passed` دیده می‌شود. اگر هنوز رمز کوتاه باشد، خطای قابل‌فهم با نام دقیق متغیر نمایش داده می‌شود. برای بررسی syntax Compose بدون افشای مقدار Secret:

```bash
docker compose config --quiet
```

سپس:

```bash
docker compose up -d --build --force-recreate
docker compose ps
docker compose logs --tail=80 backend
```

سرویس `frontend` تا سالم‌شدن `backend` منتظر می‌ماند. وضعیت سالم باید با آدرس زیر پاسخ `status=ok` بدهد:

- `http://localhost:8000/health`
- `http://localhost:3000` صفحه ورود سایت است.

در ورود، همان `ADMIN_USERNAME` و `ADMIN_PASSWORD` تنظیم‌شده هنگام **اولین راه‌اندازی موفق** را وارد کن. در نسخه ۲، مسیر درست API ورود `/api/v2/auth/login` است؛ `/api/v1/auth/login` عمداً غیرفعال شده است.

## ۳) اگر Backend بالا آمد ولی رمز جدید کار نکرد

فایل `.env` فقط رمز **ساخت اولیه** مدیر را مشخص می‌کند؛ پس از ایجاد حساب، رمز به‌صورت hash در PostgreSQL نگهداری می‌شود. **ویرایش `.env` برای حساب موجود رمز را عوض نمی‌کند**. این رفتار برای جلوگیری از تعویض ناخواسته رمز و ایجاد حساب مدیر اضافی است.

پس از قرار دادن رمز جدیدِ ۱۲ کاراکتری یا بیشتر در فایل `.env`، برای اعمال عمدی آن روی حساب مدیر **موجود**، از ریشه پروژه این دستور را اجرا کن:

```bash
docker compose run --rm backend python -m ops.reset_admin --apply
```

این دستور رمز حساب owner سازمان اصلی را تغییر می‌دهد، ولی پروژه‌ها، اطلاعات پرسنل، وظایف و سایر رکوردهای دیتابیس را حذف نمی‌کند. اگر نام کاربری را هم در `.env` عوض کرده‌ای و می‌خواهی **همان حساب قبلی** به نام جدید تغییر کند:

```bash
docker compose run --rm backend python -m ops.reset_admin --apply --rename-to-configured
```

اگر بیش از یک حساب owner وجود دارد، `--username OLD_USERNAME` را اضافه کن. سپس:

```bash
docker compose up -d --force-recreate backend frontend
```

**هیچ‌وقت برای برطرف‌کردن خطای رمز از `docker compose down -v` استفاده نکن:** آن دستور volume پایگاه داده را حذف می‌کند. دستور `docker compose down` بدون `-v` داده volume را حفظ می‌کند، اما برای این اصلاح نیازی به آن هم نیست.

## ۴) خطاها و معنی آن‌ها

| خطا | معنی و اقدام |
|---|---|
| `ADMIN_PASSWORD ... too short` | رمز کمتر از ۱۲ کاراکتر یا نمونه غیرواقعی است؛ ریشه `.env` را درست کن |
| `Missing required ...` | متغیر در `.env` ریشه موجود نیست یا خالی است |
| `SESSION_SECRET` | کلید باید تصادفی و طول ۳۲+ کاراکتر داشته باشد |
| `HR_ENCRYPTION_KEY` | باید ۶۴ رقم hexadecimal (۳۲ بایت) باشد یا برای تست بدون مدارک، خالی بماند |
| `ADMIN_PASSWORD ... differs from SAVED owner` | حساب قبلاً ساخته شده؛ دستور `ops.reset_admin --apply` لازم است |
| `ADMIN_USERNAME differs from EXISTING owner` | نام قبلی هنوز فعال است؛ با `--rename-to-configured` عمداً تغییر بده |
| `Invalid credentials` | حساب پیدا نشده یا رمز در DB متفاوت است؛ از فرمان Reset استفاده کن |
| `backend unhealthy` | `docker compose logs --tail=100 backend` را بررسی کن |

## امنیت و محدوده تأیید

- داده و رمز واقعی برای تشخیص لازم نیست؛ در پیام یا اسکرین‌شات عمومی ارسال نکن.
- Docker Compose محلی دارای گذرواژه پایگاه داده مخصوص توسعه است؛ آن را در اینترنت Deploy نکن.
- اجرای CLI و ورود با دیتابیس SQLite موقت به‌صورت **integration test واقعی** آزمایش شده؛ اجرای Docker Compose در این محیط انجام نشده، چون موتور Docker نصب نیست. لازم است در سیستم تو دوباره بررسی شود.
- نرم‌افزار هنوز برای مدارک هویتی واقعی Production-ready ارزیابی نشده است؛ سیاست داده، بکاپ، اسکن مدارک و ممیزی امنیت باید تکمیل شوند.

**وضعیت انتشار:** هیچ Push به GitHub و هیچ Deploy در Vercel انجام نشده است.
