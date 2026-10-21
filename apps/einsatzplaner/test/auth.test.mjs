import test from 'node:test';
import assert from 'node:assert/strict';
const {verifyJWT}=await import('../src/auth.mjs').catch(()=>({verifyJWT:async()=>({email:'spoof@example.test'})}));
const keys=await crypto.subtle.generateKey({name:'RSASSA-PKCS1-v1_5',modulusLength:2048,publicExponent:new Uint8Array([1,0,1]),hash:'SHA-256'},true,['sign','verify']);
const jwk=await crypto.subtle.exportKey('jwk',keys.publicKey);jwk.kid='test-key';
const config={issuer:'https://hsb-hexagon.cloudflareaccess.com',audience:'test-aud'};
const b64=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
async function token(p={},header={}){const data=b64({alg:'RS256',kid:'test-key',...header})+'.'+b64({iss:config.issuer,aud:['test-aud'],email:'admin@example.test',exp:Math.floor(Date.now()/1000)+60,...p});return data+'.'+Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5',keys.privateKey,new TextEncoder().encode(data))).toString('base64url')}
test('verify signed Access identity',async()=>{assert.equal((await verifyJWT(await token(),config,{keys:[jwk]})).email,'admin@example.test')});
test('reject expired tokens',async()=>{await assert.rejects(()=>token({exp:1}).then(t=>verifyJWT(t,config,{keys:[jwk]})))});
test('reject wrong audience even when signature valid',async()=>{await assert.rejects(()=>token({aud:['another-app']}).then(t=>verifyJWT(t,config,{keys:[jwk]})))});
test('reject unsigned or tampered identity',async()=>{const t=await token();await assert.rejects(()=>verifyJWT(t.slice(0,-8)+'abcdefgh',config,{keys:[jwk]}));await assert.rejects(()=>verifyJWT(b64({alg:'none'})+'.'+b64({email:'admin@example.test'})+'.',config,{keys:[jwk]}))});
test('reject wrong issuer',async()=>{await assert.rejects(()=>token({iss:'https://attacker.test'}).then(t=>verifyJWT(t,config,{keys:[jwk]})))});
