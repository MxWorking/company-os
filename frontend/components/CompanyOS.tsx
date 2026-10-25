'use client';

import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {localize,localNumber,localDate} from '@/lib/i18n';
import PersonnelWorkspace from './PersonnelWorkspace';
import AadinAccountingHub from './AadinAccountingHub';
import SignInLanding from './SignInLanding';
import FinanceRequests from './FinanceRequests';
import ManagerOverview from './ManagerOverview';
import OperationsWorkspace from './OperationsWorkspace';
import {ProjectHub,NotesWorkspace,CollaborationWorkspace,SupportWorkspace,AccountWorkspace} from './CompanyModules';
import {opsAPI,ops} from '@/lib/ops-api';
import type {OSUser} from '@/lib/ops-api';
import {
 Activity as ActivityIcon, AlertCircle, AlertTriangle, ArrowLeft, ArrowRight, BarChart3, Bell, BookOpen, Bot, Calendar,
 Check, CheckCircle2, CheckSquare, ChevronDown, ChevronLeft, CircleHelp, Clock, CreditCard, FileText, Folder,
 Headphones, Home, LogOut, Menu, MessageSquare, Moon, MoreHorizontal, Plus, Search, Settings, ShieldCheck,
 ShoppingCart, Sparkles, Sun, Target, TrendingUp, Users, Wallet, X, Zap, Send, Trash2, Pencil, Loader2
} from 'lucide-react';
import {Area,AreaChart,Bar,CartesianGrid,ComposedChart,Cell,Legend,Pie,PieChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {demo,moduleFixtures} from '@/lib/demo';
import {ApiError,endpoints} from '@/lib/api';
import type {Approval,Dashboard,ModuleItem,ModuleKey,Project,Task} from '@/lib/types';

type Language='fa'|'en';
type ModalKind='projects'|'tasks'|'approvals'|'documents'|'procurement'|'hr'|'knowledge'|'support'|null;
type IconElement=typeof Home;
const navigation:{key:ModuleKey;fa:string;en:string;icon:IconElement;access?:string}[]=[
 {key:'dashboard',fa:'داشبورد',en:'Dashboard',icon:Home},
 {key:'my-work',fa:'وظایف من',en:'My Tasks',icon:CheckSquare,access:'work'},
 {key:'work',fa:'وظایف و بوردها',en:'Tasks & Boards',icon:Folder,access:'work'},
 {key:'project-hub',fa:'فضای پروژه‌ها',en:'Project Workspace',icon:Folder,access:'work'},
 {key:'organization',fa:'سازمان و اعضا',en:'Organization & Members',icon:ShieldCheck,access:'organization'},
 {key:'hr-advanced',fa:'منابع انسانی و پرسنل',en:'HR & Personnel',icon:Users,access:'hr'},
 {key:'hr',fa:'قرارداد و مرخصی',en:'Contracts & Leave',icon:FileText,access:'hr'},
 {key:'crm',fa:'مشتریان و فروش',en:'CRM & Sales',icon:Target,access:'crm'},
 {key:'company-chat',fa:'گفتگوی عمومی',en:'Company Chat',icon:MessageSquare,access:'collaboration'},
 {key:'collaboration',fa:'کانال‌ها و جلسات',en:'Channels & Meetings',icon:MessageSquare,access:'collaboration'},
 {key:'correspondence',fa:'نامه‌ها و اسناد',en:'Letters & Documents',icon:FileText,access:'documents'},
 {key:'notes',fa:'یادداشت‌های من',en:'My Notes',icon:BookOpen,access:'notes'},
 {key:'finance-requests',fa:'درخواست‌های مالی',en:'Finance Requests',icon:MessageSquare},
 {key:'accounting',fa:'حسابداری و امور مالی',en:'Accounting & Finance',icon:Wallet,access:'finance'},
 {key:'time-tracking',fa:'فاکتور و زمان‌کاری',en:'Invoices & Timesheets',icon:Clock,access:'finance'},
 {key:'intelligence',fa:'گزارش‌ها و اتوماسیون',en:'Reports & Automation',icon:ActivityIcon,access:'intelligence'},
 {key:'assistant',fa:'دستیار هوشمند',en:'AI Assistant',icon:Bot,access:'work'},
 {key:'helpdesk',fa:'راهنما و پشتیبانی',en:'Help & Support',icon:Headphones,access:'support'},
 {key:'account',fa:'حساب و دسترسی‌ها',en:'Account & Access',icon:ShieldCheck},
 {key:'settings',fa:'تنظیمات ظاهر',en:'Appearance Settings',icon:Settings},
];
const sidebarGroups:{id:string;fa:string;en:string;icon:IconElement;keys:ModuleKey[]}[]=[
 {id:'tasks',fa:'وظایف',en:'Tasks',icon:CheckSquare,keys:['my-work','work']},
 {id:'projects',fa:'پروژه‌ها',en:'Projects',icon:Folder,keys:['project-hub']},
 {id:'org',fa:'سازمان',en:'Organization',icon:Users,keys:['organization','hr-advanced','hr','crm']},
 {id:'collab',fa:'همکاری و ارتباطات',en:'Collaboration',icon:MessageSquare,keys:['company-chat','collaboration','correspondence','notes']},
 {id:'money',fa:'مالی و حسابداری',en:'Finance',icon:Wallet,keys:['finance-requests','accounting','time-tracking']},
 {id:'insight',fa:'گزارش و هوشمندسازی',en:'Insights & AI',icon:ActivityIcon,keys:['intelligence','assistant']},
 {id:'service',fa:'حساب و پشتیبانی',en:'Account & Help',icon:Settings,keys:['account','helpdesk','settings']},
];

const words={fa:{hello:'سلام حسین عزیز',tag:'امروز روزی ویژه برای پیشرفت پروژه‌ها و تحقق اهداف است.',newItem:'ایجاد مورد جدید',today:'گزارش امروز',projects:'پروژه‌های فعال',tasks:'وظایف در جریان',approvals:'درخواست‌های تأیید',expenses:'هزینه‌های جاری',financial:'عملکرد مالی / روند ماهانه',status:'وضعیت پروژه‌ها',keyProjects:'پروژه‌های کلیدی',attention:'موارد نیازمند توجه',recent:'فعالیت‌های اخیر',assistant:'دستیار هوشمند AI',assistantDesc:'از اطلاعات سازمان بپرسید. در حالت فعلی تحلیل آماری ساده فعال است.',all:'مشاهده همه',manager:'مدیر پروژه',deadline:'تاریخ تحویل',progress:'پیشرفت',state:'وضعیت',project:'نام پروژه',active:'پروژه فعال',revenue:'درآمد',cost:'هزینه',profit:'سود خالص',message:'سؤال خود را بنویسید...',search:'جستجو در پروژه‌ها، وظایف، اسناد، افراد و ...',welcome:'نمای کلی و عملکرد سازمان شما',login:'ورود مدیر',logout:'خروج',empty:'موردی برای نمایش وجود ندارد',preview:'حالت پیش‌نمایش؛ داده‌ها نمونه هستند'},en:{hello:'Welcome back, Hossein',tag:'Today is a great day to move your projects forward.',newItem:'Create new',today:'Today’s report',projects:'Active projects',tasks:'Open tasks',approvals:'Approvals needed',expenses:'Current expenses',financial:'Financial performance / Monthly trend',status:'Project status',keyProjects:'Key projects',attention:'Needs attention',recent:'Recent activity',assistant:'AI Assistant',assistantDesc:'Ask about your work, data, and reports.',all:'View all',manager:'Manager',deadline:'Due date',progress:'Progress',state:'Status',project:'Project',active:'Active projects',revenue:'Revenue',cost:'Expenses',profit:'Net profit',message:'Ask a question...',search:'Search projects, tasks, people...',welcome:'A snapshot of your organization',login:'Admin login',logout:'Logout',empty:'Nothing to show',preview:'Preview mode; sample data'}};


function Logo(){return <div className="brand-icon" aria-hidden="true"><span /></div>}
function MiniLine({color='#08ddcb',up=true}:{color?:string;up?:boolean}){return <svg className="mini-line" viewBox="0 0 88 33" fill="none" aria-hidden="true"><path d={up?'M2 26 17 20 26 23 39 10 54 17 70 4 85 11':'M2 25 17 14 29 22 43 19 56 23 71 13 85 5'} stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/><path d={up?'M2 26 17 20 26 23 39 10 54 17 70 4 85 11V33H2Z':'M2 25 17 14 29 22 43 19 56 23 71 13 85 5V33H2Z'} fill={color} opacity=".09" /></svg>}
function MiniBars({color}:{color:string}){return <div className="mini-bars">{[18,27,43].map((h,i)=><span key={i} style={{height:h,background:`linear-gradient(0deg, ${color}, color-mix(in srgb, ${color} 35%, white))`}} />)}</div>}
function StatusPill({value,language}:{value:string;language:Language}){return <span className={`status-pill ${value.includes('ریسک')||value.includes('تأخیر')?'risk':value.includes('تکمیل')||value.includes('انجام شده')||value.includes('تأیید شده')?'done':'active'}`}>{localize(value,language)}</span>}
function Panel({title,action,children,className=''}:{title:string;action?:React.ReactNode;children:React.ReactNode;className?:string}){return <section className={`panel ${className}`}><header className="panel-head"><h2>{title}</h2>{action}</header>{children}</section>}

export default function CompanyOS(){
 const [theme,setTheme]=useState<'light'|'dark'>('dark');
 const [language,setLanguage]=useState<Language>('fa');
 const [section,setSection]=useState<ModuleKey>('dashboard');
 const [currentUser,setCurrentUser]=useState<OSUser|null>(null);
 const [expandedGroups,setExpandedGroups]=useState<string[]>(['tasks','projects']);
 const [dashboard,setDashboard]=useState<Dashboard>(demo);
 const [items,setItems]=useState<Partial<Record<ModuleKey,ModuleItem[]>>>(moduleFixtures);
 const [apiReady,setApiReady]=useState(false);
 const [auth,setAuth]=useState<'loading'|'required'|'authenticated'>('loading');
 const [login,setLogin]=useState({username:'',password:''});
 const [sidebarOpen,setSidebarOpen]=useState(false);
 const [landingMenuOpen,setLandingMenuOpen]=useState(false);
 const [entered,setEntered]=useState(false);
 const [notifs,setNotifs]=useState(false);
 const [selectedApproval,setSelectedApproval]=useState<Approval|null>(null);
 const [search,setSearch]=useState('');
 const [modal,setModal]=useState<ModalKind>(null);
 const [editing,setEditing]=useState<number|null>(null);
 const [form,setForm]=useState({title:'',manager:'',progress:'0',due_date:'',description:'',priority:'متوسط'});
 const [toast,setToast]=useState('');
 const [period,setPeriod]=useState('6');
 const [question,setQuestion]=useState('');
 const [assistantMessages,setAssistantMessages]=useState<{role:'user'|'assistant';text:string}[]>([]);
 const [submitting,setSubmitting]=useState(false);
 const searchRef=useRef<HTMLInputElement>(null);
 const t=words[language];
 const rtl=language==='fa';
 const tx=(v:string|number|null|undefined)=>localize(v,language);
 const fmt=(v:number)=>localNumber(v,language);
 const reveal=(msg:string)=>{setToast(tx(msg));window.setTimeout(()=>setToast(''),3600)};

 const refresh=useCallback(async()=>{
  try{const data=await endpoints.dashboard();setDashboard(data);setApiReady(true)}catch{setApiReady(false)}
 },[]);
 useEffect(()=>{
  const s=localStorage.getItem('companyos-theme');setTheme(s==='light'?'light':'dark');
  const lng=localStorage.getItem('companyos-language');if(lng==='en')setLanguage('en');
  void opsAPI.me().then(user=>{setCurrentUser(user);setAuth('authenticated');setSection(['owner','admin','manager'].includes(user.role)?'dashboard':'my-work');if(['owner','admin'].includes(user.role))void refresh()}).catch(()=>{setCurrentUser(null);setAuth('required')});
 },[refresh]);
 useEffect(()=>{document.documentElement.setAttribute('data-theme',theme);localStorage.setItem('companyos-theme',theme)},[theme]);
 useEffect(()=>{document.documentElement.lang=language;document.documentElement.dir=rtl?'rtl':'ltr';localStorage.setItem('companyos-language',language)},[language,rtl]);
 useEffect(()=>{const listener=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();searchRef.current?.focus()}if(e.key==='Escape'){setModal(null);setSearch('');setNotifs(false);setSidebarOpen(false);setLandingMenuOpen(false)}};window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener)},[]);
 useEffect(()=>{if(!sidebarOpen)return;const previous=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=previous}},[sidebarOpen]);
 useEffect(()=>{if(!apiReady)return; if(section==='projects'){endpoints.projects().then(projects=>setDashboard(d=>({...d,projects}))).catch(()=>{});}else if(section==='tasks'){endpoints.tasks().then(tasks=>setDashboard(d=>({...d,tasks}))).catch(()=>{});}else if(section!=='dashboard'&&section!=='finance'&&section!=='assistant'&&section!=='hr'&&!['my-work','organization','work','hr','collaboration','correspondence','crm','time-tracking','intelligence'].includes(section)){endpoints.items(section).then(v=>setItems(current=>({...current,[section]:v}))).catch(()=>{});}},[apiReady,section]);
 const allowed=(key:ModuleKey)=>{if(key==='finance-requests')return !!currentUser;if(key==='dashboard')return !!currentUser&&['owner','admin','manager'].includes(currentUser.role);const item=navigation.find(n=>n.key===key);if(!item||!item.access)return true;if(item.access==='legacy')return !!currentUser&&['owner','admin'].includes(currentUser.role);return !!currentUser?.permissions?.[item.access]?.read||!!currentUser&&['owner','admin'].includes(currentUser.role)};
 const toggleGroup=(id:string)=>setExpandedGroups(a=>a.includes(id)?a.filter(x=>x!==id):[...a,id]);
 const filteredProjects=useMemo(()=>dashboard.projects.filter(p=>`${tx(p.name)} ${tx(p.manager)}`.toLowerCase().includes(search.toLowerCase())),[dashboard.projects,search]);
 const filteredTasks=useMemo(()=>dashboard.tasks.filter(x=>`${tx(x.title)} ${x.assignee}`.toLowerCase().includes(search.toLowerCase())),[dashboard.tasks,search]);
 const nav=(key:ModuleKey)=>{if(!allowed(key)){reveal(rtl?'دسترسی به این بخش برای حساب شما فعال نشده است.':'This section is not allowed for your account.');return}const group=sidebarGroups.find(g=>g.keys.includes(key));if(group)setExpandedGroups(a=>a.includes(group.id)?a:[...a,group.id]);setSection(key);setSearch('');setSidebarOpen(false)};
 const startCreate=(kind:ModalKind,id:number|null=null)=>{
  setEditing(id);const p=kind==='projects'&&id?dashboard.projects.find(x=>x.id===id):undefined;
  const tk=kind==='tasks'&&id?dashboard.tasks.find(x=>x.id===id):undefined;
  const other=kind&&id?(items[kind as ModuleKey]||[]).find(x=>x.id===id):undefined;
  setForm({title:p?.name||tk?.title||other?.title||'',manager:p?.manager||tk?.assignee||'',progress:p?String(p.progress):'0',due_date:p?.deadline||tk?.due_date||'',description:p?.description||other?.subtitle||'',priority:tk?.priority||'متوسط'});setModal(kind);
 };
 const save=async(e:React.FormEvent)=>{
  e.preventDefault();if(!modal||!form.title.trim())return;
  if(!apiReady){reveal('برای ذخیره دائمی ابتدا FastAPI را اجرا کنید.');return;}
  setSubmitting(true);
  const collection=modal==='projects'?'projects':modal==='tasks'?'tasks':modal==='approvals'?'approvals':`modules/${modal}`;
  const payload=modal==='projects'?{name:form.title,manager:form.manager||'مدیر پروژه',progress:Number(form.progress),deadline:form.due_date||'تعیین نشده',status:'در حال اجرا'}:modal==='tasks'?{title:form.title,assignee:form.manager||'تعیین نشده',priority:form.priority,due_date:form.due_date||'تعیین نشده',status:'در انتظار',project_id:null}:modal==='approvals'?{title:form.title,subtitle:form.description||'درخواست جدید',severity:'medium',status:'در انتظار'}:{title:form.title,subtitle:form.description,status:'جدید'};
  try{if(editing)await endpoints.patch(collection,editing,payload);else await endpoints.create(collection,payload);await refresh();if(modal==='projects'){const projects=await endpoints.projects();setDashboard(d=>({...d,projects}));}if(modal==='tasks'){const tasks=await endpoints.tasks();setDashboard(d=>({...d,tasks}));}if(!['projects','tasks','approvals'].includes(modal)){const newItems=await endpoints.items(modal as ModuleKey);setItems(a=>({...a,[modal]:newItems}))}setModal(null);reveal('اطلاعات با موفقیت ذخیره شد.')}catch(err){reveal(err instanceof Error?err.message:'خطا در ذخیره اطلاعات')}finally{setSubmitting(false)}
 };
 const processApproval=async(status:'تأیید شده'|'رد شده')=>{if(!selectedApproval)return;if(!apiReady){reveal('برای ثبت تصمیم ابتدا FastAPI را اجرا کنید.');return}try{await endpoints.patch('approvals',selectedApproval.id,{status});await refresh();setSelectedApproval(null);reveal('وضعیت درخواست به‌روزرسانی شد.')}catch{reveal('ثبت تصمیم انجام نشد.')}};
 const remove=async(kind:string,id:number)=>{if(!apiReady){reveal('حذف فقط در حالت اتصال به سرور امکان‌پذیر است.');return}if(!window.confirm(tx('این مورد حذف شود؟')))return;try{await endpoints.remove(kind,id);await refresh();reveal('مورد حذف شد.')}catch{reveal('حذف انجام نشد.')}};
 const respond=async(e?:React.FormEvent)=>{e?.preventDefault();if(!question.trim())return;const q=question.trim();setQuestion('');setAssistantMessages(a=>[...a,{role:'user',text:q}]);setSubmitting(true);
  try{if(!apiReady)throw new Error('offline');const r=await opsAPI.assistant(q);setAssistantMessages(a=>[...a,{role:'assistant',text:r.answer}])}catch{setAssistantMessages(a=>[...a,{role:'assistant',text:tx('در حالت پیش‌نمایش، دستیار به API متصل نیست. پس از اجرای بک‌اند، پاسخ‌های آماری مبتنی بر داده فعال می‌شوند. اتصال مدل زبانی واقعی نیازمند تنظیم جداگانه است.')}])}finally{setSubmitting(false)}
 };
 const quickAsk=(q:string)=>{setQuestion(q);document.getElementById('assistant-query')?.focus()};
 const handleSignIn=(user:OSUser)=>{setCurrentUser(user);setAuth('authenticated');setEntered(true);setSection(['owner','admin','manager'].includes(user.role)?'dashboard':'my-work');setApiReady(true);if(['owner','admin'].includes(user.role))void refresh()};
 const handleSignOut=async()=>{try{await ops('/auth/logout',{method:'POST'});setAuth('required');setCurrentUser(null);setEntered(false);setApiReady(false);setDashboard(demo);setAssistantMessages([]);setSection('dashboard')}catch{reveal(rtl?'خروج انجام نشد. اتصال به سرور را بررسی کنید.':'Sign-out failed. Check your connection.')}};
 const stats=dashboard.stats;
 const trend=(period==='3'?stats.trend.slice(-3):stats.trend).map(point=>({...point,month:tx(point.month)}));
 const statCards=[{label:t.expenses,value:`${fmt(Math.round(stats.expenses/1000000))}M`,change:tx(stats.expense_change),icon:Wallet,color:'cyan',chart:'line'},{label:t.approvals,value:fmt(stats.approvals),change:tx(stats.approval_change),icon:Target,color:'red',chart:'line'},{label:t.tasks,value:fmt(stats.tasks),change:tx(stats.task_change),icon:CheckSquare,color:'blue',chart:'bars'},{label:t.projects,value:fmt(stats.projects),change:tx(stats.project_change),icon:Calendar,color:'purple',chart:'bars'}];
 const activeNav=navigation.find(n=>n.key===section)!;
 if(auth!=='authenticated'||!currentUser)return <SignInLanding language={language} setLanguage={setLanguage} theme={theme} setTheme={setTheme} onSuccess={handleSignIn} loading={auth==='loading'}/>;
 return <div className={`site-root locale-${language}`} dir={rtl?'rtl':'ltr'}>
  <div className="app-shell" id="workspace" dir={rtl?'rtl':'ltr'}>
  {sidebarOpen&&<div className="sidebar-scrim" aria-hidden="true" onClick={()=>setSidebarOpen(false)} />}
  <aside id="companyos-sidebar" className={`sidebar ${sidebarOpen?'open':''}`} aria-label={tx("ناوبری اصلی")}>
    <button type="button" className="sidebar-close icon-button" onClick={()=>setSidebarOpen(false)} aria-label={rtl?'بستن فهرست':'Close menu'}><X size={19}/></button>
    <div className="brand" onClick={()=>nav('dashboard')} role="button" tabIndex={0} onKeyDown={e=>e.key==='Enter'&&nav('dashboard')}><Logo/><div><strong>Company OS</strong><small>{tx("سامانه جامع مدیریت سازمان")}</small></div></div>
    <div className="sidebar-user-card"><span className="sidebar-user-avatar">{currentUser.name.slice(0,1).toUpperCase()}</span><span className="sidebar-user-info"><strong>{currentUser.name}</strong><small>{currentUser.role}</small></span><button type="button" className="sidebar-user-action" onClick={()=>nav('account')} aria-label={rtl?'حساب کاربری':'Account'}><Settings size={16}/></button></div>
    <nav className="side-links grouped-sidebar" aria-label={rtl?'بخش‌های سازمان':'Workspace groups'}>
      {allowed('dashboard')&&<button type="button" className={`side-link ${section==='dashboard'?'selected':''}`} onClick={()=>nav('dashboard')}><Home size={19}/><span>{rtl?'داشبورد':'Dashboard'}</span></button>}
      {sidebarGroups.map(group=>{const entries=group.keys.map(key=>navigation.find(n=>n.key===key)).filter((x):x is typeof navigation[number]=>!!x&&allowed(x.key));if(!entries.length)return null;const Icon=group.icon;const open=expandedGroups.includes(group.id);return <div className="side-group" key={group.id}><button type="button" className={`side-group-toggle ${entries.some(e=>e.key===section)?'group-active':''}`} onClick={()=>toggleGroup(group.id)} aria-expanded={open}><Icon size={19}/><span>{rtl?group.fa:group.en}</span><ChevronDown size={16} className={open?'rotated':''}/></button>{open&&<div className="side-submenu">{entries.map(({key,fa,en,icon:SubIcon})=><button key={key} type="button" className={`side-link side-sub ${section===key?'selected':''}`} onClick={()=>nav(key)}><SubIcon size={16}/><span>{rtl?fa:en}</span></button>)}</div>}</div>})}
    </nav>
    <div className="side-bottom"><span className="side-live"><span className="live-dot"/>{apiReady?'API Connected':t.preview}</span><button className="side-link" onClick={()=>{void handleSignOut()}}><LogOut size={18}/>{t.logout}</button></div>
  </aside>

  <div className="workarea">
   <header className="topbar">
    <div className="header-right"><button className="mobile-menu icon-button" aria-label={tx("باز کردن منو")} aria-expanded={sidebarOpen} aria-controls="companyos-sidebar" onClick={()=>setSidebarOpen(true)}><Menu size={22}/></button><div className="searchbox"><Search size={18}/><input ref={searchRef} value={search} onChange={e=>setSearch(e.target.value)} placeholder={t.search} aria-label={t.search}/><kbd>Ctrl K</kbd></div></div>
    <div className="header-left"><div className="language-switch" role="group" aria-label="Language"><button className={language==='fa'?'on':''} onClick={()=>setLanguage('fa')}>FA</button><button className={language==='en'?'on':''} onClick={()=>setLanguage('en')}>EN</button></div><button className="theme-button icon-button" title={tx(theme==='dark'?'تم روشن':'تم تاریک')} aria-label={tx("تغییر تم")} onClick={()=>setTheme(theme==='dark'?'light':'dark')}>{theme==='dark'?<Moon size={21}/>:<Sun size={21}/>}</button><div className="notification-wrap"><button className="icon-button" title={tx("اعلان‌ها")} onClick={()=>setNotifs(!notifs)} aria-label={tx("اعلان‌ها")}><Bell size={20}/><i className="notification-dot"/></button>{notifs&&<div className="notification-popup"><strong>{tx("اعلان‌های سازمان")}</strong>{dashboard.approvals.slice(0,3).map(a=><button key={a.id} onClick={()=>{setSelectedApproval(a);setNotifs(false)}}><AlertCircle size={16}/><span>{tx(a.title)}</span></button>)}<button onClick={()=>{nav('settings');setNotifs(false)}}>{tx("تنظیمات اعلان‌ها")}</button></div>}</div><button className="avatar" aria-label={tx("پروفایل")} onClick={()=>nav('account')}>{currentUser.name.slice(0,1).toUpperCase()}</button></div>
   </header>
   <main className="main-content">
    {section==='dashboard'&&!!currentUser&&['owner','admin'].includes(currentUser.role)?<>
     <section className="hero"><div className="hero-copy"><h1><span className="sun-emoji">☀️</span>{t.hello}</h1><p>{t.tag}</p><div className="hero-actions"><button className="primary-btn" onClick={()=>nav('project-hub')}><Plus size={17}/>{t.newItem}</button><button className="outline-btn" onClick={()=>{document.getElementById('analytics')?.scrollIntoView({behavior:'smooth'});reveal('گزارش مالی و وضعیت پروژه‌ها در پایین صفحه قرار دارد.')}}><CircleHelp size={16}/>{t.today}</button><span className="today-date">{localDate(language)}</span></div></div></section>
     <section className="stat-grid" aria-label={tx("شاخص‌های اصلی")}>{statCards.map((item,index)=>{const Icon=item.icon;return <div className={`stat-card ${item.color}`} key={index}><div className="stat-upper"><span className="stat-label">{item.label}</span><span className="stat-icon"><Icon size={20}/></span></div><div className="stat-number">{item.value}</div><div className="stat-bottom"><strong className={item.change.startsWith('-')?'negative':'positive'}>{item.change}</strong>{item.chart==='bars'?<MiniBars color={index===2?'#14adff':'#7752ff'}/>:<MiniLine color={index===1?'#ff3653':'#04d4de'} up={index!==1}/>}</div></div>})}</section>
     <section className="analytics-grid" id="analytics"><Panel className="project-status" title={t.status}><div className="status-content"><div className="status-legend">{stats.statuses.map(s=><div key={s.label}><span className="legend-dot" style={{background:s.color}}/><span>{tx(s.label)}</span><strong>{fmt(s.count)}</strong></div>)}</div><div className="donut-holder"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={stats.statuses} innerRadius="66%" outerRadius="90%" dataKey="count" stroke="none" startAngle={90} endAngle={-270}>{stats.statuses.map((s,i)=><Cell key={i} fill={s.color}/>)}</Pie></PieChart></ResponsiveContainer><div className="donut-middle"><b>{fmt(stats.projects)}</b><small>{t.active}</small></div></div></div></Panel>
      <Panel className="finance-chart" title={t.financial} action={<select className="period-select" value={period} onChange={e=>setPeriod(e.target.value)} aria-label={tx("بازه زمانی")}><option value="6">{tx("۶ ماه گذشته")}</option><option value="3">{tx("۳ ماه گذشته")}</option></select>}><div className="chart-area" dir="ltr"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={trend} margin={{top:11,right:1,left:-14,bottom:0}}><defs><linearGradient id="blueCol" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#20d0ff"/><stop offset="100%" stopColor="#2778ff"/></linearGradient><linearGradient id="violetCol" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#a88aff"/><stop offset="100%" stopColor="#6d3bf9"/></linearGradient></defs><CartesianGrid stroke="var(--grid-line)" strokeDasharray="3 3" vertical={true}/><XAxis dataKey="month" tick={{fill:'var(--muted)',fontSize:10}} axisLine={false} tickLine={false}/><YAxis tickFormatter={(value:number)=>`${value}M`} domain={[0,80]} tick={{fill:'var(--muted)',fontSize:10}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{borderRadius:12,background:'var(--tooltip-bg)',border:'1px solid var(--panel-border)',color:'var(--text)'}} formatter={(value,name)=>[`${value}M`,name==='income'?t.revenue:name==='expense'?t.cost:t.profit]}/><Bar dataKey="income" barSize={18} fill="url(#blueCol)" radius={[3,3,0,0]}/><Bar dataKey="expense" barSize={18} fill="url(#violetCol)" radius={[3,3,0,0]}/><Area type="monotone" dataKey="profit" stroke="#a24aff" strokeWidth={2} fill="transparent" dot={{fill:'#7538ff',r:3}}/></ComposedChart></ResponsiveContainer></div><div className="chart-legend"><span><i className="legend-dot" style={{background:'#20adff'}}/>{t.profit}</span><span><i className="legend-dot" style={{background:'#8754fa'}}/>{t.cost}</span><span><i className="legend-dot" style={{background:'#13d2bc'}}/>{t.revenue}</span></div></Panel></section>
     <section className="lists-grid"><Panel title={t.attention} className="attention-panel" action={<button className="small-danger" onClick={()=>nav('my-work')}>{fmt(dashboard.approvals.length)} {tx("مورد مهم")}</button>}><div className="attention-list">{dashboard.approvals.slice(0,4).map((v,i)=>{const icons=[AlertTriangle,Target,AlertCircle,Calendar];const Icon=icons[i%4];return <button className="attention-item" key={v.id} onClick={()=>setSelectedApproval(v)}><span className={`attention-mark m${i}`}><Icon size={21}/></span><div><strong>{tx(v.title)}</strong><small>{tx(v.subtitle)}</small></div><i className={`risk-indicator r${i}`}/></button>})}</div></Panel>
      <Panel title={t.keyProjects} className="key-projects" action={<button className="view-all" onClick={()=>nav('project-hub')}>{t.all}</button>}><div className="table-wrap"><table className="projects-table"><thead><tr><th>{t.project}</th><th>{t.state}</th><th>{t.progress}</th><th>{t.deadline}</th><th>{t.manager}</th></tr></thead><tbody>{filteredProjects.slice(0,4).map(p=><tr key={p.id} onClick={()=>nav('project-hub')}><td className="project-name">{tx(p.name)}</td><td><StatusPill value={p.status} language={language}/></td><td><div className="progress-field"><span>{fmt(p.progress)}{tx("٪")}</span><i className="progress-track"><i style={{width:`${p.progress}%`}}/></i></div></td><td className="date-cell">{tx(p.deadline)}</td><td><div className="manager"><span className="person-avatar" style={{background:p.color||'#5e62e8'}}>{rtl?p.initials:tx(p.manager).split(' ').map(n=>n[0]).join('').slice(0,2)}</span>{tx(p.manager)}</div></td></tr>)}</tbody></table></div></Panel></section>
     <section className="bottom-grid"><Panel title={t.recent} className="activity-panel" action={<button className="view-all" onClick={()=>nav('correspondence')}>{t.all}</button>}><div className="activities">{dashboard.activities.slice(0,4).map((a,i)=>{const Icon=[FileText,CheckSquare,MessageSquare,Calendar][i%4];return <div key={a.id} className="activity-row"><span className={`activity-icon ac${i}`}><Icon size={15}/></span><div><b>{tx(a.title)}</b><small>{tx(a.detail)}</small></div><time>{tx(a.time)}</time></div>})}</div></Panel>
</section>
     </>:section==='dashboard'&&currentUser?.role==='manager'?<ManagerOverview language={language} onOpen={nav}/>:section==='dashboard'?<OperationsWorkspace key="secure-home" myWork module="work" language={language} search={search} onToast={reveal}/>:section==='project-hub'?<ProjectHub language={language} search={search} onToast={reveal}/>:section==='company-chat'?<CollaborationWorkspace language={language} onToast={reveal}/>:section==='notes'?<NotesWorkspace language={language} onToast={reveal}/>:section==='finance-requests'?<FinanceRequests language={language} onToast={reveal}/>:section==='accounting'?<AadinAccountingHub language={language} onToast={reveal}/>:section==='helpdesk'?<SupportWorkspace language={language} onToast={reveal}/>:section==='account'?<AccountWorkspace language={language} onToast={reveal}/>:section==='hr-advanced'?<PersonnelWorkspace language={language} onToast={reveal}/>:['my-work','organization','work','hr','collaboration','correspondence','crm','time-tracking','intelligence'].includes(section)?<OperationsWorkspace key={section} myWork={section==='my-work'} module={({ 'my-work':'work',organization:'organization',work:'work',hr:'hr',collaboration:'collaboration',correspondence:'documents',crm:'crm','time-tracking':'finance',intelligence:'intelligence'} as const)[section as 'my-work'|'organization'|'work'|'hr'|'collaboration'|'correspondence'|'crm'|'time-tracking'|'intelligence']} language={language} search={search} onToast={reveal}/>:section==='assistant'?<section className="ai-page" aria-label={t.assistant}>
      <div className="ai-hero"><div><span className="ai-eyebrow"><Sparkles size={15}/>{rtl?'فضای کار اختصاصی':'DEDICATED AI WORKSPACE'}</span><h1>{t.assistant}</h1><p>{t.assistantDesc}</p><span className="ai-availability">{apiReady?(rtl?'متصل به API، تحلیل آماری فعال':'API connected, statistical insights available'):(rtl?'حالت پیش‌نمایش؛ برای پاسخ واقعی، بک‌اند را اجرا کنید':'Preview mode: start FastAPI to get live data responses')}</span></div><div className="ai-artwork ai-robot-emblem" aria-hidden="true"><span className="ai-robot-halo"/><Bot size={88} strokeWidth={1.45}/><Sparkles className="ai-robot-spark" size={26}/></div></div>
      <div className="ai-chat-card">
       <header className="ai-chat-head"><div><Bot size={22}/><span>{rtl?'گفت‌وگو با دستیار':'Chat with Assistant'}</span></div><span>{rtl?'پاسخ‌ها بر پایه داده‌های سازمانی هستند':'Data-based answers'}</span></header>
       <div className="ai-chat-history" aria-live="polite" aria-label={rtl?'پیام‌های گفت‌وگو':'Chat messages'}>
        {assistantMessages.length===0?<div className="ai-chat-empty"><div className="ai-empty-icon"><Sparkles size={31}/></div><h2>{rtl?'چه چیزی می‌خواهید بررسی کنیم؟':'What would you like to explore?'}</h2><p>{rtl?'درباره پروژه‌ها، فعالیت‌ها و شاخص‌های سازمان سؤال بپرسید.':'Ask about company projects, activities, and metrics.'}</p></div>:assistantMessages.map((m,i)=><div key={i} className={`ai-chat-bubble ${m.role}`}>{m.text}</div>)}
       </div>
       <div className="ai-prompt-chips">{(rtl?['وضعیت پروژه‌ها','تحلیل هزینه‌ها','وظایف در جریان','درخواست‌های تأیید']:['Project status','Expense analysis','Open tasks','Pending approvals']).map(q=><button type="button" key={q} onClick={()=>quickAsk(q)}><Sparkles size={14}/>{q}</button>)}</div>
       <form className="ai-chat-form" onSubmit={respond}><input id="assistant-query" value={question} onChange={e=>setQuestion(e.target.value)} placeholder={t.message} aria-label={t.message} autoComplete="off"/><button type="submit" disabled={!question.trim()||submitting} aria-label={rtl?'ارسال پیام':'Send message'}>{submitting?<Loader2 className="spin" size={19}/>:<Send size={19}/>}</button></form>
       <p className="ai-disclaimer">{rtl?'نسخه فعلی، دستیار آماری مبتنی بر FastAPI است و هنوز مدل زبانی مستقل ندارد.':'This version uses the FastAPI analytics assistant, not a standalone LLM.'}</p>
      </div>
     </section>:<section className="module-page"><div className="module-banner"><div><span className="eyebrow">COMPANY OS / WORKSPACE</span><h1>{rtl?activeNav.fa:activeNav.en}</h1><p>{t.welcome}</p></div><activeNav.icon size={50}/></div>
      <div className="module-tools"><div className="module-summary"><span>{section==='projects'?filteredProjects.length:section==='tasks'?filteredTasks.length:(items[section]||[]).length} {rtl?'مورد':'items'}</span><span className="dim">{tx(apiReady?'متصل به پایگاه داده':'اطلاعات نمونه')}</span></div>{section!=='settings'&&section!=='finance'&&<button className="primary-btn" onClick={()=>startCreate(section as ModalKind)}><Plus size={17}/>{tx("افزودن مورد جدید")}</button>}</div>
      {section==='projects'?<Panel title={tx("فهرست پروژه‌های سازمان")}><div className="table-wrap"><table className="projects-table full-table"><thead><tr><th>{tx("نام پروژه")}</th><th>{tx("وضعیت")}</th><th>{tx("پیشرفت")}</th><th>{tx("تاریخ تحویل")}</th><th>{tx("مسئول")}</th><th>{tx("عملیات")}</th></tr></thead><tbody>{filteredProjects.map(p=><tr key={p.id}><td className="project-name">{tx(p.name)}</td><td><StatusPill value={p.status} language={language}/></td><td><div className="progress-field"><span>{fmt(p.progress)}{tx("٪")}</span><i className="progress-track"><i style={{width:p.progress+'%'}}/></i></div></td><td>{tx(p.deadline)}</td><td>{tx(p.manager)}</td><td><div className="table-actions"><button title={tx("ویرایش")} onClick={()=>startCreate('projects',p.id)}><Pencil size={16}/></button><button title={tx("حذف")} onClick={()=>remove('projects',p.id)}><Trash2 size={16}/></button></div></td></tr>)}</tbody></table></div></Panel>:
      section==='tasks'?<div className="card-list">{filteredTasks.map(tk=><article className="item-card" key={tk.id}><span className="item-emblem"><CheckSquare size={22}/></span><div className="item-info"><h3>{tx(tk.title)}</h3><p>{tx(tk.assignee)} · {tx(tk.due_date)}</p></div><StatusPill value={tk.status} language={language}/><span className="priority">{tx(tk.priority)}</span><div className="table-actions"><button title={tx("ویرایش")} onClick={()=>startCreate('tasks',tk.id)}><Pencil size={16}/></button><button title={tx("حذف")} onClick={()=>remove('tasks',tk.id)}><Trash2 size={16}/></button></div></article>)}</div>:
      section==='finance'?<><section className="stat-grid finance-stats"><div className="stat-card blue"><div className="stat-label">{tx("کل هزینه‌ها")}</div><div className="stat-number">{fmt(dashboard.expenses.reduce((s,e)=>s+e.amount,0))} {tx("ریال")}</div></div><div className="stat-card cyan"><div className="stat-label">{tx("تعداد تراکنش‌ها")}</div><div className="stat-number">{fmt(dashboard.expenses.length)}</div></div></section><Panel title={tx("تراکنش‌های مالی")}><div className="table-wrap"><table className="projects-table full-table"><thead><tr><th>{tx("عنوان")}</th><th>{tx("دسته‌بندی")}</th><th>{tx("مبلغ (ریال)")}</th><th>{tx("تاریخ")}</th></tr></thead><tbody>{dashboard.expenses.map(x=><tr key={x.id}><td>{tx(x.title)}</td><td>{tx(x.category)}</td><td>{fmt(x.amount)}</td><td>{tx(x.paid_at)}</td></tr>)}</tbody></table></div></Panel></>:
      section==='settings'?<div className="settings-grid"><Panel title={tx("نمایش و زبان")}><div className="setting-row">{tx("حالت نمایش")}<button className="outline-btn" onClick={()=>setTheme(theme==='light'?'dark':'light')}>{tx(theme==='light'?'روشن':'تاریک')} <Sun size={16}/></button></div><div className="setting-row">{tx("زبان برنامه")}<button className="outline-btn" onClick={()=>setLanguage(language==='fa'?'en':'fa')}>{language==='fa'?'فارسی':'English'}</button></div></Panel><Panel title={tx("وضعیت سامانه")}><div className="setting-row">Backend <b>{apiReady?'Online':'Offline / Demo'}</b></div><div className="setting-row">{tx("امنیت نشست")} <b>{tx(auth==='authenticated'?'ورود تأییدشده':auth==='loading'?'در حال بررسی':'نیازمند ورود')}</b></div><p className="security-note">{tx("برای محیط عملیاتی، تنظیمات امنیتی، پایگاه داده پایدار و متغیرهای محیطی را طبق README تکمیل کنید.")}</p></Panel></div>:
      <div className="card-list">{(items[section]||[]).filter(x=>`${x.title} ${x.subtitle} ${tx(x.title)} ${tx(x.subtitle)}`.toLowerCase().includes(search.toLowerCase())).map(item=><article className="item-card" key={item.id}><span className="item-emblem"><activeNav.icon size={22}/></span><div className="item-info"><h3>{tx(item.title)}</h3><p>{tx(item.subtitle)}</p></div><StatusPill value={item.status} language={language}/>{item.amount!=null&&<b className="item-amount">{fmt(item.amount)} {tx("ریال")}</b>}{section!=='settings'&&<div className="table-actions"><button title={tx("ویرایش")} onClick={()=>startCreate(section as ModalKind,item.id)}><Pencil size={16}/></button><button title={tx("حذف")} onClick={()=>remove(`modules/${section}`,item.id)}><Trash2 size={16}/></button></div>}</article>)}{(items[section]||[]).length===0&&<div className="empty-state">{t.empty}</div>}</div>}</section>}
   </main>
  </div>
  {modal&&<div className="modal-overlay" onClick={()=>setModal(null)}><form className="modal-box" onClick={e=>e.stopPropagation()} onSubmit={save}><header><h2>{tx(editing?'ویرایش':'ایجاد')} {tx(modal==='projects'?'پروژه':modal==='tasks'?'وظیفه':'مورد جدید')}</h2><button type="button" className="plain-icon" onClick={()=>setModal(null)}><X size={20}/></button></header><label>{tx("عنوان")} <span>*</span><input required maxLength={160} value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder={tx("عنوان را وارد کنید")} autoFocus/></label>{(modal==='projects'||modal==='tasks')&&<><label>{tx("مسئول")}<input value={form.manager} maxLength={100} onChange={e=>setForm({...form,manager:e.target.value})} placeholder={tx("نام و نام خانوادگی")}/></label><label>{tx("تاریخ تحویل")}<input value={form.due_date} maxLength={40} onChange={e=>setForm({...form,due_date:e.target.value})} placeholder={tx("۱۴۰۵-۰۷-۲۰")} /></label>{modal==='projects'?<label>{tx("درصد پیشرفت")}<input type="number" min="0" max="100" value={form.progress} onChange={e=>setForm({...form,progress:e.target.value})}/></label>:<label>{tx("اولویت")}<select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})}><option>{tx("پایین")}</option><option>{tx("متوسط")}</option><option>{tx("بالا")}</option></select></label>}</>}{modal!=='projects'&&modal!=='tasks'&&<label>{tx("توضیحات")}<textarea rows={3} value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>}<footer><button className="outline-btn" type="button" onClick={()=>setModal(null)}>{tx("انصراف")}</button><button className="primary-btn" disabled={submitting}>{submitting?<Loader2 size={16} className="spin"/>:<Check size={16}/>}{tx("ذخیره")}</button></footer></form></div>}
  {selectedApproval&&<div className="modal-overlay" onClick={()=>setSelectedApproval(null)}><div className="modal-box" onClick={e=>e.stopPropagation()}><header><h2>{tx("بررسی درخواست تأیید")}</h2><button className="plain-icon" onClick={()=>setSelectedApproval(null)}><X size={19}/></button></header><h3>{tx(selectedApproval.title)}</h3><p>{tx(selectedApproval.subtitle)}</p><footer><button className="outline-btn" onClick={()=>setSelectedApproval(null)}>{tx("انصراف")}</button><button className="outline-btn" onClick={()=>processApproval('رد شده')}>{tx("رد درخواست")}</button><button className="primary-btn" onClick={()=>processApproval('تأیید شده')}><Check size={16}/>{tx("تأیید")}</button></footer></div></div>}
  {toast&&<div className="toast" role="status"><Sparkles size={16}/>{toast}<button onClick={()=>setToast('')} aria-label={tx("بستن")}><X size={14}/></button></div>}
 </div>
 </div>;
}
