'use client';
import {useCallback,useEffect,useState} from 'react';
import {CheckCircle2,Clock3,ShieldCheck,XCircle} from 'lucide-react';
import {ops,opsAPI} from '@/lib/ops-api';

type Lang='fa'|'en';
type Application={id:number;account_id:number;username:string;full_name:string;requested_job_title:string;approved_job_title:string|null;department:string;status:string;assigned_role:string|null;created_at:string};
type Props={language:Lang;onToast:(message:string)=>void};
export default function RegistrationApprovals({language,onToast}:Props){
 const fa=language==='fa';const t=(a:string,b:string)=>fa?a:b;
 const [canElevate,setCanElevate]=useState(false);
 const [rows,setRows]=useState<Application[]>([]);const [loading,setLoading]=useState(true);
 const [editing,setEditing]=useState<Record<number,{title:string;role:string;reason:string}>>({});
 const load=useCallback(async()=>{try{const r=await ops<Application[]>('/membership-applications?status=pending');setRows(r);setEditing(old=>{const next={...old};r.forEach(row=>{if(!next[row.id])next[row.id]={title:row.requested_job_title,role:'member',reason:''}});return next})}catch(e){onToast(String(e))}finally{setLoading(false)}},[onToast]);
 useEffect(()=>{void opsAPI.me().then(me=>setCanElevate(['owner','admin'].includes(me.role)));void load()},[load]);
 const review=async(id:number,decision:'approved'|'rejected')=>{
  const current=editing[id];if(!current)return;
  if(!window.confirm(t(decision==='approved'?'این درخواست تأیید شود؟':'این درخواست رد شود؟',decision==='approved'?'Approve this registration?':'Reject this registration?')))return;
  try{await ops(`/membership-applications/${id}/review`,{method:'POST',body:JSON.stringify({decision,approved_job_title:current.title,assigned_role:current.role,reason:current.reason})});onToast(t('درخواست بررسی شد.','Application reviewed.'));await load()}catch(e){onToast(String(e))}
 };
 return <section className="co-panel"><h3><ShieldCheck size={18}/>{t('درخواست‌های عضویت در انتظار تأیید','Pending membership applications')}</h3>
 <p className="co-muted">{t('عنوان شغلی اعلام‌شده توسط عضو، مجوز سیستم نیست؛ نقش و عنوان نهایی را مدیر تأیید می‌کند.','A requested job title does not grant permissions. An administrator approves the final title and access role.')}</p>
 {loading?<p>{t('در حال دریافت...','Loading...')}</p>:rows.length===0?<p className="co-muted">{t('درخواستی در انتظار نیست.','No pending applications.')}</p>:rows.map(row=><article key={row.id} className="registration-approval-card"><div><b>{row.full_name}</b> <small dir="ltr">@{row.username}</small><p>{t('عنوان پیشنهادی: ','Requested position: ')}{row.requested_job_title} · {row.department||'—'}</p></div><div className="registration-review-form"><label>{t('عنوان شغلی تأییدشده','Approved job title')}<input maxLength={120} value={editing[row.id]?.title??''} onChange={e=>setEditing(v=>({...v,[row.id]:{...v[row.id],title:e.target.value}}))}/></label><label>{t('نقش سیستمی','System access role')}<select value={editing[row.id]?.role??'member'} onChange={e=>setEditing(v=>({...v,[row.id]:{...v[row.id],role:e.target.value}}))}><option value="member">{t('کارمند / عضو','Member')}</option><option value="viewer">{t('فقط مشاهده محدود','Limited viewer')}</option><option value="accountant">{t('حسابدار','Accountant')}</option>{canElevate&&<><option value="manager">{t('مدیر سازمان','Manager')}</option><option value="admin">{t('مدیر ارشد سامانه','Administrator')}</option></>}</select></label><label>{t('دلیل رد (اختیاری)','Rejection reason (optional)')}<input maxLength={500} value={editing[row.id]?.reason??''} onChange={e=>setEditing(v=>({...v,[row.id]:{...v[row.id],reason:e.target.value}}))}/></label></div><div className="co-toolbar"><button type="button" className="co-btn" disabled={!editing[row.id]?.title.trim()} onClick={()=>void review(row.id,'approved')}><CheckCircle2 size={16}/>{t('تأیید و فعال‌سازی','Approve & activate')}</button><button type="button" className="co-btn subtle" onClick={()=>void review(row.id,'rejected')}><XCircle size={16}/>{t('رد درخواست','Reject')}</button></div></article>)}
 </section>
}
