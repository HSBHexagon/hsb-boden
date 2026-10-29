import Core from './core.mjs';
export async function readState(db){
 const row=await db.prepare('SELECT revision,payload FROM meta,snapshot WHERE meta.id=1').first();
 if(!row)throw Error('Datenbank nicht initialisiert.');
 return {revision:row.revision,state:JSON.parse(row.payload)};
}
export async function writeState(db,state,revision,actor,kind,detail){
 if(!Number.isSafeInteger(revision)||revision<0)throw Error('Revision fehlt.');
 const clean=structuredClone(state);clean.history=[];
 if(!Core.validateDB(clean))throw Error('Ungültige Planungsdaten: Laufzeit, Tagesbedarf, Qualifikation und Abwesenheiten prüfen.');
 const id=crypto.randomUUID(),at=new Date().toISOString();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(clean)))),b=>b.toString(16).padStart(2,'0')).join('');
 const guard='EXISTS(SELECT 1 FROM meta WHERE id=1 AND write_id=?)';
 const q=(sql,...params)=>db.prepare(sql).bind(...params);
 const stmts=[q('UPDATE meta SET revision=revision+1,write_id=? WHERE id=1 AND revision=? RETURNING revision',id,revision),
 q(`INSERT INTO backups(id,revision,at,payload) SELECT ?,?,?,payload FROM snapshot WHERE ${guard}`,id,revision,at,id)];
 for(const table of ['assignments','absences','projects','workers'])stmts.push(q(`DELETE FROM ${table} WHERE ${guard}`,id));
 for(const [table,cols,extract] of [
  ['workers','id,data',"json_extract(value,'$.id'),value"],
  ['projects','id,number,data',"json_extract(value,'$.id'),json_extract(value,'$.number'),value"],
  ['assignments','id,worker_id,project_id,day,data',"json_extract(value,'$.id'),json_extract(value,'$.workerId'),json_extract(value,'$.projectId'),json_extract(value,'$.date'),value"],
  ['absences','id,worker_id,from_day,to_day,data',"json_extract(value,'$.id'),json_extract(value,'$.workerId'),json_extract(value,'$.from'),json_extract(value,'$.to'),value"]]){
   stmts.push(q(`INSERT INTO ${table}(${cols}) SELECT ${extract} FROM json_each(?) WHERE ${guard}`,JSON.stringify(clean[table]),id));
 }
 const message=`${kind==='restore'?'Wiederherstellung':'Plan gespeichert'}: ${clean.projects.length} Projekte, ${clean.workers.length} Monteure, ${clean.assignments.length} Einsätze`;
 stmts.push(q(`INSERT INTO audit(id,revision,at,actor,kind,message,digest,detail) SELECT ?,revision,?,?,?,?,?,? FROM meta WHERE id=1 AND write_id=?`,id,at,actor,kind,message,digest,detail||JSON.stringify({type:kind}),id));
 stmts.push(q(`DELETE FROM backups WHERE id NOT IN(SELECT id FROM backups ORDER BY revision DESC LIMIT 30) AND ${guard}`,id));
 const results=await db.batch(stmts);
 return results[0].results?.length?{ok:true,revision:revision+1}:{ok:false,conflict:true};
}
