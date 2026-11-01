import {identity} from './auth.mjs';
import {route,json} from './routes.mjs';
import assets from './assets.generated.mjs';
const security={
 'cache-control':'no-store',
 'content-security-policy':"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
 'x-content-type-options':'nosniff','referrer-policy':'no-referrer','permissions-policy':'camera=(), microphone=(), geolocation=()','strict-transport-security':'max-age=31536000'
};
export default {
 async fetch(request,env){
  let response;
  try{
   const user=await identity(request,env),path=new URL(request.url).pathname;
   if(path.startsWith('/api/'))response=await route(request,env,user);
   else if(request.method==='GET'&&assets[path])response=new Response(assets[path].body,{headers:{'content-type':assets[path].type}});
   else response=json({error:'Nicht gefunden.'},404);
  }catch{response=json({error:'Anmeldung erforderlich oder Benutzer nicht freigeschaltet.'},401)}
  const headers=new Headers(response.headers);for(const [key,value] of Object.entries(security))headers.set(key,value);
  return new Response(response.body,{status:response.status,headers});
 }
};
