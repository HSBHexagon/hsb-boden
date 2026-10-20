import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import Core from '../src/core.mjs';
import {route} from '../src/routes.mjs';
import {database} from './sqlite-d1.mjs';
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
