import Core from './core.mjs';
import {applyCommand} from './commands.mjs';
import {readState,writeState} from './store.mjs';
export const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
async function body(request){
 if(!request.headers.get('content-type')?.startsWith('application/json'))throw Error('JSON erforderlich.');
 const reader=request.body?.getReader();if(!reader)throw Error('Daten fehlen.');
 let n=0,chunks=[];while(true){const r=await reader.read();if(r.done)break;n+=r.value.length;if(n>1000000){await reader.cancel();throw Error('Daten zu groß (maximal 1 MB).')}chunks.push(r.value)}
 const out=new Uint8Array(n);let offset=0;for(const c of chunks){out.set(c,offset);offset+=c.length}return JSON.parse(new TextDecoder().decode(out));
}
export async function route(request,env,user){
 const url=new URL(request.url),path=url.pathname,method=request.method,admin=user.role==='admin';
 const write=!['GET','HEAD'].includes(method);
 if(write&&(user.role==='viewer'||request.headers.get('origin')!==url.origin))return json({error:'Änderung nicht erlaubt.'},403);
 if((['/api/users','/api/backups','/api/restore','/api/audit'].includes(path))&&!admin)return json({error:'Administratorrecht erforderlich.'},403);
 try{
  if(path==='/api/state'&&method==='POST'&&!admin)return json({error:'Vollständiger Datenimport erfordert Administratorrecht.'},403);
  if(path==='/api/state'&&method==='GET'){
   const result=await readState(env.DB);
   if(user.role==='viewer'){result.state.absences=result.state.absences.map(a=>({...a,type:'sonstig'}));result.state.projects=result.state.projects.map(p=>({...p,notes:''}));}
   return json({...result,user});
  }
  if(path==='/api/whatsapp'&&method==='GET'){
   const week=url.searchParams.get('week');if(!Core.validDate(week))return json({error:'Ungültige Woche.'},400);
   const {state}=await readState(env.DB);return json({text:Core.whatsAppText(state,week)});
  }
  if((path==='/api/state'||path==='/api/restore'||path==='/api/command')&&method==='POST'){
   const match=request.headers.get('if-match')?.match(/^"(\d+)"$/);if(!match)return json({error:'Revision erforderlich.'},428);
   const data=await body(request);let state=data.state,kind='save';
   if(path==='/api/restore'){
    const backup=await env.DB.prepare('SELECT payload FROM backups WHERE id=?').bind(String(data.id)).first();
    if(!backup)return json({error:'Sicherung nicht gefunden.'},404);
    state=JSON.parse(backup.payload);kind='restore';
   }else if(data.restore===true){if(!admin)return json({error:'Administratorrecht erforderlich.'},403);kind='restore';}
   let commandResult=true,detail;
   if(path==='/api/command'){const current=await readState(env.DB);if(current.revision!==Number(match[1]))return json({error:'Zwischenzeitlich geändert. Bitte aktuellen Stand laden.'},409);state=current.state;state.history=[];commandResult=applyCommand(state,data.command);kind=data.command.type;detail=JSON.stringify(data.command);}
   const result=await writeState(env.DB,state,Number(match[1]),user.email,kind,detail);
   if(!result.ok)return json({error:'Zwischenzeitlich geändert. Aktuellen Stand laden und Änderung erneut prüfen.'},409);
   return json({...result,result:commandResult});
  }
  if(path==='/api/backups'&&method==='GET')return json((await env.DB.prepare('SELECT id,revision,at FROM backups ORDER BY revision DESC').all()).results);
  if(path==='/api/audit'&&method==='GET')return json({changes:(await env.DB.prepare('SELECT * FROM audit ORDER BY revision DESC LIMIT 250').all()).results,roles:(await env.DB.prepare('SELECT * FROM user_audit ORDER BY at DESC LIMIT 100').all()).results});
  if(path==='/api/users'&&method==='GET')return json((await env.DB.prepare('SELECT email,role FROM users ORDER BY email').all()).results);
  if(path==='/api/users'&&method==='POST'){
   const data=await body(request),email=String(data.email||'').toLowerCase();
   if(!['j-cherino@hsb-boden.de','j-post@hsb-boden.de'].includes(email)||!['admin','planner','viewer','disabled'].includes(data.role)||email===user.email)return json({error:'Nur den anderen eingerichteten Benutzer ändern. Eigene Rolle bleibt geschützt.'},400);
   const result=await env.DB.batch([env.DB.prepare("UPDATE users SET role=? WHERE email=? AND EXISTS(SELECT 1 FROM users actor WHERE actor.email=? AND actor.role='admin') AND (role<>'admin' OR ?='admin' OR (SELECT count(*) FROM users WHERE role='admin')>1) RETURNING email").bind(data.role,email,user.email,data.role),env.DB.prepare('INSERT INTO user_audit(id,at,actor,email,role) SELECT ?,?,?,?,? WHERE changes()>0').bind(crypto.randomUUID(),new Date().toISOString(),user.email,email,data.role)]);if(!result[0].results?.length)return json({error:'Letzter Administrator geschützt oder Benutzerrecht wurde geändert.'},409);
   return json({ok:true});
  }
  return json({error:'Endpunkt oder Methode unbekannt.'},404);
 }catch(e){return json({error:e.message?.startsWith('D1_')?'Datenbank momentan nicht verfügbar. Bitte erneut laden.':e.message||'Ungültige Anfrage.'},400);}
}
