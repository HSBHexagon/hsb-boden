'use client';
import { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Plus, X, Check, RefreshCw, Pencil } from 'lucide-react';
import { OPTIONS, PROJECTS, dateKey, monday, shift, weekNumber, summary, type Plan, type Assignment } from '@/lib/planner';

const format=(d:string,options:Intl.DateTimeFormatOptions)=>new Intl.DateTimeFormat('de-DE',{...options,timeZone:'UTC'}).format(new Date(d+'T12:00:00Z'));
const today=()=>new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Berlin'}).format(new Date());
export default function Planner(){
  const [plan,setPlan]=useState<Plan|null>(null),[revision,setRevision]=useState(0);
  const [week,setWeek]=useState(()=>monday(today())),[selected,setSelected]=useState(()=>Math.min(4,Math.max(0,(new Date(today()+'T12:00:00Z').getUTCDay()+6)%7)));
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[loaded,setLoaded]=useState(false),[saved,setSaved]=useState(false),[dirty,setDirty]=useState(false);
  const [editor,setEditor]=useState<string|null>(null),[name,setName]=useState('');
  const locked=useRef(false),unsaved=useRef(false);
  async function load(){
    try{const response=await fetch('/api/plan',{cache:'no-store'});const data=await response.json() as {plan:Plan;revision:number;error?:string};if(!response.ok)throw new Error(data.error);setPlan(data.plan);setRevision(data.revision);setLoaded(true);setSaved(data.revision>0);}
    catch(e){setError(e instanceof Error?e.message:'Laden fehlgeschlagen.');}
  }
  useEffect(()=>{void load();const focus=()=>{if(!locked.current&&!unsaved.current)void load();};window.addEventListener('focus',focus);return()=>window.removeEventListener('focus',focus);},[]);
  useEffect(()=>{const protect=(e:BeforeUnloadEvent)=>{if(unsaved.current){e.preventDefault();}};window.addEventListener('beforeunload',protect);return()=>window.removeEventListener('beforeunload',protect);},[]);
  async function persist(next:Plan){
    if(locked.current)return;locked.current=true;setBusy(true);setError('');setPlan(next);setDirty(true);unsaved.current=true;
    try{
      const response=await fetch('/api/plan',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan:next,revision})});const data=await response.json() as {revision:number;error?:string};
      if(response.status===409){await load();setDirty(false);unsaved.current=false;throw new Error(data.error+' Bitte die gewünschte Änderung erneut eingeben.');}
      if(!response.ok)throw new Error(data.error);setRevision(data.revision);setSaved(true);setDirty(false);unsaved.current=false;
    }catch(e){setError(e instanceof Error?e.message:'Speichern fehlgeschlagen.');}
    finally{locked.current=false;setBusy(false);}
  }
  function assign(employee:string,date:string,value:Assignment){if(!plan)return;void persist({...plan,assignments:{...plan.assignments,[date]:{...plan.assignments[date],[employee]:value}}});}
  function demand(project:string,value:string){if(!plan)return;void persist({...plan,demands:{...plan.demands,[day]:{...plan.demands[day],[project]:value===''?null:Number(value)}}});}
  function changeWeek(amount:number){setWeek(shift(week,amount*7));}
  function employeeSubmit(e:React.FormEvent){e.preventDefault();if(!plan||!name.trim())return;const employees=editor==='new'?[...plan.employees,{id:`m-${Date.now()}-${Array.from(crypto.getRandomValues(new Uint32Array(2)),n=>n.toString(16)).join('')}`,name:name.trim()}]:plan.employees.map(p=>p.id===editor?{...p,name:name.trim()}:p);void persist({...plan,employees});setEditor(null);}
  const days=Array.from({length:5},(_,i)=>shift(week,i)),day=days[selected];
  const free=plan?.employees.filter(e=>(plan.assignments[day]?.[e.id]??'Frei')==='Frei')??[];
  return <main>
    <header><div><div className="brand">HSB Boden</div><h1>Monteurplanung</h1></div><button className="primary" disabled={!loaded||busy} onClick={()=>{setName('');setEditor('new');}}><Plus size={18}/><span>Monteur hinzufügen</span></button></header>
    <div className="toolbar"><div className="weeknav"><button aria-label="Vorherige Woche" onClick={()=>changeWeek(-1)}><ChevronLeft size={22}/></button><label className="weeklabel"><span>KW {weekNumber(week)} · {format(week,{day:'numeric'})}–{format(days[4],{day:'numeric',month:'long',year:'numeric'})}</span><input aria-label="Woche auswählen" type="date" value={week} onChange={e=>{if(e.target.value)setWeek(monday(e.target.value));}}/></label><button aria-label="Nächste Woche" onClick={()=>changeWeek(1)}><ChevronRight size={22}/></button></div><div className="savestate" role="status">{busy?<><RefreshCw className="spin" size={14}/>Speichert …</>:dirty?'Nicht gespeichert':saved?<><Check size={15}/>Gespeichert</>:'Beispieldaten'}</div></div>
    {error&&<div className="notice" role="alert"><span>{error}</span><button disabled={busy} onClick={()=>{if(dirty&&plan)void persist(plan);else{setError('');void load();}}}>Erneut versuchen</button></div>}
    {!plan?<div className="loading" role="status">{error?'Planung momentan nicht verfügbar.':'Planung wird geladen …'}</div>:<>
    <div className="scrollgrid"><table className="schedule"><thead><tr><th scope="col">Monteur</th>{days.map((date,i)=><th key={date} scope="col" className={i===selected?'selected':''}><button onClick={()=>setSelected(i)} aria-pressed={i===selected}>{format(date,{weekday:'short',day:'2-digit',month:'2-digit'})}</button></th>)}</tr></thead><tbody>{plan.employees.map(employee=><tr key={employee.id}><th scope="row"><button className="person" title="Name ändern" aria-label={`${employee.name}: Name ändern`} disabled={busy} onClick={()=>{setEditor(employee.id);setName(employee.name);}}>{employee.name}<Pencil size={12}/></button></th>{days.map((date,i)=>{const value=plan.assignments[date]?.[employee.id]??'Frei';return <td key={date} className={i===selected?'selected':''}><select disabled={busy} aria-label={`${employee.name}, ${format(date,{weekday:'long',day:'numeric',month:'long'})}`} className={`assignment color-${value}`} value={value} onFocus={()=>setSelected(i)} onChange={e=>assign(employee.id,date,e.target.value as Assignment)}>{OPTIONS.map(option=><option value={option} key={option}>{PROJECTS.includes(option as typeof PROJECTS[number])?plan.projects[option]:option}</option>)}</select></td>;})}</tr>)}</tbody></table></div>
    <section className="summary"><h2>Besetzung · {format(day,{weekday:'long',day:'2-digit',month:'2-digit'})}</h2><div className="summaryscroll"><table><thead><tr><th>Projekt</th><th>Bedarf</th><th>Eingeteilt</th><th>Offen</th></tr></thead><tbody>{summary(plan,day).map(row=><tr key={row.id}><th scope="row"><input className="projectname" aria-label={`Name Projekt ${row.id}`} defaultValue={plan.projects[row.id]} key={row.id+plan.projects[row.id]} maxLength={80} disabled={busy} onBlur={e=>{const name=e.target.value.trim();if(name&&name!==plan.projects[row.id])void persist({...plan,projects:{...plan.projects,[row.id]:name}});else if(!name)e.target.value=plan.projects[row.id];}}/></th><td><input className="demand" type="number" aria-label={`Bedarf ${plan.projects[row.id]}`} min={0} max={200} step={1} placeholder="—" key={day+row.id+row.demand} defaultValue={row.demand??''} disabled={busy} onBlur={e=>{if(e.target.validity.valid&&(e.target.value===''?null:Number(e.target.value))!==row.demand)demand(row.id,e.target.value);else if(!e.target.validity.valid)e.target.value=row.demand===null?'':String(row.demand);}} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur();}}/></td><td>{row.assigned}</td><td className={row.missing===null?'unset':row.missing>0?'shortage':row.surplus>0?'surplus':'complete'}>{row.missing===null?'Bedarf festlegen':row.missing>0?`${row.missing} fehlen`:row.surplus>0?`${row.surplus} zu viel`:'0'}</td></tr>)}</tbody></table></div></section>
    <div className="available">Verfügbar am {format(day,{weekday:'long'})}: <strong>{free.length?free.map(e=>e.name).join(', '):'Keine freien Monteure'}</strong></div>
    <footer>Ganze Tage · ein Einsatz pro Monteur und Tag <span>Projektname und Bedarf direkt anklicken und ändern.</span></footer>
    </>}
    {editor&&<div className="backdrop" onClick={e=>{if(e.target===e.currentTarget)setEditor(null);}}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><button className="close" aria-label="Schließen" onClick={()=>setEditor(null)}><X size={20}/></button><h2 id="dialog-title">{editor==='new'?'Monteur hinzufügen':'Name ändern'}</h2><form onSubmit={employeeSubmit}><label>Name<input autoFocus required maxLength={80} value={name} onChange={e=>setName(e.target.value)} placeholder="Vor- und Nachname"/></label><div className="modalactions"><button type="button" onClick={()=>setEditor(null)}>Abbrechen</button><button className="primary" disabled={busy||!name.trim()}>Speichern</button></div></form></section></div>}
  </main>;
}
