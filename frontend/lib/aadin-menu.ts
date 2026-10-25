/** Navigation taxonomy from aadin-company-os-final-report-fa.md (17 Oct 2026).
 * Items labelled observed were seen in the source app or its documented menus.
 * These menu titles do not imply working financial transactions in Company OS.
 */
export type AadinLeaf={id:string;fa:string;en:string;descFa:string;descEn:string;draftKind?:string;ledger?:boolean;report?:boolean};
export type AadinGroup={id:string;fa:string;en:string;items:AadinLeaf[]};
export type AadinArea={id:string;fa:string;en:string;groups:AadinGroup[]};
const leaf=(id:string,fa:string,en:string,descFa:string,descEn:string, draftKind?:string):AadinLeaf=>({id,fa,en,descFa,descEn,draftKind});
export const aadinAreas:AadinArea[]=[
 {id:'dashboard',fa:'پیشخوان',en:'Overview',groups:[{id:'overview',fa:'پیشخوان',en:'Dashboard',items:[
  leaf('dashboard','نمای کلی مالی','Financial overview','فروش امروز و دیروز، وضعیت دوره و میان‌بر عملیات','Daily sales, active period and quick actions'),
  leaf('recent','آخرین تغییرات','Recent changes','فهرست عملیات و سابقهٔ تغییرات','Recent operations and audit trail'),
  leaf('quick','میان‌برهای عملیاتی','Quick actions','فروش، خرید، دریافت، پرداخت و پیش‌فاکتور','Shortcuts to sales, purchases, receipts and payments')]}]},
 {id:'parties',fa:'اشخاص',en:'Parties',groups:[{id:'people',fa:'اشخاص',en:'Party directory',items:[
  leaf('party-list','فهرست اشخاص','People and companies','اشخاص، مشتریان و تأمین‌کنندگان','Customers and suppliers','person'),
  leaf('party-groups','گروه اشخاص','Party groups','گروه‌بندی مشتری و فروشنده','Customer and vendor groups'),
  leaf('party-balances','مانده و گردش اشخاص','Party balances & activity','مانده، خرید، فروش، دریافت و پرداخت','Party balances and activity')]}]},
 {id:'inventory',fa:'انبار',en:'Inventory',groups:[
  {id:'goods',fa:'کالا و خدمات',en:'Goods & services',items:[
   leaf('items','کالاها','Products','نام، کد، بارکد، قیمت‌ها و حداقل موجودی','Product codes, prices and thresholds','item'),
   leaf('archive','آرشیو کالاها','Archived products','مشاهده کالاهای غیرفعال','Browse archived products'),
   leaf('item-groups','گروه و زیرگروه کالا','Categories & subcategories','گروه‌بندی کالا','Product taxonomy'),
   leaf('tags','تگ‌های کالا','Product tags','برچسب و ایموجی کالا','Labels and emoji tags'),
   leaf('units','واحد و واحد فرعی','Units & conversions','ضریب تبدیل و قیمت‌گذاری دو واحدی','Unit conversions and multiple prices'),
   leaf('services','خدمات','Services','قلم غیرانبارداری و تعرفه','Non-stock services and pricing','service'),
   leaf('invoice-fees','هزینه‌های فاکتور','Invoice charges','قلم هزینهٔ افزوده به فاکتور','Invoice-level charges','invoice_charge')]},
  {id:'stock',fa:'موجودی و سفارش',en:'Stock & ordering',items:[
   leaf('inventory-summary','موجودی کالا','Stock balances','موجودی، حداقل و هشدار','Inventory balances and alerts'),
   leaf('inventory-history','ورودی و خروجی کالا','Stock movements','گردش و کاردکس کالا','Stock movements and history'),
   leaf('orders','سفارش','Order page','صفحه سفارش و گزینه‌های نمایش','Order form and settings','customer_order'),
   leaf('catalog','کاتالوگ','Product catalog','فهرست کالاها، قیمت‌ها و سفارش ناموجود','Catalog configuration','catalog')]}]},
 {id:'operations',fa:'امور مالی',en:'Financial operations',groups:[
  {id:'sales',fa:'فروش',en:'Sales',items:[
   leaf('sales-list','فروش‌ها','Sales invoices','فهرست فاکتورهای فروش','Sales records','sales_invoice'),
   leaf('quotes','پیش‌فاکتور','Proforma invoices','پیش‌فاکتور و وضعیت آن','Quotes and proforma invoices','sales_quote'),
   leaf('sales-settings','تنظیمات فروش','Sales settings','خریدار پیش‌فرض، قیمت اول/دوم و بارکد','Default customer, price tier and barcode alerts'),
   leaf('sales-return','برگشت از فروش','Sales returns','برگشت مرتبط با فروش مرجع','Sales return linked to original sale','sales_return'),
   leaf('receivables','مطالبات مشتریان','Customer receivables','ماندهٔ باز مشتریان','Open customer receivables')]},
  {id:'purchases',fa:'خرید',en:'Purchases',items:[
   leaf('purchases-list','خریدها','Purchase invoices','فهرست فاکتورهای خرید','Purchase records','purchase_invoice'),
   leaf('purchase-settings','تنظیمات خرید','Purchase settings','قیمت خرید و تنظیمات بارکد','Purchase price and barcode settings'),
   leaf('purchase-return','برگشت از خرید','Purchase returns','برگشت به سند خرید مرجع','Return against original purchase','purchase_return'),
   leaf('payables','بدهی تأمین‌کنندگان','Supplier payables','ماندهٔ تأمین‌کنندگان','Supplier outstanding balances')]},
  {id:'treasury',fa:'دریافت و پرداخت',en:'Receipts & payments',items:[
   leaf('receipts','دریافت‌ها','Receipts','دریافت وجه و حساب مقصد','Receipts and destination account','receipt'),
   leaf('disbursements','پرداخت‌ها','Payments','پرداخت وجه و حساب مبدأ','Disbursements and funding source','disbursement'),
   leaf('cashboxes','صندوق‌ها','Cashboxes','صندوق، موجودی و گردش','Cash register records','cashbox'),
   leaf('bank-accounts','حساب‌های بانکی','Bank accounts','حساب، صاحب حساب، شعبه و مانده','Bank account catalog','bank_account'),
   leaf('cashbox-turnover','گردش صندوق','Cashbox turnover','واریز، برداشت و ماندهٔ سطری','Cash register statement'),
   leaf('transfers','انتقال وجه','Fund transfers','انتقال بین صندوق و بانک','Transfers between cash and bank')]},
  {id:'checks',fa:'چک‌ها',en:'Cheques',items:[
   leaf('cheques-in','چک‌های دریافتی','Received cheques','ثبت و پیگیری چک دریافتی','Received cheque tracking','cheque_in'),
   leaf('cheques-out','چک‌های پرداختی','Issued cheques','ثبت و پیگیری چک پرداختی','Issued cheque tracking','cheque_out'),
   leaf('cheques-status','وضعیت چک‌ها','Cheque statuses','پاس‌شده، در انتظار، پاس‌نشده و واگذارشده','Cleared, pending, returned and endorsed')]},
  {id:'expenses',fa:'هزینه‌ها',en:'Expenses',items:[
   leaf('expenses-list','هزینه‌ها','Expenses','هزینه، مبلغ، تاریخ و منبع پرداخت','Expense details and source','expense'),
   leaf('expense-groups','گروه هزینه','Expense categories','دسته‌بندی هزینه‌ها','Expense classification')]},
  {id:'books',fa:'حسابداری و دوره‌ها',en:'Accounting & periods',items:[
   {...leaf('ledger-core','کدینگ حساب‌ها و اسناد حسابداری','Chart of accounts & journal','ثبت دوبل و تراز آزمایشی','Double-entry ledger and trial balance'),ledger:true},
   leaf('fiscal-period','دوره مالی و بستن دوره','Fiscal periods & closing','دوره فعال، قفل و افتتاحیه','Fiscal periods, locks and opening balances'),
   leaf('opening','مانده‌های افتتاحیه','Opening balances','مانده اشخاص و صندوق و موجودی اولیه','Opening balances')]},
  {id:'tools',fa:'ابزارهای مالی',en:'Financial tools',items:[
   leaf('words','عدد به حروف','Number to words','تبدیل مبلغ به متن فارسی','Convert numbers to words'),
   leaf('bulk-prices','تغییر قیمت گروهی','Bulk price change','افزایش، کاهش و گردکردن قیمت','Bulk prices and rounding'),
   leaf('merge-invoices','تجمیع کالاهای چند فاکتور','Merge invoice items','ترکیب اقلام انتخابی','Aggregate selected invoice items'),
   leaf('db-stats','آمار دیتابیس','Database statistics','تعداد رکوردهای موجود','Record counts')]},
  {id:'settings',fa:'تنظیمات مالی',en:'Financial settings',items:[
   leaf('appearance','نمایش، فونت و ارقام','Display & numerals','فونت، اندازه و ارقام فارسی/انگلیسی','Typography and numeral preferences'),
   leaf('currency-calendar','واحد پول و تقویم','Currency & calendar','تومان/ریال و شمسی/میلادی','Currency and calendar display'),
   leaf('invoice-template','قالب و شماره‌گذاری فاکتور','Invoice templates','فروشنده، فاکتور فروش/خرید، پیش‌فاکتور، برگشت، مهر و امضا','Seller details, print layouts and numbering'),
   leaf('message-center','مرکز پیام','Message templates','قالب‌های فروش، خرید، دریافت و پرداخت','Communication templates'),
   leaf('finance-security','امنیت و سطح دسترسی','Finance permissions','مجوز ثبت، اصلاح، خروجی و دوره','Access, posting, export and closing permissions')]},
  {id:'services',fa:'حساب و خدمات',en:'Account & services',items:[
   leaf('user-profile','نمایه و حساب کاربری','Profile & account','نمایه، رمز ورود و مشخصات حساب','Profile and password'),
   leaf('messages','پیام‌ها','Messages','پیام‌های مربوط به حساب','Account messages'),
   leaf('subscriptions','اشتراک‌ها','Subscriptions','طرح‌های عرضه شده در آدین؛ نه اشتراک Company OS','Aadin plans, not Company OS billing'),
   leaf('addons','افزونه‌ها','Add-ons','فروشگاه، API، پیامک، چاپخانه و انبار اضافه','Online shop, API, SMS, print and extra inventory'),
   leaf('guides','راهنما و پشتیبانی','Help & support','مرکز راهنما و پشتیبانی','Help and support center'),
   leaf('maintenance','نگهداری و پشتیبان‌گیری','Maintenance & backups','حذف/صفرکردن و تصحیح داده فقط برای شناخت عنوان، نه اجرا','Reference only: destructive operations are NOT available')]}]},
 {id:'reports',fa:'گزارشات',en:'Reports',groups:[
  {id:'report-people',fa:'اشخاص',en:'Parties',items:[
   leaf('r-parties','گزارش اشخاص','Party report','تعداد، خرید، فروش، پرداخت، دریافت و مانده','Counts, sales, purchases and balances'),
   leaf('r-balances','بدهکاران و طلبکاران','Debtors & creditors','تعداد و مجموع بدهکار/طلبکار','Debt and credit balances')]},
  {id:'report-inventory',fa:'کالاها',en:'Inventory',items:[
   leaf('r-items','گزارش کالاها','Product report','موجودی، ورود، خروج، موجود/ناموجود','Stock, movements and availability'),
   leaf('r-alerts','هشدار موجودی و انقضا','Stock & expiry alerts','زیر حد مجاز و نزدیک انقضا','Low stock and approaching expiry')]},
  {id:'report-treasury',fa:'امور مالی',en:'Treasury & finance',items:[
   leaf('r-cash','گزارش صندوق و بانک','Cash & bank report','واریز، برداشت و مانده','Deposits, withdrawals and balances'),
   leaf('r-cheques','گزارش چک‌ها','Cheque report','وضعیت، جهت و سررسید','Cheque direction, due dates and statuses'),
   leaf('r-expenses','گزارش هزینه‌ها','Expense report','هزینه‌های ثبت‌شده به تفکیک دسته','Expenses by category')]},
  {id:'report-profit',fa:'سود و سرمایه',en:'Profit & capital',items:[
   leaf('r-profit','سود فروش','Sales profit','فروش، تخفیف، هزینه و سود','Sales, discounts, cost and profit'),
   leaf('r-capital','ارزش موجودی و سرمایه','Stock value & capital','ارزش انبار به قیمت خرید و فروش','Inventory values at purchase and sales prices'),
   {...leaf('r-trial','تراز آزمایشی','Trial balance','گزارش از دفتر دوبل موجود در Company OS','Current Company OS trial balance'),report:true},
   leaf('r-statements','ترازنامه و سود و زیان','Balance sheet & P&L','گزارش‌های استاندارد نیازمند نگاشت حساب','Financial statements requiring account mappings')]},
  {id:'report-export',fa:'خروجی گزارش‌ها',en:'Export',items:[
   leaf('r-export','خروجی Excel / PDF','Excel / PDF','ستون‌بندی، فیلتر و ترتیب گزارش','Filtered exports and column selection')]}]},
];
export const aadinLeaves=aadinAreas.flatMap(a=>a.groups.flatMap(g=>g.items));
