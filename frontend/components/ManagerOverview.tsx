'use client';
import {useCallback,useEffect,useState} from 'react';
import {RefreshCcw,FolderKanban,CheckSquare,Users,BarChart3} from 'lucide-react';
import {opsAPI} from '@/lib/ops-api';

type Lang='fa'|'en';
type Props={language:Lang;onOpen:(key:'project-hub'|'work'|'hr-advanced'|'intelligence')=>void};
export default function ManagerOverview({language,onOpen}:Props){
 const fa=language==='fa';
 const [data,setData]=useState<{counts:Record<string,Record<string,number>>}|null>(null);const [error,setError]=useState('');
 const refresh=useCallback(async()=>{try{const v=await opsAPI.summary();setData(v);setError('')}catch(e){setError(String(e))}},[]);
 useEffect(()=>{void refresh()},[refresh]);
 const total=(module:string)=>Object.values(data?.counts[module]||{}).reduce((sum,n)=>sum+n,0);
 const cards=[{module:'work',fa:'پروژه‌ها و وظایف',en:'Projects & Tasks',key:'project-hub' as const,icon:FolderKanban},{module:'organization',fa:'ساختار سازمانی',en:'Organization',key:'hr-advanced' as const,icon:Users},{module:'finance',fa:'رویدادهای مالی',en:'Finance records',key:'intelligence' as const,icon:BarChart3},{module:'collaboration',fa:'ارتباطات تیمی',en:'Collaboration',key:'work' as const,icon:CheckSquare}];
 return <section className="co-page"><header className="co-heading"><h1>{fa?'داشبورد مدیر سازمان':'Organization Manager Dashboard'}</h1><p>{fa?'آمار سازمانی از API امن و محدود به سازمان جاری دریافت می‌شود.':'Organization-scoped figures from the secure API.'}</p><button className="co-btn" onClick={()=>void refresh()}><RefreshCcw size={16}/>{fa?'به‌روزرسانی':'Refresh'}</button></header>{error&&<p role="alert">{error}</p>}<div className="stat-grid">{cards.map(card=><button key={card.module} className="stat-card" onClick={()=>onOpen(card.key)}><card.icon size={24}/><span className="stat-label">{fa?card.fa:card.en}</span><strong className="stat-number">{total(card.module).toLocaleString(fa?'fa-IR':'en-US')}</strong></button>)}</div></section>;
}
