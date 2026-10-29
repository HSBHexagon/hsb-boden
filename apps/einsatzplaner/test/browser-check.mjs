// Real Chromium UI against the actual local routes and SQLite-backed store.
// MOCK_DATA and injected local identity: this does NOT verify Cloudflare login.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import {createRequire} from 'node:module';
import Core from '../src/core.mjs';
import {route} from '../src/routes.mjs';
import {writeState} from '../src/store.mjs';
import {database} from './sqlite-d1.mjs';
const require=createRequire(new URL('../../website/package.json',import.meta.url));
const {chromium}=require('playwright');
const {db}=database(),state=Core.emptyDB();
const now=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Berlin'}).format(new Date());
const day=Core.asUTC(now).getUTCDay()===0?Core.monday(now):now;
state.workers=Array.from({length:6},(_,i)=>({id:'w'+i,name:'MOCK_DATA Monteur '+(i+1),skills:'',crew:'',active:true}));
state.projects=['A','B'].map((name,i)=>({id:'p'+i,number:'MOCK_DATA-'+name,customer:'MOCK_DATA Baustelle '+name,place:'Testort',start:Core.monday(day),end:Core.plusDays(Core.monday(day),5),requirement:3,dayNeeds:{[day]:3},active:true}));
for(let i=0;i<6;i++)Core.assign(state,'w'+i,i<3?'p0':'p1',day);
await writeState(db,state,0,'test@example.test','save');
const files={
 '/':{body:await readFile(new URL('../public/index.html',import.meta.url)),type:'text/html'},
 '/app.js':{body:await readFile(new URL('../public/app.js',import.meta.url)),type:'application/javascript'},
 '/core.mjs':{body:await readFile(new URL('../src/core.mjs',import.meta.url)),type:'application/javascript'}
};
const server=createServer(async(req,res)=>{
 try{
  const base='http://'+req.headers.host;
  if(req.url.startsWith('/api/')){
   const chunks=[];for await(const chunk of req)chunks.push(chunk);
   const r=await route(new Request(base+req.url,{method:req.method,headers:req.headers,body:['GET','HEAD'].includes(req.method)?undefined:Buffer.concat(chunks)}),{DB:db},{email:'test@example.test',role:'admin'});
   res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));return;
  }
  const file=files[req.url];res.writeHead(file?200:404,{'content-type':file?.type||'text/plain'});res.end(file?.body||'Not found');
 }catch(e){res.writeHead(500);res.end(e.message)}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.HEXAFLOOR_CHROMIUM_EXECUTABLE||undefined,args:['--no-sandbox','--disable-gpu'],env:process.env});
const errors=[];
try{
 const a=await browser.newContext({viewport:{width:1280,height:900},timezoneId:'Europe/Berlin'});
 const b=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Europe/Berlin',isMobile:true,hasTouch:true});
 const desktop=await a.newPage(),mobile=await b.newPage();
 for(const p of [desktop,mobile])p.on('pageerror',e=>errors.push(e.message));
 await Promise.all([desktop.goto(base),mobile.goto(base)]);
 await desktop.waitForSelector('.project-card');await mobile.waitForSelector('.project-card');
 assert.equal(await desktop.locator('.project-card').count(),2);
 await desktop.locator('[data-tab="changes"]').click();
 await desktop.locator('#absenceWorker').selectOption('w5');await desktop.locator('#absenceFrom').fill(day);await desktop.locator('#absenceTo').fill(day);
 await desktop.locator('#absenceForm button').click();
 await desktop.waitForFunction(()=>document.querySelector('#projects').textContent.includes('1 fehlt'));
 await mobile.reload();await mobile.waitForSelector('.project-card');
 assert.match(await mobile.locator('#projects').innerText(),/1 fehlt/);
 for(const p of [desktop,mobile])assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 const evidence=process.env.HEXAFLOOR_BROWSER_EVIDENCE;
 if(evidence){await mkdir(evidence,{recursive:true});await desktop.screenshot({path:evidence+'/desktop.png',fullPage:true});await mobile.screenshot({path:evidence+'/mobile-390.png',fullPage:true});}
 await mobile.locator('[data-tab="changes"]').click();await mobile.locator('[data-action="edit-absence"]').click();
 await mobile.locator('#f_absenceType').selectOption('sonstig');await mobile.locator('button[form="entityForm"]').click();
 await mobile.waitForFunction(()=>!document.querySelector('#modal').open);
 assert.match(await mobile.locator('#absenceList').innerText(),/abwesend/);
 mobile.once('dialog',d=>d.accept());await mobile.locator('[data-action="cancel-absence"]').click();
 await mobile.waitForFunction(()=>!document.querySelector('#absenceList').textContent.includes('Korrigieren'));
 await desktop.reload();await desktop.waitForSelector('.project-card');assert.doesNotMatch(await desktop.locator('#projects').innerText(),/1 fehlt/);
 const getState=p=>p.evaluate(()=>fetch('/api/state').then(r=>r.json()));
 const [s1,s2]=await Promise.all([getState(desktop),getState(mobile)]);assert.deepEqual(s1.state,s2.state);assert.equal(s1.revision,s2.revision);
 const write=(p,name)=>p.evaluate(async({revision,name})=>{const r=await fetch('/api/command',{method:'POST',headers:{'content-type':'application/json','if-match':`"${revision}"`},body:JSON.stringify({command:{type:'worker',id:'w0',data:{name,skills:'',crew:'',active:true}}})});return r.status},{revision:s1.revision,name});
 assert.deepEqual((await Promise.all([write(desktop,'MOCK_DATA Winner A'),write(mobile,'MOCK_DATA Winner B')])).sort(),[200,409]);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({result:'PASS',desktop:'1280px',mobile:'390px; no horizontal overflow',independentBrowserContexts:2,absence:'3→2→3; edit and cancel via UI',concurrentWrites:[200,409],pageErrors:errors,identity:'LOCAL_TEST_ONLY; not Cloudflare Access'}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
