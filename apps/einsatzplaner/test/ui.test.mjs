import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import Core from '../src/core.mjs';
import {route} from '../src/routes.mjs';
import {database} from './sqlite-d1.mjs';
import {writeState} from '../src/store.mjs';
const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
const script=readFileSync(new URL('../public/app.js',import.meta.url),'utf8').replace("import Core from '/core.mjs';",'const Core=window.Core;');
async function session(db,role='admin'){
 const dom=new JSDOM(html,{url:'https://planner.test/',runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window;
 w.Core=Core;w.structuredClone=structuredClone;w.confirm=()=>true;w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')};
 w.fetch=async(path,init={})=>{const r=new Request('https://planner.test'+path,init);if(init.method)r.headers.set('origin','https://planner.test');return route(r,{DB:db},{email:'j-cherino@hsb-boden.de',role});};
 w.eval(script);await settle();return dom;
}
async function settle(){await new Promise(r=>setTimeout(r,35));}
function click(w,s){w.document.querySelector(s).click()}
function fill(w,id,value){w.document.getElementById(id).value=value;}
test('existing UI creates project and worker through command API and second session reads same persisted data',async()=>{
 const {db}=database();const a=await session(db),w=a.window;
 try{
 click(w,'[data-action="new-project"]');for(const [id,value]of Object.entries({f_number:'MOCK_DATA-UI',f_customer:'MOCK_DATA Customer',f_place:'Test',f_start:'2026-10-19',f_end:'2026-10-24'}))fill(w,id,value);
 w.document.getElementById('entityForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await settle();
 assert.equal(w.document.querySelector('#modal').open,false);assert.match(w.document.querySelector('.local').textContent,/Stand 1/);
 click(w,'[data-action="new-worker"]');fill(w,'f_name','MOCK_DATA UI Worker');w.document.getElementById('entityForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await settle();
 assert.match(w.document.querySelector('.local').textContent,/Stand 2/);
 const b=await session(db);try{click(b.window,'[data-tab="data"]');assert.match(b.window.document.querySelector('#projectList').textContent,/MOCK_DATA-UI/);click(b.window,'[data-subtab="workers"]');assert.match(b.window.document.querySelector('#workerList').textContent,/MOCK_DATA UI Worker/)}finally{b.window.close()}
 }finally{a.window.close()}
});
test('read-only UI prevents mutations after tab changes',async()=>{const {db}=database();const a=await session(db,'viewer'),w=a.window;try{click(w,'[data-tab="data"]');click(w,'[data-subtab="workers"]');assert.equal(w.document.querySelector('#sub-workers [data-action="new-worker"]').disabled,true);click(w,'[data-tab="changes"]');assert.equal(w.document.querySelector('#absenceForm button').disabled,true)}finally{w.close()}});
test('simple project view shows three staff then one missing after sickness without replacement dialog',async()=>{
 const {db}=database(),state=Core.emptyDB();
 const now=new Date(),today=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`,date=now.getDay()===0?Core.monday(today):today;
 state.workers=['A','B','C'].map(id=>({id,name:'MOCK_DATA '+id,crew:'',skills:'',active:true}));
 state.projects=[{id:'p',number:'MOCK_DATA',customer:'MOCK_DATA Baustelle',place:'Test',start:Core.monday(date),end:Core.plusDays(Core.monday(date),5),requirement:3,dayNeeds:{[date]:3},active:true}];
 for(const w of state.workers)Core.assign(state,w.id,'p',date);
 await writeState(db,state,0,'test@example.test','save');
 const a=await session(db),w=a.window;
 try{
  assert.equal(w.document.querySelectorAll('[data-action="whatsapp"]').length,0);
  assert.match(w.document.querySelector('#projects').textContent,/3\s*\/\s*3/);
  click(w,'[data-tab="changes"]');fill(w,'absenceWorker','A');fill(w,'absenceFrom',date);fill(w,'absenceTo',date);fill(w,'absenceType','krank');
  w.document.getElementById('absenceForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await settle();
  assert.equal(w.document.querySelector('#modal').open,false);
  const text=w.document.querySelector('#projects').textContent;
  assert.match(text,/2\s*\/\s*3/);assert.match(text,/1 fehlt/);assert.match(text,/MOCK_DATA A.*krank/);
  click(w,'[data-tab="changes"]');assert.match(w.document.querySelector('#absenceList').textContent,/MOCK_DATA A/);
  const viewer=await session(db,'viewer');try{assert.equal(viewer.window.document.querySelector('[data-action="cancel-absence"]').disabled,true)}finally{viewer.window.close()}
  click(w,'[data-action="edit-absence"]');assert.equal(w.document.querySelector('#modal').open,true);fill(w,'f_absenceType','sonstig');
  w.document.getElementById('entityForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await settle();assert.equal(w.document.querySelector('#modal').open,false);assert.match(w.document.querySelector('#projects').textContent,/abwesend/);
  click(w,'[data-action="cancel-absence"]');await settle();
  assert.match(w.document.querySelector('#projects').textContent,/3\s*\/\s*3/);assert.doesNotMatch(w.document.querySelector('#projects').textContent,/1 fehlt|krank/);
 }finally{w.close()}
});
