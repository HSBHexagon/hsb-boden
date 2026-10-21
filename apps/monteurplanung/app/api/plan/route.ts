import { env } from 'cloudflare:workers';
import { Core } from '@/public/planner-core.mjs';
import { readPlan, writePlan } from '@/lib/plan-store.mjs';
export const dynamic='force-dynamic';
const json=(data:unknown,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
// Sites dispatch enforces the private allowlist on ALL routes and consumes
// service credentials before forwarding. Never publish this Site publicly.
// Forwarded visitor IDs are Site-specific audit identities, not account UUIDs.
function actor(request:Request) {
 return request.headers.get('oai-authenticated-user-id')??'private-platform-service';
}
function environment(request:Request) {return new URL(request.url).pathname==='/api/test-plan'?'test':'production';}
export async function GET(request:Request) {
 try {return json(await readPlan(env.DB!,environment(request)));}
 catch {return json({error:'Die zentrale Planung konnte nicht geladen werden. Bitte erneut versuchen.'},503);}
}
export async function PUT(request:Request) {
 const user=actor(request);
 const origin=request.headers.get('origin');
 if(!origin||origin!==new URL(request.url).origin)return json({error:'Ungültiger Ursprung.'},403);
 if(!request.headers.get('content-type')?.startsWith('application/json'))return json({error:'JSON erforderlich.'},415);
 const reader=request.body?.getReader();if(!reader)return json({error:'Daten fehlen.'},400);
 let size=0;const chunks:Uint8Array[]=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>1500000){await reader.cancel();return json({error:'Planung zu groß.'},413);}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 let parsed;try{parsed=JSON.parse(new TextDecoder().decode(bytes));}catch{return json({error:'Ungültige Daten.'},400);}
 const {plan,revision}=parsed??{};
 if(!Number.isSafeInteger(revision)||revision<0||!Core.validateDB(plan))return json({error:'Ungültige Planungsdaten. Stammdaten, Zeitraum, Qualifikation und bestehende Einsätze prüfen.'},400);
 try {
  const result=await writePlan(env.DB!,environment(request),plan,revision,user);
  return result?json(result):json({error:'Ein anderer Zugriff hat die Planung geändert. Bitte aktuellen Stand laden und die Änderung erneut eingeben.'},409);
 }catch{return json({error:'Speichern fehlgeschlagen. Der letzte gespeicherte Stand bleibt erhalten. Bitte erneut versuchen.'},503);}
}
