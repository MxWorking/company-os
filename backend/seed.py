"""Deterministic sample data inspired by the attached visual reference. Development only."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from models import Project, Task, Approval, Expense, Activity, ModuleItem, Employee

PROJECT_NAMES = ['سامانه مشتریان','اپلیکیشن موبایل','زیرساخت ابری','تحلیل داده‌های سازمانی']
MANAGERS = ['محمد احمدی','سارا احمدی','علی رضایی','مریم کریمی']
STATUS = ['در حال اجرا']*12 + ['تکمیل شده']*6 + ['متوقف شده']*4 + ['در معرض ریسک']*2


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Project)):
        return
    for i in range(24):
        db.add(Project(name=PROJECT_NAMES[i] if i<4 else f'پروژه سازمانی {i+1}',manager=MANAGERS[i%4],initials=['ما','سا','عر','مک'][i%4],progress=[83,65,43,92][i%4],deadline=['۱۴۰۴-۰۸-۱۴','۱۴۰۴-۰۷-۲۹','۱۴۰۴-۰۹-۲۴','۱۴۰۴-۰۶-۳۰'][i%4],status=STATUS[i],color=['#2c88ff','#7864ec','#ff9750','#01b9bd'][i%4]))
    db.flush()
    for i in range(86):
        db.add(Task(title=['بازبینی گزارش مالی','طراحی صفحه ورود','تست زیرساخت ابری','بهبود عملکرد سامانه'][i%4] if i<4 else f'وظیفه سازمانی {i+1}',project_id=(i%24)+1,assignee=MANAGERS[i%4],status=['در حال انجام','در انتظار','انجام شده'][i%3],priority=['بالا','متوسط','پایین'][i%3],due_date='۱۴۰۴-۰۷-۲۰'))
    titles=['تأخیر در تحویل فاز طراحی','افزایش هزینه‌های زیرساخت','عدم تأیید سند قرارداد جدید','منقضی شدن گواهی SSL']
    sub=['پروژه سامانه مشتریان','بیش از سقف مصوب','در انتظار بررسی حقوقی','زیرساخت تولید']
    for i in range(12):
        db.add(Approval(title=titles[i%4] if i<4 else f'درخواست تأیید #{i+1}',subtitle=sub[i%4],severity='high' if i<2 else 'medium',status='در انتظار'))
    for name,amount,cat in [('سرویس‌های ابری',150_000_000,'زیرساخت'),('حقوق تیم محصول',210_000_000,'پرسنل'),('مجوز نرم‌افزار',90_000_000,'تجهیزات')]:
        db.add(Expense(title=name,amount=amount,category=cat,paid_at='۱۴۰۴/۰۶/۰۵'))
    for i,(title,detail,when) in enumerate([('سند پروژه جدید ایجاد شد','توسط محمد احمدی','۱۰:۳۰'),('وظیفه به‌روزرسانی شد','توسط سارا احمدی','۰۹:۱۵'),('نظر جدیدی ثبت شد','توسط علی رضایی','دیروز'),('فایل جدید بارگذاری شد','توسط مریم کریمی','دیروز')]):
        db.add(Activity(title=title,detail=detail,time=when,icon=['file','check','chat','file'][i]))
    data={
     'documents':[('قرارداد توسعه سامانه مشتریان','PDF · واحد حقوقی','در انتظار امضا'),('صورت‌جلسه کمیته محصول','DOCX · دبیرخانه','نهایی شده'),('راهنمای هویت بصری','PDF · طراحی','منتشر شده')],
     'procurement':[('تمدید سرویس سرور ابری','درخواست خرید · فناوری','در انتظار تأیید'),('خرید تجهیزات شبکه','درخواست خرید · زیرساخت','در حال بررسی')],
     'hr':[(n,'همکار سازمان','فعال') for n in MANAGERS],
     'knowledge':[('راهنمای شروع همکاری','دانش سازمانی','منتشر شده'),('استانداردهای توسعه نرم‌افزار','دانش سازمانی','منتشر شده')],
     'support':[('مشکل ورود همکار جدید','تیکت #۱۰۲۴','در حال بررسی'),('درخواست فعال‌سازی دسترسی','تیکت #۱۰۲۵','باز')],
     'settings':[('تنظیمات سازمان','پروفایل و زبان','آماده'),('تنظیمات امنیتی','دسترسی‌ها','آماده')]
    }
    for module,values in data.items():
        for title,subtitle,status in values:
            db.add(ModuleItem(module=module,title=title,subtitle=subtitle,status=status))
    if not db.scalar(select(func.count()).select_from(Employee)):
        personnel = [
            ('1001','حسین','یزدان‌پناه','مدیرعامل','مدیریت ارشد','مدیرعامل','فعال',None),
            ('1002','سارا','احمدی','مدیر ارشد','مدیریت','مدیر عملیات','فعال',1),
            ('1003','محمد','احمدی','مدیر','فناوری اطلاعات','مدیر فناوری','فعال',1),
            ('1004','مریم','کریمی','سرپرست','محصول','سرپرست محصول','فعال',2),
            ('1005','علی','رضایی','کارمند','توسعه','توسعه‌دهنده','فعال',3),
            ('1006','نیلوفر','قاسمی','کارمند','منابع انسانی','کارشناس منابع انسانی','فعال',2),
            ('1007','رضا','محمدی','کارگر','عملیات','نیروی خدمات','فعال',2),
            ('1008','مهدی','نوری','پیمانکار','پشتیبانی','پشتیبان قرارداد','فعال',3),
        ]
        for code,first,last,role,dept,title,status,supervisor in personnel:
            db.add(Employee(personnel_code=code,first_name=first,last_name=last,role=role,department=dept,job_title=title,employment_status=status,reporting_to_id=supervisor,employment_type='تمام‌وقت'))
            db.flush()
    db.commit()
