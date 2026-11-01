export const PROJECTS = ['A','B','C','D','E'] as const;
export const OPTIONS = [...PROJECTS,'Frei','Krank','Urlaub'] as const;
export type Assignment = typeof OPTIONS[number];
export type Plan = {
  employees: {id:string;name:string}[];
  projects: Record<string,string>;
  assignments: Record<string,Record<string,Assignment>>;
  demands: Record<string,Record<string,number|null>>;
};
export function dateKey(date:Date) { return `${date.getUTCFullYear()}-${String(date.getUTCMonth()+1).padStart(2,'0')}-${String(date.getUTCDate()).padStart(2,'0')}`; }
export function monday(date:string) { const d=new Date(date+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7)); return dateKey(d); }
export function shift(date:string,days:number) { const d=new Date(date+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()+days); return dateKey(d); }
export function weekNumber(date:string) { const d=new Date(date+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()+3-((d.getUTCDay()+6)%7)); const start=new Date(Date.UTC(d.getUTCFullYear(),0,1,12)); return Math.ceil((((d.getTime()-start.getTime())/86400000)+1)/7); }
export function initialPlan():Plan {
  const employees=Array.from({length:10},(_,i)=>({id:`m${i+1}`,name:`Monteur ${String(i+1).padStart(2,'0')}`}));
  const assignments:Plan['assignments']={}; const demands:Plan['demands']={};
  for(let day=0;day<5;day++) { const date=shift('2026-10-19',day); assignments[date]={}; employees.forEach((e,i)=>assignments[date][e.id]=i<3?'A':i<5?'B':i<8?'C':i===8?'Frei':'Urlaub'); demands[date]={A:3,B:4,C:5,D:null,E:null}; }
  return {employees,projects:{A:'Projekt A',B:'Projekt B',C:'Projekt C',D:'Projekt D',E:'Projekt E'},assignments,demands};
}
export function summary(plan:Plan,date:string) { return PROJECTS.map(id=>{const assigned=plan.employees.filter(e=>plan.assignments[date]?.[e.id]===id).length;const demand=plan.demands[date]?.[id]??null;return {id,assigned,demand,missing:demand===null?null:Math.max(0,demand-assigned),surplus:demand===null?0:Math.max(0,assigned-demand)};}); }
