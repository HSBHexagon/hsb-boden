import Core from './core.mjs';
const text=x=>String(x??'').trim();
export function applyCommand(db,c,today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Berlin'}).format(new Date())){
 if(!c||typeof c!=='object')throw Error('Änderungsauftrag fehlt.');
 switch(c.type){
 case 'worker':{
  const d=c.data||{},id=c.id||d.id||Core.genid(),existing=db.workers.find(x=>x.id===id);
  if(c.id&&!existing)throw Error('Monteur nicht gefunden.');
  const w={id,name:text(d.name),skills:text(d.skills),crew:text(d.crew),active:d.active===true||d.active==='1'};
  if(existing)Object.assign(existing,w);else db.workers.push(w);
  if(!w.active)db.assignments=db.assignments.filter(a=>a.workerId!==id||a.date<today);
  Core.log(db,`Monteur ${id} gespeichert`);return true;
 }
 case 'project':{
  const d=c.data||{},id=c.id||d.id||Core.genid(),existing=db.projects.find(x=>x.id===id);
  if(c.id&&!existing)throw Error('Projekt nicht gefunden.');
  const p={id,number:text(d.number),customer:text(d.customer),title:text(d.title),place:text(d.place),address:text(d.address),meeting:text(d.meeting),time:text(d.time),start:d.start,end:d.end,requirement:Number(d.requirement),requiredSkill:text(d.requiredSkill),notes:text(d.notes),active:d.active===true||d.active==='1',dayNeeds:existing?.dayNeeds||{}};
  if(!p.number||!p.customer||!p.place)throw Error('Projektnummer, Kunde und Ort sind Pflichtfelder.');
  Core.checkProjectLimit(db,p,id);
  if(existing)Object.assign(existing,p);else db.projects.push(p);
  if(!p.active)db.assignments=db.assignments.filter(a=>a.projectId!==id||a.date<today);
  Core.log(db,`Projekt ${id} gespeichert`);return true;
 }
 case 'assign':return Core.assignRange(db,c.workerId,c.projectId,c.from,c.to);
 case 'unassign':Core.unassign(db,c.workerId,c.date);return true;
 case 'absence':return Core.markAbsence(db,c.workerId,c.from,c.to,c.absenceType);
 case 'need':Core.updateNeed(db,c.projectId,c.from,c.to,c.count);if(c.count===0)db.assignments=db.assignments.filter(a=>a.projectId!==c.projectId||a.date<c.from||a.date>c.to);return true;
 case 'extend':return Core.extendProject(db,c.projectId,c.end,c.carry===true);
 case 'crew':{
  const members=db.workers.filter(w=>w.active&&w.crew===c.crew),skip=[];let done=0;
  for(const w of members){const previous=structuredClone(db);try{Core.unassign(db,w.id,c.date);Core.assign(db,w.id,c.projectId,c.date);done++}catch(e){Object.assign(db,previous);skip.push(`${w.name}: ${e.message}`)}}return {done,skip};
 }
 default:throw Error('Unbekannter Änderungsauftrag.');
 }
}
