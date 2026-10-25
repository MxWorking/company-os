export type Project = { id:number; name:string; manager:string; initials:string; progress:number; status:string; deadline:string; color?:string; description?:string };
export type Task = { id:number; title:string; project_id:number | null; assignee:string; status:string; priority:string; due_date:string };
export type Approval = { id:number; title:string; subtitle:string; severity:string; status:string };
export type Expense = { id:number; title:string; amount:number; category:string; paid_at:string };
export type Activity = { id:number; title:string; detail:string; time:string; icon:string };
export type ModuleItem = { id:number; module:string; title:string; subtitle:string; status:string; amount?:number };
export type Stats = {projects:number; tasks:number; approvals:number; expenses:number; project_change:string; task_change:string; approval_change:string; expense_change:string; statuses:{label:string;count:number;color:string}[]; trend:{month:string;income:number;expense:number;profit:number}[]};
export type Dashboard = {stats:Stats;projects:Project[];tasks:Task[];approvals:Approval[];activities:Activity[];expenses:Expense[]};
export type ModuleKey = 'dashboard'|'projects'|'tasks'|'documents'|'finance'|'procurement'|'hr'|'knowledge'|'assistant'|'settings'|'support'|'organization'|'my-work'|'work'|'hr-advanced'|'collaboration'|'correspondence'|'crm'|'time-tracking'|'intelligence'|'project-hub'|'company-chat'|'notes'|'accounting'|'finance-requests'|'account'|'helpdesk';

export type Employee = {id:number; personnel_code:string; first_name:string; last_name:string; role:string; job_title:string; department:string; reporting_to_id:number|null; employment_type:string; employment_status:string; phone:string; email:string; work_location:string; start_date:string; end_date:string; notes:string};
