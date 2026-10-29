import { Core as c } from '../public/planner-core.mjs';
export function fixture() {
  const db=c.emptyDB();
  db.workers=Array.from({length:4},(_,i)=>({id:`test-w${i}`,name:`TEST Person ${i}`,skills:'Fliesen, Fahrer',crew:i<2?'Testkolonne':'',active:true}));
  db.projects=[{id:'test-a',number:'TEST-A',customer:'TEST Kunde A',title:'Testarbeiten',place:'Testort',address:'Testadresse',meeting:'Testtreffpunkt',time:'06:30',start:'2026-10-19',end:'2026-10-23',requirement:2,requiredSkill:'Fliesen',notes:'Vertrauliche interne Notiz',active:true,dayNeeds:{}},{id:'test-b',number:'TEST-B',customer:'TEST Kunde B',title:'Testarbeiten',place:'Testort B',address:'',meeting:'',time:'07:00',start:'2026-10-19',end:'2026-10-23',requirement:1,requiredSkill:'',notes:'',active:true,dayNeeds:{}}];
  return db;
}
