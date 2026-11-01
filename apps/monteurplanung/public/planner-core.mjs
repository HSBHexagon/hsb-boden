
'use strict';
const iso=d=>{if(typeof d==='string')return d;return d.toISOString().slice(0,10)};
const asUTC=s=>new Date(s+'T12:00:00Z');
const plusDays=(s,n)=>{let d=asUTC(s);d.setUTCDate(d.getUTCDate()+n);return iso(d)};
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(asUTC(s).getTime())&&iso(asUTC(s))===s;
const monday=s=>plusDays(s,-((asUTC(s).getUTCDay()+6)%7));
const weekDays=s=>Array.from({length:6},(_,i)=>plusDays(monday(s),i));
const isoWeek=s=>{let d=asUTC(s);d.setUTCDate(d.getUTCDate()+3-((d.getUTCDay()+6)%7));let y=d.getUTCFullYear();let first=asUTC(`${y}-01-01`);return {year:y,num:Math.ceil((((d-first)/86400000)+1)/7)};};
const inRange=(d,a,b)=>d>=a&&d<=b;
const genid=()=>crypto.randomUUID();
function emptyDB(){return {version:3,workers:[],projects:[],assignments:[],absences:[],history:[]};}
function log(db,message){db.history.unshift({id:genid(),at:new Date().toISOString(),message});db.history=db.history.slice(0,250)}
function projectActive(p,day){return p.active!==false&&inRange(day,p.start,p.end)&&asUTC(day).getUTCDay()!==0;}
function need(p,day){if(!projectActive(p,day))return 0;if(Object.prototype.hasOwnProperty.call(p.dayNeeds||{},day))return Math.max(0,Number(p.dayNeeds[day]));return asUTC(day).getUTCDay()===6?0:p.requirement;}
const workerSkills=w=>(w.skills||'').split(/[,;/]/).map(x=>x.trim().toLowerCase()).filter(Boolean);
const qualifies=(w,p)=>!p.requiredSkill||workerSkills(w).includes(p.requiredSkill.trim().toLowerCase());
function daySummary(db,date){let projects=db.projects.filter(p=>projectActive(p,date)).map(p=>{const required=need(p,date),assigned=db.assignments.filter(a=>a.date===date&&a.projectId===p.id);return {project:p,required,assigned,missing:Math.max(0,required-assigned.length),extra:Math.max(0,assigned.length-required)};}).filter(x=>x.required>0||x.assigned.length>0);const occupied=new Set(db.assignments.filter(a=>a.date===date).map(a=>a.workerId));let available=db.workers.filter(w=>w.active!==false&&!occupied.has(w.id)&&!db.absences.some(a=>a.workerId===w.id&&inRange(date,a.from,a.to)));return {date,projects,free:available.length,available,totalNeed:projects.reduce((a,x)=>a+x.required,0),assigned:projects.reduce((a,x)=>a+x.assigned.length,0),missing:projects.reduce((a,x)=>a+x.missing,0)};}
function candidates(db,projectId,date){const p=db.projects.find(x=>x.id===projectId);if(!p)return [];let all=daySummary(db,date);const crewCount=new Map();for(const a of db.assignments.filter(a=>a.projectId===projectId&&a.date===date)){let w=db.workers.find(x=>x.id===a.workerId);if(w?.crew)crewCount.set(w.crew,(crewCount.get(w.crew)||0)+1)}return all.available.filter(w=>qualifies(w,p)).sort((a,b)=>(crewCount.get(b.crew)||0)-(crewCount.get(a.crew)||0)||a.name.localeCompare(b.name,'de'));}
function suggestMoves(db,projectId,date){
 const target=db.projects.find(p=>p.id===projectId);if(!target||!projectActive(target,date)||!need(target,date))return [];
 return daySummary(db,date).projects.filter(p=>p.project.id!==projectId&&p.extra>0).flatMap(p=>p.assigned.map(a=>({worker:db.workers.find(w=>w.id===a.workerId),source:p.project}))).filter(x=>x.worker?.active&&qualifies(x.worker,target));
}
function reassign(db,workerId,projectId,date){
 if(!suggestMoves(db,projectId,date).some(x=>x.worker.id===workerId))throw Error('Keine geeignete Überbesetzung mehr vorhanden.');
 const before=structuredClone(db);try{unassign(db,workerId,date);assign(db,workerId,projectId,date);}catch(e){Object.assign(db,before);throw e;}
}
function assign(db,workerId,projectId,date){const w=db.workers.find(x=>x.id===workerId),p=db.projects.find(x=>x.id===projectId);if(!w||!p)throw Error('Mitarbeiter oder Projekt unbekannt.');if(w.active===false)throw Error('Monteur ist deaktiviert.');if(!validDate(date)||!projectActive(p,date))throw Error('Projekt ist an diesem Tag nicht aktiv.');if(!need(p,date))throw Error('Für diesen Tag ist kein Personalbedarf festgelegt.');if(db.absences.some(a=>a.workerId===workerId&&inRange(date,a.from,a.to)))throw Error('Monteur ist an diesem Tag abwesend.');if(db.assignments.some(a=>a.workerId===workerId&&a.date===date))throw Error('Monteur ist bereits an diesem Tag eingeplant.');if(!qualifies(w,p))throw Error('Erforderliche Qualifikation fehlt.');db.assignments.push({id:genid(),workerId,projectId,date});log(db,`${w.name} → ${p.number} am ${date} eingeteilt`);}
function assignRange(db,workerId,projectId,from,to){if(!validDate(from)||!validDate(to)||to<from||((asUTC(to)-asUTC(from))/86400000)>60)throw Error('Ungültiger Zeitraum (maximal 61 Tage).');let added=[],skipped=[];for(let d=from;d<=to;d=plusDays(d,1)){if(asUTC(d).getUTCDay()===0)continue;try{assign(db,workerId,projectId,d);added.push(d)}catch(e){skipped.push({date:d,error:e.message})}}return {added,skipped};}
function unassign(db,workerId,date){let previous=db.assignments.find(a=>a.workerId===workerId&&a.date===date);if(!previous)return;db.assignments=db.assignments.filter(a=>a!==previous);log(db,`Zuteilung ${workerId} am ${date} entfernt`)}
function markAbsence(db,workerId,from,to,type){if(!['krank','urlaub','sonstig'].includes(type))throw Error('Ungültige Abwesenheit.');if(!validDate(from)||!validDate(to)||to<from)throw Error('Ungültiger Zeitraum.');const w=db.workers.find(x=>x.id===workerId);if(!w)throw Error('Monteur nicht gefunden.');const removed=db.assignments.filter(a=>a.workerId===workerId&&inRange(a.date,from,to));db.assignments=db.assignments.filter(a=>!removed.includes(a));db.absences.push({id:genid(),workerId,from,to,type});log(db,`Abwesenheit für ${w.name}: ${from} bis ${to}; ${removed.length} Einsätze entfernt`);return {removed};}
function checkProjectLimit(db,newp,excludeId){if(!validDate(newp.start)||!validDate(newp.end)||newp.end<newp.start)throw Error('Ungültiger Projektzeitraum.');if( (asUTC(newp.end)-asUTC(newp.start))/86400000>730)throw Error('Projekte dürfen maximal zwei Jahre umfassen.');if(newp.active===false)return;let date=monday(newp.start),end=monday(newp.end);for(;date<=end;date=plusDays(date,7)){let overlaps=db.projects.filter(p=>p.id!==excludeId&&p.active!==false&&p.start<=plusDays(date,6)&&p.end>=date).length;}}
function extendProject(db,projectId,newEnd,carry){const p=db.projects.find(x=>x.id===projectId);if(!p)throw Error('Projekt nicht gefunden.');if(!validDate(newEnd)||newEnd<=p.end)throw Error('Neues Projektende muss später liegen.');checkProjectLimit(db,{...p,end:newEnd},p.id);const oldEnd=p.end;const source=[...db.assignments].filter(a=>a.projectId===p.id&&a.date<=oldEnd).sort((a,b)=>b.date.localeCompare(a.date));const team=[...new Set(source.filter(a=>a.date===source[0]?.date).map(a=>a.workerId))];p.end=newEnd;const skipped=[];if(carry){for(let day=plusDays(oldEnd,1);day<=newEnd;day=plusDays(day,1)){if(!need(p,day))continue;for(let workerId of team){try{assign(db,workerId,p.id,day)}catch(e){skipped.push({date:day,workerId,error:e.message});}}}}log(db,`Projekt ${p.number} bis ${newEnd} verlängert`);return {skipped};}
function updateNeed(db,projectId,from,to,required){const p=db.projects.find(x=>x.id===projectId);if(!p)throw Error('Projekt nicht gefunden.');if(!validDate(from)||!validDate(to)||to<from)throw Error('Ungültiger Zeitraum.');if(!Number.isInteger(required)||required<0||required>99)throw Error('Personalbedarf zwischen 0 und 99 eingeben.');for(let d=from;d<=to;d=plusDays(d,1))if(inRange(d,p.start,p.end)&&asUTC(d).getUTCDay()!==0)p.dayNeeds[d]=required;log(db,`Personalbedarf ${p.number}: ${required} vom ${from} bis ${to}`)}
function whatsAppText(db,week){let days=weekDays(week),{year,num}=isoWeek(week);let out=[`KW ${num}/${year}`,`Planung ${days[0]} bis ${days[5]}`];const weekProj=db.projects.filter(p=>days.some(d=>need(p,d)>0||db.assignments.some(a=>a.projectId===p.id&&a.date===d)));const weekday=['So','Mo','Di','Mi','Do','Fr','Sa'];for(const p of weekProj){let active=days.filter(d=>need(p,d)>0||db.assignments.some(a=>a.projectId===p.id&&a.date===d));if(!active.length)continue;out.push('',`${p.number} · ${p.customer||p.title||'Projekt'} · ${p.place||'Ort offen'}`);if(p.address)out.push(`Baustelle: ${p.address}`);if(p.meeting||p.time)out.push(`Treffpunkt: ${p.meeting||'noch offen'} · ${p.time||'Uhrzeit offen'}`);const entries=active.map(d=>({date:d,names:db.assignments.filter(a=>a.projectId===p.id&&a.date===d).map(a=>db.workers.find(w=>w.id===a.workerId)?.name).filter(Boolean).sort()}));const same=entries.length>1&&entries.every((e,i)=>e.names.join('|')===entries[0].names.join('|')&&(i===0||plusDays(entries[i-1].date,1)===e.date));if(same){out.push(`${weekday[asUTC(active[0]).getUTCDay()]}–${weekday[asUTC(active[active.length-1]).getUTCDay()]}: ${entries[0].names.join(', ')||'Noch nicht besetzt'}`)}else for(const e of entries)out.push(`${weekday[asUTC(e.date).getUTCDay()]} ${e.date.slice(8)}.${e.date.slice(5,7)}.: ${e.names.join(', ')||'Noch nicht besetzt'}`)}return out.join('\n').trim()+'\n';}
function validateDB(db){
 try {
  if(!db||db.version!==3||!['workers','projects','assignments','absences','history'].every(k=>Array.isArray(db[k])))return false;
  if(db.workers.length>500||db.projects.length>1500||db.assignments.length>100000||db.absences.length>10000)return false;
  const text=(v,max,required=false)=>typeof v==='string'&&v.length<=max&&(!required||v.trim().length>0);
  const ids=new Set(), wi=new Map(),pi=new Map(),pn=new Set(),slots=new Set();
  const unique=x=>text(x.id,80,true)&&!ids.has(x.id)&&(ids.add(x.id),true);
  for(const w of db.workers){
   if(!unique(w)||!text(w.name,100,true)||!text(w.skills,500)||!text(w.crew,100)||typeof w.active!=='boolean')return false;wi.set(w.id,w);
  }
  for(const p of db.projects){
   if(!unique(p)||!text(p.number,40,true)||pn.has(p.number.trim().toLowerCase())||!text(p.customer,100)||!text(p.title,120)||!(p.customer.trim()||p.title.trim())||!text(p.place,120,true)||!validDate(p.start)||!validDate(p.end)||p.end<p.start||(asUTC(p.end)-asUTC(p.start))/86400000>730||!Number.isInteger(p.requirement)||p.requirement<0||p.requirement>99||typeof p.active!=='boolean'||!p.dayNeeds||typeof p.dayNeeds!=='object'||Array.isArray(p.dayNeeds))return false;
   if(!text(p.address,500)||!text(p.meeting,500)||!text(p.time,5)||p.time&&!/^([01]\d|2[0-3]):[0-5]\d$/.test(p.time)||!text(p.requiredSkill,100)||!text(p.notes,5000))return false;
   for(const [date,n] of Object.entries(p.dayNeeds))if(!validDate(date)||!inRange(date,p.start,p.end)||!Number.isInteger(n)||n<0||n>99)return false;
   pi.set(p.id,p);pn.add(p.number.trim().toLowerCase());
  }
  for(const a of db.assignments){
   const w=wi.get(a.workerId),p=pi.get(a.projectId),key=a.workerId+':'+a.date;
   if(!unique(a)||!w||!p||w.active===false||!validDate(a.date)||!projectActive(p,a.date)||!qualifies(w,p)||slots.has(key))return false;slots.add(key);
  }
  for(const a of db.absences){
   if(!unique(a)||!wi.has(a.workerId)||!validDate(a.from)||!validDate(a.to)||a.to<a.from||!['krank','urlaub','sonstig'].includes(a.type))return false;
   if(db.assignments.some(b=>b.workerId===a.workerId&&inRange(b.date,a.from,a.to)))return false;
  }
  return true;
 } catch { return false; }
}
const Core={emptyDB,suggestMoves,reassign,iso,asUTC,plusDays,validDate,monday,weekDays,isoWeek,need,qualifies,daySummary,candidates,assign,assignRange,unassign,markAbsence,checkProjectLimit,extendProject,updateNeed,whatsAppText,validateDB,log,genid};


export { Core };
