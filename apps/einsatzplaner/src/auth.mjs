const decode=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
export async function verifyJWT(token,config,jwks){
 if(!token||token.length>16384||!config.issuer||!config.audience)throw Error('Anmeldung erforderlich.');
 const parts=token.split('.');if(parts.length!==3)throw Error('Ungültige Anmeldung.');
 const header=JSON.parse(new TextDecoder().decode(decode(parts[0]))),claims=JSON.parse(new TextDecoder().decode(decode(parts[1])));
 const now=Math.floor(Date.now()/1000);
 if(header.alg!=='RS256'||claims.iss!==config.issuer||!Number.isFinite(claims.exp)||claims.exp<=now||claims.nbf>now||!(Array.isArray(claims.aud)?claims.aud:[claims.aud]).includes(config.audience))throw Error('Anmeldung abgelaufen oder ungültig.');
 const jwk=jwks.keys?.find(k=>k.kid===header.kid&&k.kty==='RSA');if(!jwk)throw Error('Signaturschlüssel fehlt.');
 const key=await crypto.subtle.importKey('jwk',jwk,{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
 if(!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',key,decode(parts[2]),new TextEncoder().encode(parts[0]+'.'+parts[1])))throw Error('Ungültige Signatur.');
 return claims;
}
let cached;
export async function identity(request,env){
 const token=request.headers.get('cf-access-jwt-assertion');
 if(!token)throw Error('Anmeldung erforderlich.');
 const issuer=env.ACCESS_ISSUER;
 if(!issuer?.match(/^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com$/))throw Error('Anmeldung nicht eingerichtet.');
 if(!cached||cached.issuer!==issuer||cached.until<Date.now()){
  const response=await fetch(issuer+'/cdn-cgi/access/certs');if(!response.ok)throw Error('Anmeldung nicht verfügbar.');
  cached={issuer,until:Date.now()+300000,keys:await response.json()};
 }
 const claims=await verifyJWT(token,{issuer,audience:env.ACCESS_AUD},cached.keys);
 const email=typeof claims.email==='string'?claims.email.toLowerCase():'';
 const user=await env.DB.prepare('SELECT role FROM users WHERE email=?').bind(email).first();
 if(!user||user.role==='disabled')throw Error('Kein Benutzerrecht für diese Anwendung.');
 return {email,role:user.role};
}
