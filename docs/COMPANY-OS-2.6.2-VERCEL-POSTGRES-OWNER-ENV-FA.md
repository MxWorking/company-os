# Company OS 2.6.2 | Vercel PostgreSQL and ENV-based Owner (FA)

این نسخه بر اساس سورس ۲.۶ واقعی است. UI/UX، حسابداری، پرسنل و سایدبار تغییر نکرده‌اند. بدون دیتابیس و ممیزی امنیتی، **Production آماده استفاده با داده واقعی نیست**.

## مشکل ورود
- `SESSION_SECRET` رمز مدیر نیست؛ برای امضای Cookie لازم است و باید ثابت و تصادفی (حداقل ۳۲ کاراکتر) باشد.
- `HR_ENCRYPTION_KEY` رمز مدیر نیست؛ فقط برای مدارک رمزگذاری‌شده منابع انسانی است و اگر قبلاً مدارک ذخیره شده‌اند، همان کلید قبلی باید حفظ شود.
- در نسخه‌های پیشین، تغییر `ADMIN_USERNAME` و `ADMIN_PASSWORD` پس از ایجاد Owner در DB، حساب موجود را به‌روزرسانی نمی‌کرد.
- اکنون در محیطی که `ADMIN_ENV_SYNC=true` باشد، بک‌اند هنگام راه‌اندازی **همان یک Owner موجود** را با نام/رمز ENV همگام می‌کند و هش رمز در DB نگهداری می‌شود. نقش‌ها و نشست/CSRF تغییر نمی‌کنند؛ نام تکراری یا چند Owner موجب توقف امن می‌شود.

## اتصال دیتابیس در Supabase
1. وارد https://supabase.com/dashboard شو و یک **پروژه اختصاصی جدید** برای Company OS بساز؛ از دیتابیس پروژه‌های دیگر استفاده نکن.
2. از Connect، **Transaction Pooler** با پورت **6543** را انتخاب کن. برای Vercel Serverless مناسب است؛ hostname را از داشبورد کپی کن.
3. رمز DB را در URI قرار بده و `sslmode=require` را اضافه کن. کاراکترهای خاص پسورد URL-encode شوند. مثال ساختگی: `postgresql://postgres.PROJECT_REF:DB_PASSWORD@HOST.pooler.supabase.com:6543/postgres?sslmode=require`.
4. در Vercel، پروژه backend را باز کن: https://vercel.com/hosseinyazdanpanahs-projects/company-os-api → Settings → Environment Variables.

| متغیر backend | مقدار |
|---|---|
| `DATABASE_URL` | URI واقعی Supabase و TLS |
| `ADMIN_USERNAME` | نام دلخواه انگلیسی (۳ تا ۸۰ کاراکتر) |
| `ADMIN_PASSWORD` | رمز دلخواه قوی حداقل ۱۲ کاراکتر |
| `ADMIN_ENV_SYNC` | `true` |
| `SESSION_SECRET` | رشته تصادفی حداقل ۳۲ کاراکتر |
| `HR_ENCRYPTION_KEY` | اختیاری برای HR؛ **کلید موجود قبلی** |

برای ساخت Secret می‌توانی در سیستم خودت اجرا کنی:
`python -c "import secrets;print(secrets.token_urlsafe(48))"`
از قرار دادن هرگونه رمز یا کلید در GitHub، چت، `NEXT_PUBLIC_` یا Source Code خودداری کن.

5. ENV را ابتدا فقط برای **Preview** تست کن؛ برای Production دیتابیس مجزا یا روند ارتقا و بکاپ لازم است.
6. در Frontend `company-os-web` متغیر `BACKEND_ORIGIN` باید آدرس API همان Environment را داشته باشد (بدون `/api` یا / انتهایی). در Preview شاخه `company-os-v2.6` این مقدار تنظیم شده است.
7. **Redeploy** لازم است؛ ENV جدید روی Deploymentهای قدیمی اعمال نمی‌شود.

## تست بعد از Redeploy
- `/health` بک‌اند باید HTTP 200 بدهد.
- در Landing اصلی، فرم «ورود اعضا» با `ADMIN_USERNAME` و `ADMIN_PASSWORD` باید وارد شود؛ `/api/v2/me` نقش `owner` بدهد.
- رمز قبلی نباید کار کند؛ عضو معمولی نباید به owner ارتقا یابد.
- اگر خطا می‌بینی، Runtime Logs همان Deployment را بررسی کن؛ PostgreSQL و نام کاربری/رمز را در Logs چاپ نکن.

## محدودیت‌های امنیتی
- هنوز SQLite محلی Docker یا دیتابیس قدیمی به Supabase منتقل نشده‌اند. Volume/DB قدیمی را حذف نکن؛ برای مهاجرت داده واقعی Backup و روش مستقل لازم است.
- Preview و Production را با دو ENV مدیر متفاوت به یک دیتابیس مشترک وصل نکن، چون رمز Owner را پی‌درپی عوض می‌کنند.
- تغییر رمز ENV نشست‌های موجود را فوراً باطل نمی‌کند؛ برای خاتمه فوری همه نشست‌ها، `SESSION_SECRET` را نیز بچرخان و Redeploy کن.
- ذخیره فایل HR روی فایل‌سیستم تابع Serverless پایدار نیست؛ بدون ممیزی داده واقعی بارگذاری نکن.
- `Base.metadata.create_all` جایگزین migration نسخه‌دار Alembic نیست.
- Backend: ۵۶ تست محلی موفق؛ GitHub CI و Preview باید بعد از Push مجدداً بررسی شوند.

منابع رسمی:
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/kb/troubleshooting/using-sqlalchemy-with-supabase-FUqebT
- https://vercel.com/docs/environment-variables
