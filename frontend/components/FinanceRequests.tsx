'use client';
import {useCallback,useEffect,useState} from 'react';
import {MessageCircle,Send,Wallet} from 'lucide-react';
import {ops} from '@/lib/ops-api';
import type {OSUser} from '@/lib/ops-api';

type Lang='fa'|'en';
type Req={id:number;requester:string;requester_id:number;subject:string;description:string;status:string;created_at:string};
type Msg={id:number;author:string;body:string;created_at:string};
export default function FinanceRequests({language,onToast}:{language:Lang;onToast:(s:string)=>void}){
 const fa=language==='fa';const t=(a:string,b:string)=>fa?a:b;
 const [user,setUser]=useState<OSUser|null>(null);const [requests,setRequests]=useState<Req[]>([]);const [subject,setSubject]=useState('');const [description,setDescription]=useState('');
 const [selected,setSelected]=useState<number|null>(null);const [messages,setMessages]=useState<Msg[]>([]);const [message,setMessage]=useState('');const [busy,setBusy]=useState(false);
 const canAccount=user&&['owner','admin','manager','accountant'].includes(user.role);
 const reload=useCallback(async()=>{try{const [me,list]=await Promise.all([ops<OSUser>('/me'),ops<Req[]>('/finance-requests')]);setUser(me);setRequests(list)}catch(e){onToast(String(e))}},[onToast]);
 useEffect(()=>{void reload()},[reload]);
 const pick=async(id:number)=>{try{setSelected(id);setMessages(await ops<Msg[]>(`/finance-requests/${id}/messages`))}catch(e){onToast(String(e))}};
 const add=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);try{await ops('/finance-requests',{method:'POST',body:JSON.stringify({subject,description})});setSubject('');setDescription('');await reload();onToast(t('درخواست مالی ثبت شد.','Finance request submitted.'))}catch(e){onToast(String(e))}finally{setBusy(false)}};
 const send=async(e:React.FormEvent)=>{e.preventDefault();if(!selected)return;setBusy(true);try{await ops(`/finance-requests/${selected}/messages`,{method:'POST',body:JSON.stringify({body:message})});setMessage('');await pick(selected)}catch(e){onToast(String(e))}finally{setBusy(false)}};
 const update=async(id:number,status:string)=>{try{await ops(`/finance-requests/${id}/status`,{method:'PATCH',body:JSON.stringify({status})});await reload()}catch(e){onToast(String(e))}};
 return <section className="co-page"><header className="co-heading"><h1><Wallet size={25}/>{t('درخواست‌های مالی','Finance requests')}</h1><p>{t('درخواست هزینه، پرداخت، خرید یا تسویه را بدون دسترسی به دفتر حسابداری به حسابداران ارسال کنید.','Send payment, expense, purchase and settlement requests to accountants without ledger access.')}</p></header>
 <div className="co-panel"><h3>{t('درخواست جدید','New request')}</h3><form className="co-form" onSubmit={e=>void add(e)}><label>{t('موضوع','Subject')}<input required minLength={3} maxLength={180} value={subject} onChange={e=>setSubject(e.target.value)}/></label><label>{t('شرح درخواست','Description')}<textarea required minLength={5} maxLength={5000} rows={3} value={description} onChange={e=>setDescription(e.target.value)}/></label><button disabled={busy} className="co-btn"><Send size={16}/>{t('ارسال به واحد مالی','Submit to accounting')}</button></form></div>
 <div className="co-panel"><h3><MessageCircle size={19}/>{canAccount?t('صندوق درخواست‌های سازمان','Organization finance inbox'):t('درخواست‌های من','My requests')}</h3>{requests.length===0?<p className="co-muted">{t('درخواستی ثبت نشده است.','No requests yet.')}</p>:requests.map(r=><div className="co-item" key={r.id}><button className="ops-link" type="button" onClick={()=>void pick(r.id)}>{r.subject}</button><span>{r.requester}</span><span>{r.status}</span>{canAccount&&<select aria-label={t('وضعیت','Status')} value={r.status} onChange={e=>void update(r.id,e.target.value)}><option value="open">Open</option><option value="in_review">In review</option><option value="answered">Answered</option><option value="closed">Closed</option></select>}</div>)}
 {selected&&<div className="finance-thread"><h3>{requests.find(x=>x.id===selected)?.subject}</h3><p>{requests.find(x=>x.id===selected)?.description}</p>{messages.map(m=><article key={m.id} className="co-note"><b>{m.author}</b><p>{m.body}</p></article>)}<form className="co-form" onSubmit={e=>void send(e)}><textarea aria-label={t('پیام','Message')} required value={message} onChange={e=>setMessage(e.target.value)} rows={2}/><button className="co-btn" disabled={busy||!message.trim()}><Send size={15}/>{t('ارسال پیام','Send message')}</button></form></div>}</div>
 </section>;
}
