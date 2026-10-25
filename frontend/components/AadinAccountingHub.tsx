'use client';
import {useCallback,useEffect,useMemo,useState} from 'react';
import {BookOpen, ChevronDown,ChevronLeft, ChevronRight, Search,RefreshCcw,Plus, Trash2,FileSpreadsheet,ClipboardList,ShieldAlert,Wallet,Package,Users,ChartNoAxesCombined,LayoutDashboard,ArrowRight,Check,FileText} from 'lucide-react';
import {aadinAreas,aadinLeaves,type AadinLeaf} from '@/lib/aadin-menu';
import {Layers3, CircleDot} from 'lucide-react';
import {ops,opsAPI} from '@/lib/ops-api';
import {AccountingWorkspace} from './CompanyModules';
import AccountingOperations25,{isLiveAccountingScreen} from './AccountingOperations25';
import AccountingTools26,{hasAccountingTool} from './AccountingTools26';

type Lang='fa'|'en';
type Draft={id:number;kind:string;title:string;details:Record<string,string|number>;status:string;created_at:string};
type Trial={debits:number;credits:number;balanced:boolean;profit_loss:number;accounts:{id:number;name:string;code:string;debit:number;credit:number;balance:number}[]};
const icons={dashboard:LayoutDashboard,parties:Users,inventory:Package,operations:Wallet,reports:ChartNoAxesCombined};
const fields:{key:string;fa:string;en:string;type:'text'|'number'|'date'}[]=[
 {key:'reference',fa:'شماره مرجع',en:'Reference',type:'text'},
 {key:'party',fa:'طرف حساب (نام)',en:'Counterparty name',type:'text'},
 {key:'item_code',fa:'کد کالا',en:'Product code',type:'text'},
 {key:'group',fa:'گروه',en:'Group',type:'text'},
 {key:'contact',fa:'اطلاعات تماس عمومی',en:'Public contact',type:'text'},
 {key:'unit',fa:'واحد شمارش',en:'Unit',type:'text'},
 {key:'quantity',fa:'تعداد',en:'Quantity',type:'number'},
 {key:'unit_price',fa:'قیمت واحد (ریال)',en:'Unit price (IRR)',type:'number'},
 {key:'amount',fa:'مبلغ (ریال)',en:'Amount (IRR)',type:'number'},
 {key:'date',fa:'تاریخ',en:'Date',type:'date'},
 {key:'due_date',fa:'سررسید',en:'Due date',type:'date'},
 {key:'related_document',fa:'سند مرتبط (متن)',en:'Related document (text)',type:'text'},
 {key:'description',fa:'توضیحات',en:'Description',type:'text'}
];
const draftFields:Record<string,string[]>={
 person:['group','contact','description'],item:['item_code','group','unit','quantity','unit_price','description'],
 service:['item_code','unit','unit_price','description'],invoice_charge:['unit','unit_price','description'],
 sales_quote:['reference','party','date','amount','description'],sales_invoice:['reference','party','date','amount','description'],
 purchase_invoice:['reference','party','date','amount','description'],sales_return:['reference','related_document','date','amount','description'],
 purchase_return:['reference','related_document','date','amount','description'],receipt:['reference','party','date','amount','description'],
 disbursement:['reference','party','date','amount','description'],cashbox:['reference','description'],
 bank_account:['reference','description'],expense:['reference','group','date','amount','description'],
 cheque_in:['reference','party','amount','due_date','description'],cheque_out:['reference','party','amount','due_date','description'],
 customer_order:['reference','party','date','description'],catalog:['reference','description']
};

function translate(language:Lang,fa:string,en:string){return language==='fa'?fa:en}
function format(language:Lang,n:number){return Number(n||0).toLocaleString(language==='fa'?'fa-IR':'en-US')}

export default function AadinAccountingHub({language,onToast}:{language:Lang;onToast:(msg:string)=>void}){
 const [active,setActive]=useState('dashboard');
 const [opened,setOpened]=useState<string[]>(['dashboard','overview']);
 const [query,setQuery]=useState('');
 const [drafts,setDrafts]=useState<Draft[]>([]);
 const [title,setTitle]=useState('');
 const [details,setDetails]=useState<Record<string,string>>({});
 const [working,setWorking]=useState(false);
 const [canWrite,setCanWrite]=useState(false);
 const [editing,setEditing]=useState<number|null>(null);
 const [trial,setTrial]=useState<Trial|null>(null);
 const current=aadinLeaves.find(p=>p.id===active)||aadinLeaves[0];
 const area=aadinAreas.find(p=>p.groups.some(g=>g.items.some(it=>it.id===active)))||aadinAreas[0];
 const t=(fa:string,en:string)=>translate(language,fa,en);
 const toggle=(id:string)=>setOpened(s=>s.includes(id)?s.filter(x=>x!==id):[...s,id]);
 const choose=(id:string)=>{setActive(id);setQuery('');setTitle('');setDetails({});setEditing(null);const group=aadinAreas.flatMap(a=>a.groups).find(g=>g.items.some(i=>i.id===id));if(group)setOpened(old=>old.includes(group.id)?old:[...old,group.id])};
 const currency=format.bind(null,language);
 const loadingError=(e:unknown)=>onToast(e instanceof Error?e.message:t('اتصال با سرور برقرار نشد.','Could not reach the server.'));
 const load=useCallback(async(kind?:string)=>{
   try{
    if(kind){const data=await ops<{items:Draft[]}>(`/accounting/preparations?kind=${encodeURIComponent(kind)}`);setDrafts(data.items)}
    else {setDrafts([])}
   }catch(e){loadingError(e)}
 // Depend only on locale and callbacks outside to avoid requests on every render
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[language]);
 useEffect(()=>{void load(current.draftKind)},[current.draftKind,load]);
 useEffect(()=>{void opsAPI.me().then(me=>setCanWrite(['owner','admin','manager'].includes(me.role)||!!me.permissions?.finance?.write)).catch(()=>setCanWrite(false))},[]);
 useEffect(()=>{if(active==='dashboard'||active==='r-trial'){ops<Trial>('/ledger/reports/trial-balance').then(setTrial).catch(()=>setTrial(null))}},[active]);
 const allMatched=useMemo(()=>aadinLeaves.filter(x=>x.fa.includes(query)||x.en.toLowerCase().includes(query.toLowerCase())),[query]);
 const liveScreen=isLiveAccountingScreen(active);
 const supportScreen=hasAccountingTool(active);
 const canDraft=!!current.draftKind&&!liveScreen&&!supportScreen;
 const shownFields=draftFields[current.draftKind||'']||[];
 const reset=()=>{setTitle('');setDetails({});setEditing(null)};
 const submit=async(e:React.FormEvent)=>{
  e.preventDefault();if(!current.draftKind||!title.trim()||!canWrite)return;
  const cleaned:Record<string,string|number>={};
  for(const f of shownFields){const val=(details[f]||'').trim();if(!val)continue;const field=fields.find(x=>x.key===f);if(field?.type==='number'){const n=Number(val.replace(/[۰-۹]/g,c=>String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c))).replace(/[٠-٩]/g,c=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(c))));if(!Number.isFinite(n)||n<0){onToast(t('مقدار عددی نامعتبر است','Invalid numeric value'));return}cleaned[f]=n}else cleaned[f]=val}
  setWorking(true);
  try{
   await ops(`/accounting/preparations${editing?'/'+editing:''}`,{method:editing?'PATCH':'POST',body:JSON.stringify({kind:current.draftKind,title:title.trim(),details:cleaned})});
   reset();await load(current.draftKind);onToast(t('پیش‌نویس غیرمالی ذخیره شد','Non-posting draft saved'));
  }catch(error){loadingError(error)}finally{setWorking(false)}
 };
 const remove=async(id:number)=>{
  if(!window.confirm(t('این پیش‌نویس آرشیو شود؟','Archive this preparation?')))return;
  try{await ops(`/accounting/preparations/${id}`,{method:'DELETE'});await load(current.draftKind);onToast(t('به آرشیو منتقل شد','Archived'))}catch(e){loadingError(e)}
 };
 const groupedName=(g:{fa:string;en:string})=>language==='fa'?g.fa:g.en;
 const tabName=(g:AadinLeaf)=>language==='fa'?g.fa:g.en;
 const status=supportScreen?t('ابزارها و داده‌های سازمان','Organization data & tools'):liveScreen?t('عملیات مالی فعال (پایلوت)','Operational finance pilot'):canDraft?t('ثبت پیش‌نویس فعال','Draft storage available'):current.ledger||current.report?t('متصل به دفتر حسابداری','Connected to existing ledger'):t('طرح رابط و عنوان آماده','Navigation mapped');
 return <section className="aadin-workspace" aria-label={t('حسابداری Company OS','Company OS accounting')}>
  <header className="aadin-title">
   <div><div className="aadin-kicker">COMPANY OS / ACCOUNTING</div><h1>{t('حسابداری و مدیریت فروشگاه','Accounting & Store Management')}</h1><p>{t('چیدمان مبتنی بر عناوین مشاهده‌شده در گزارش آدین؛ با حفظ هویت و دسترسی‌های Company OS','Sections mapped from the supplied Aadin research report within the Company OS design system')}</p></div>
   <span className="aadin-period"><Wallet size={17}/>{t('بخش مالی سازمان','Organization finance')}</span>
  </header>
  <div className="aadin-top-nav" role="tablist" aria-label={t('بخش‌های اصلی حسابداری','Accounting areas')}>
   {aadinAreas.map(a=>{const Icon=icons[a.id as keyof typeof icons];const selected=area.id===a.id;return <button key={a.id} type="button" role="tab" aria-selected={selected} className={selected?'selected':''} onClick={()=>choose(a.groups[0].items[0].id)}><Icon size={18}/>{groupedName(a)}</button>})}
  </div>
  <div className="aadin-shell">
   <aside className="aadin-side" aria-label={t('زیرمنوهای حسابداری','Accounting submenu')}>
    <div className="aadin-side-search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} aria-label={t('جستجوی عنوان‌های حسابداری','Search accounting sections')} placeholder={t('جستجو در همه عنوان‌ها...','Search all sections...')}/></div>
    {query.trim()?<div className="aadin-side-group">{allMatched.map(item=><button key={item.id} className={`aadin-leaf ${active===item.id?'active':''}`} onClick={()=>choose(item.id)}>{tabName(item)}</button>)}{!allMatched.length&&<p className="aadin-muted">{t('عنوانی پیدا نشد','No matches')}</p>}</div>:
      aadinAreas.filter(a=>a.id===area.id).map(a=>a.groups.map(g=><div key={g.id} className="aadin-side-group">
       <button type="button" className={`aadin-group-label ${g.items.some(it=>it.id===active)?'selected':''}`} onClick={()=>toggle(g.id)} aria-expanded={opened.includes(g.id)} aria-controls={`aadin-group-${g.id}`}><span className="aadin-group-leading"><Layers3 size={15}/><span>{groupedName(g)}</span></span><span className="aadin-group-trailing"><small>{g.items.length.toLocaleString(language==='fa'?'fa-IR':'en-US')}</small><ChevronDown size={15} className={opened.includes(g.id)?'':'collapsed'}/></span></button>
       <div className="aadin-group-children" id={`aadin-group-${g.id}`} hidden={!opened.includes(g.id)}>{g.items.map(item=><button key={item.id} type="button" aria-current={active===item.id?'page':undefined} className={`aadin-leaf ${active===item.id?'active':''}`} onClick={()=>choose(item.id)}><CircleDot size={12}/><span>{tabName(item)}</span></button>)}</div>
      </div>))}
    <div className="aadin-source-note"><BookOpen size={16}/><span>{t('عناوین: گزارش آدین ۱۴۰۵/۲۰۲۶. نمایش منو به‌معنای پیاده‌سازی موتور مالی نیست.','Menu based on Aadin research. A visible section does not imply a working posting engine.')}</span></div>
   </aside>
   <main className="aadin-content">
    <div className="aadin-breadcrumb"><span>{groupedName(area)}</span>{language==='fa'?<ChevronLeft size={14}/>:<ChevronRight size={14}/>}<strong>{tabName(current)}</strong></div>
    <div className="aadin-heading"><div><h2>{tabName(current)}</h2><p>{language==='fa'?current.descFa:current.descEn}</p></div><span className={`aadin-status ${canDraft?'draft':current.ledger||current.report?'live':''}`}>{status}</span></div>
    {liveScreen?<AccountingOperations25 active={active} language={language} onToast={onToast} onNavigate={choose}/>:supportScreen?<AccountingTools26 active={active} language={language} onToast={onToast} onNavigate={choose}/>:current.ledger?<AccountingWorkspace language={language} onToast={onToast}/>:
     canDraft?<>
      <div className="aadin-notice"><ShieldAlert size={20}/><p><strong>{t('فرم پیش‌نویس آزمایشی','Preparation-only form')}</strong> {t('اطلاعات در پایگاه داده سازمان ذخیره می‌شود، اما هیچ فاکتور قطعی، پرداخت، تغییر موجودی یا ثبت حسابداری ایجاد نمی‌کند. برای مدارک و داده‌های حساس استفاده نشود.','Saved in your organization database, but DOES NOT post invoices, payments, stock movements or ledger entries. Do not include sensitive banking or identity data.')}</p></div>
      {canWrite?<form onSubmit={submit} className="aadin-form"><h3>{editing?t('ویرایش پیش‌نویس','Edit preparation'):t('ایجاد پیش‌نویس','New preparation')}</h3><label className="aadin-field"><span>{t('عنوان / نام','Title / name')} *</span><input required maxLength={180} value={title} onChange={e=>setTitle(e.target.value)} placeholder={tabName(current)}/></label>
       <div className="aadin-field-grid">{shownFields.map(f=>{const def=fields.find(x=>x.key===f)!;return <label className="aadin-field" key={f}><span>{language==='fa'?def.fa:def.en}</span><input type={def.type} min={def.type==='number'?0:undefined} step={def.type==='number'?'any':undefined} value={details[f]||''} onChange={e=>setDetails(s=>({...s,[f]:e.target.value}))} maxLength={def.type==='text'?500:undefined}/></label>})}</div>
       <div className="aadin-actions"><button type="submit" disabled={working} className="aadin-primary"><Check size={16}/>{working?t('در حال ذخیره...','Saving...'):editing?t('ذخیره ویرایش','Save changes'):t('ذخیره پیش‌نویس','Save preparation')}</button>{editing&&<button type="button" onClick={reset} className="aadin-quiet">{t('انصراف','Cancel')}</button>}</div>
      </form>:<p className="aadin-notice">{t('دسترسی شما فقط برای مشاهده است. ثبت و ویرایش پیش‌نویس به مجوز مدیر نیاز دارد.','You have read-only access. Ask an administrator for permission to create preparations.')}</p>}
      <div className="aadin-results"><div className="aadin-results-head"><h3>{t('پیش‌نویس‌های ذخیره‌شده','Saved preparations')} ({format(language,drafts.length)})</h3><button type="button" onClick={()=>void load(current.draftKind)} className="aadin-quiet"><RefreshCcw size={15}/>{t('تازه‌سازی','Refresh')}</button></div>
       {drafts.length?<div className="aadin-table-wrap"><table><thead><tr><th>{t('عنوان','Title')}</th><th>{t('شرح کوتاه','Details')}</th><th>{t('زمان','Created')}</th><th>{t('اقدامات','Actions')}</th></tr></thead><tbody>{drafts.map(d=><tr key={d.id}><td>{d.title}</td><td>{Object.entries(d.details).slice(0,3).map(([k,v])=>`${language==='fa'?(fields.find(f=>f.key===k)?.fa||k):(fields.find(f=>f.key===k)?.en||k)}: ${String(v)}`).join(' · ')||'—'}</td><td>{new Date(d.created_at).toLocaleDateString(language==='fa'?'fa-IR':'en-US')}</td><td><div className="aadin-actions">{canWrite&&<button type="button" onClick={()=>{setTitle(d.title);setDetails(Object.fromEntries(Object.entries(d.details).map(([k,v])=>[k,String(v)])));setEditing(d.id)}}>{t('ویرایش','Edit')}</button>}{canWrite&&<button type="button" onClick={()=>void remove(d.id)} aria-label={t('آرشیو پیش‌نویس','Archive preparation')}><Trash2 size={15}/></button>}</div></td></tr>)}</tbody></table></div>:<p className="aadin-empty">{t('هنوز پیش‌نویسی ثبت نشده است.','No saved preparations yet.')}</p>}
      </div>
     </>:
     current.report||active==='dashboard'?<div className="aadin-results"><h3>{t('خلاصه دفتر حسابداری موجود','Existing ledger summary')}</h3>{trial?<><div className="aadin-kpis"><div><span>{t('جمع بدهکار','Total debit')}</span><strong>{currency(trial.debits)} IRR</strong></div><div><span>{t('جمع بستانکار','Total credit')}</span><strong>{currency(trial.credits)} IRR</strong></div><div><span>{t('تراز دفتر','Balanced')}</span><strong>{trial.balanced?'✓':'!'}</strong></div></div><p className="aadin-muted">{t('این اعداد فقط از اسناد قطعی دفتر دوبل فعلی Company OS هستند؛ نماینده کل فروش و موجودی آدین نیستند.','Figures reflect only posted entries in the existing Company OS ledger, not Aadin sales or inventory.')}</p></>:<p>{t('برای مشاهده آمار، API را اجرا کنید.','Start the API to retrieve ledger metrics.')}</p>}</div>:
     <div className="aadin-coming"><ClipboardList size={36}/><h3>{t('ساختار این صفحه از گزارش آدین ثبت شده است','This page is mapped from the Aadin report')}</h3><p>{t('عنوان، جایگاه منو و کاربرد صفحه مشخص است. موتور مالی، محاسبات و گردش کاری این بخش هنوز پیاده‌سازی یا آزموده نشده و عمداً دکمهٔ عملیاتی نمایشی ندارد.','The title, menu placement and purpose are mapped. Its accounting logic and business workflow are not yet implemented or tested; no misleading operation controls are shown.')}</p><span>{t('مرحله بعد: مدل داده، قواعد مالی، API و آزمون پذیرش','Next: data models, financial rules, APIs, and acceptance tests')}</span></div>}
   </main>
  </div>
 </section>
}
