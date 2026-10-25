import {localize} from './i18n';
import type {Dashboard,Project,Task,Approval,ModuleItem,ModuleKey,Employee} from './types';
const BASE='/api/v1';
export class ApiError extends Error { constructor(public status:number,message:string){super(message);} }
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
 const response=await fetch(`${BASE}${path}`,{credentials:'same-origin',cache:'no-store',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
 if(!response.ok){let detail='خطا در ارتباط با سرور';try{const b=await response.json();detail=b.detail||detail;}catch{}throw new ApiError(response.status,localize(detail,typeof document!=='undefined'&&document.documentElement.lang==='en'?'en':'fa'))}
 return response.status===204?undefined as T:response.json() as Promise<T>;
}
export const endpoints={
 dashboard:()=>api<Dashboard>('/dashboard'),
 projects:()=>api<Project[]>('/projects'),
 tasks:()=>api<Task[]>('/tasks'),
 approvals:()=>api<Approval[]>('/approvals'),
 employees:()=>api<Employee[]>('/employees'),
 items:(module:ModuleKey)=>api<ModuleItem[]>(`/modules/${module}`),
 create:(kind:string, data:object)=>api<unknown>(`/${kind}`,{method:'POST',body:JSON.stringify(data)}),
 patch:(kind:string,id:number,data:object)=>api<unknown>(`/${kind}/${id}`,{method:'PATCH',body:JSON.stringify(data)}),
 remove:(kind:string,id:number)=>api<void>(`/${kind}/${id}`,{method:'DELETE'}),
 assistant:(question:string,language:'fa'|'en'='fa')=>api<{answer:string;mode:string}>('/assistant',{method:'POST',body:JSON.stringify({question,language})}),
 login:(username:string,password:string)=>api<{ok:boolean}>('/auth/login',{method:'POST',body:JSON.stringify({username,password})}),
 session:()=>api<{authenticated:boolean;demo:boolean}>('/auth/session'),
 logout:()=>api<{ok:boolean}>('/auth/logout',{method:'POST'})
};
