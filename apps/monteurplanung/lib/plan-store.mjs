import { Core } from '../public/planner-core.mjs';

// Names never come from a request. All environments use the same fixed schema;
// environment is a bound value included in every key and every query.
export async function readPlan(database, environment) {
 const statements=[
  database.prepare('SELECT revision FROM planning_meta WHERE environment=?').bind(environment),
  ...['workers','projects','assignments','absences'].map(table=>database.prepare(`SELECT payload FROM planning_${table} WHERE environment=? ORDER BY id`).bind(environment)),
  database.prepare('SELECT revision, at, actor, summary FROM planning_revisions WHERE environment=? ORDER BY revision DESC LIMIT 250').bind(environment),
 ];
 const rows=await database.batch(statements);
 const plan=Core.emptyDB();
 ['workers','projects','assignments','absences'].forEach((key,i)=>plan[key]=rows[i+1].results.map(r=>JSON.parse(r.payload)));
 plan.history=rows[5].results.map(r=>({id:String(r.revision),at:r.at,message:r.summary,actor:r.actor}));
 return {plan,revision:rows[0].results[0]?.revision??0};
}

export async function writePlan(database, environment, plan, revision, actor) {
 const previous=await readPlan(database,environment);
 if(previous.revision!==revision)return null;
 const token=crypto.randomUUID(),at=new Date().toISOString();
 const statements=[
  database.prepare('INSERT INTO planning_meta (environment,revision,write_token) VALUES (?,0,?) ON CONFLICT(environment) DO NOTHING').bind(environment,''),
  database.prepare('UPDATE planning_meta SET revision=revision+1,write_token=? WHERE environment=? AND revision=? RETURNING revision').bind(token,environment,revision),
 ];
 const allowed='EXISTS (SELECT 1 FROM planning_meta WHERE environment=? AND write_token=?)';
 // Dependent rows first. The revision token gates EVERY statement so a stale
 // writer makes no changes. D1 batch rolls back on any constraint failure.
 for(const table of ['assignments','absences'])statements.push(database.prepare(`DELETE FROM planning_${table} WHERE environment=? AND ${allowed}`).bind(environment,environment,token));
 // Release business-number uniqueness inside this same transaction. Stable
 // internal IDs stay in place, including references from future documents.
 statements.push(database.prepare(`UPDATE planning_projects SET number=? || id WHERE environment=? AND ${allowed}`).bind(`__transaction_${token}_`,environment,environment,token));
 for(const table of ['workers','projects']){
  const extra=table==='projects'?',number':'';
  const value=table==='projects'?",json_extract(value,'$.number')":'';
  const update=table==='projects'?',number=excluded.number':'';
  statements.push(database.prepare(`INSERT INTO planning_${table} (environment,id,payload${extra}) SELECT ?,json_extract(value,'$.id'),value${value} FROM json_each(?) WHERE ${allowed} ON CONFLICT(environment,id) DO UPDATE SET payload=excluded.payload${update}`).bind(environment,JSON.stringify(plan[table]),environment,token));
  statements.push(database.prepare(`DELETE FROM planning_${table} WHERE environment=? AND id NOT IN (SELECT json_extract(value,'$.id') FROM json_each(?)) AND ${allowed}`).bind(environment,JSON.stringify(plan[table]),environment,token));
 }
 statements.push(database.prepare(`INSERT INTO planning_assignments (environment,id,worker_id,project_id,date,payload) SELECT ?,json_extract(value,'$.id'),json_extract(value,'$.workerId'),json_extract(value,'$.projectId'),json_extract(value,'$.date'),value FROM json_each(?) WHERE ${allowed}`).bind(environment,JSON.stringify(plan.assignments),environment,token));
 statements.push(database.prepare(`INSERT INTO planning_absences (environment,id,worker_id,payload) SELECT ?,json_extract(value,'$.id'),json_extract(value,'$.workerId'),value FROM json_each(?) WHERE ${allowed}`).bind(environment,JSON.stringify(plan.absences),environment,token));
 const changes=[];
 for(const [key,label] of [['workers','Monteur'],['projects','Projekt'],['assignments','Einsatz'],['absences','Abwesenheit']]){
  const before=new Map(previous.plan[key].map(row=>[row.id,row]));
  for(const row of plan[key]){
   const old=before.get(row.id);
   if(JSON.stringify(old)!==JSON.stringify(row)){
    const name=row.name??row.number??`${plan.workers.find(w=>w.id===row.workerId)?.name??row.workerId} ${row.date??`${row.from}–${row.to}`}`;
    changes.push(`${label} ${old?'geändert':'hinzugefügt'}: ${name}`);
   }
   before.delete(row.id);
  }
  for(const row of before.values())changes.push(`${label} entfernt: ${row.name??row.number??`${row.workerId} ${row.date??row.from}`}`);
 }
 const summary=changes.join('; ').slice(0,10000)||'Stand wiederhergestellt / unverändert gespeichert';
 const backup=JSON.stringify({...plan,history:[]});
 statements.push(database.prepare(`INSERT INTO planning_revisions (environment,revision,at,actor,summary,payload) SELECT environment,revision,?,?,?,? FROM planning_meta WHERE environment=? AND write_token=?`).bind(at,actor,summary,backup,environment,token));
 const results=await database.batch(statements);
 return results[1].results[0]??null;
}
