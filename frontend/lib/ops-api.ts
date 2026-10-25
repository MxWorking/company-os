/** Organization-scoped v2 client; the v1 dashboard API remains untouched. */
export type OSModule='organization'|'work'|'hr'|'collaboration'|'documents'|'crm'|'finance'|'intelligence';
export type OSKind=string;
export type OSRecord={id:number;kind:string;title:string;status:string;payload:Record<string,string|number|boolean>;version:number;organization_id:number;created_at:string};
export type Catalog={modules:Record<OSModule,string[]>;kinds:Record<string,{module:OSModule;fields:Record<string,string>}>;statuses:string[]};
export type OSUser={id:number;username:string;name:string;role:string;organization:{id:number;name:string;slug:string};organizations:{id:number;name:string;role:string}[];csrf:string;demo:boolean;job_title?:string|null;permissions?:Record<string,{read:boolean;write:boolean}>};
let csrf='';
export class OpsError extends Error {constructor(public status:number,message:string){super(message)}}
export async function ops<T>(path:string,options:RequestInit={}):Promise<T>{
 const mutation=!!options.method&&options.method!=='GET';
 const response=await fetch('/api/v2'+path,{credentials:'same-origin',cache:'no-store',...options,headers:{'Content-Type':'application/json',...(mutation&&csrf?{'X-Company-CSRF':csrf}:{}),...options.headers}});
 if(!response.ok){let msg=`API request failed (${response.status})`;try{const body=await response.json();msg=typeof body.detail==='string'?body.detail:msg}catch{}throw new OpsError(response.status,msg)}
 return response.status===204?undefined as T:response.json() as Promise<T>
}
export const opsAPI={
 register:(data:{username:string;password:string;full_name:string;organization_slug:string;requested_job_title:string;department:string})=>ops<{status:string;message:string}>('/auth/register',{method:'POST',body:JSON.stringify(data)}),
 reapply:(data:{username:string;password:string;requested_job_title:string;department:string})=>ops<{status:string;message:string}>('/auth/reapply',{method:'POST',body:JSON.stringify(data)}),
 login:(username:string,password:string)=>ops<{ok:boolean;role:string}>('/auth/login',{method:'POST',body:JSON.stringify({username,password})}),
 switchOrg:(org_id:number)=>ops<{ok:boolean}>(`/organizations/switch?org_id=${org_id}`,{method:'POST'}),
 createOrg:(name:string,slug:string)=>ops<{id:number;name:string}>('/organizations',{method:'POST',body:JSON.stringify({name,slug})}),
 me:async()=>{const data=await ops<OSUser>('/me');csrf=data.csrf;return data},
 catalog:()=>ops<Catalog>('/catalog'),
 myWork:()=>ops<{items:OSRecord[];total:number}>('/my-work'),
 list:(kind:string,q='',limit=100,offset=0)=>ops<{items:OSRecord[];total:number}>(`/records/${encodeURIComponent(kind)}?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`),
 add:(kind:string,payload:{title:string;status:string;payload:Record<string,unknown>})=>ops<OSRecord>(`/records/${kind}`,{method:'POST',body:JSON.stringify(payload)}),
 update:(id:number,payload:object)=>ops<OSRecord>(`/record/${id}`,{method:'PATCH',body:JSON.stringify(payload)}),
 archive:(id:number)=>ops<void>(`/record/${id}`,{method:'DELETE'}),
 comments:(id:number)=>ops<{id:number;body:string;author:string;created_at:string}[]>(`/record/${id}/notes`),
 comment:(id:number,body:string)=>ops<{id:number}>(`/record/${id}/notes`,{method:'POST',body:JSON.stringify({body})}),
 checklist:(id:number)=>ops<{id:number;title:string;done:boolean}[]>(`/record/${id}/checklist`),
 checklistAdd:(id:number,title:string)=>ops<{id:number}>(`/record/${id}/checklist`,{method:'POST',body:JSON.stringify({title})}),
 checklistSet:(id:number,done:boolean)=>ops<{id:number}>(`/checklist/${id}?done=${done}`,{method:'PATCH'}),
 members:()=>ops<{id:number;account_id:number;username:string;full_name:string;role:string;active:boolean}[]>('/members'),
 createMember:(body:object)=>ops('/members',{method:'POST',body:JSON.stringify(body)}),
 setMemberRole:(id:number,role:string)=>ops<{ok:boolean}>(`/members/${id}/role?role=${encodeURIComponent(role)}`,{method:'PATCH'}),
 summary:()=>ops<{counts:Record<string,Record<string,number>>;totals:Record<string,number>;source:string;computed_at:string}>('/analytics/summary'),
 assistant:(text:string)=>ops<{answer:string;mode:string;actions_executed:number}>('/assistant/query',{method:'POST',body:JSON.stringify({body:text})}),
 audit:()=>ops<{id:number;action:string;target:string;actor_id:number;at:string}[]>('/audit')
};
