// Node-only test of the same Apps Script server functions deployed by clasp.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(process.env.HSB_MOBILE_TEST_GS_PATH || __dirname+'/../apps_script/HSB_SALES_OS.gs','utf8');
const box = {console, Session:{getActiveUser:()=>({getEmail:()=>''})},
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'cherinojoel@gmail.com,jordie.post@gmail.com,cherinodiaz@outlook.com'})},
  SpreadsheetApp:{openById:()=>({getEditors:()=>['cherinojoel@gmail.com','jordie.post@gmail.com','cherinodiaz@outlook.com','j-cherino@hsb-boden.de'].map(e=>({getEmail:()=>e})),getOwner:()=>({getEmail:()=> 'cherinojoel@gmail.com'})})},
  ContentService:{MimeType:{JSON:'JSON'},createTextOutput: x=>({setMimeType:()=>x})},
  HtmlService:{createHtmlOutputFromFile: name=>({setTitle: title=>({name,title})})}
};
vm.createContext(box);vm.runInContext(source, box);
function test(name,fn){try{fn();console.log('PASS',name)}catch(err){console.error('FAIL',name,err.message);process.exitCode=1}}
test('anonymous users cannot enqueue mobile requests',()=>{assert.throws(()=>box.uiMobileComQueueDrafts({owner:'JOEL',count:1}),/auth|anmeld|zugriff/i)});
test('unknown Google users cannot enqueue mobile requests',()=>{box.Session.getActiveUser=()=>({getEmail:()=> 'external@gmail.com'});assert.throws(()=>box.uiMobileComQueueDrafts({owner:'JOEL',count:1}),/berechtig|zugriff/i)});
test('allowed Google editor reaches existing queue with same safe parameters',()=>{box.Session.getActiveUser=()=>({getEmail:()=> 'jordie.post@gmail.com'});let got=null;box.uiComQueueDrafts=opts=>(got=opts,{ok:true,data:{status:'COM_REQUESTED'}});const args={owner:'JORDI',count:1,requestId:'mobiltest001'};let r=box.uiMobileComQueueDrafts(args);assert.equal(r.ok,true);assert.deepEqual(JSON.stringify(got),JSON.stringify(args))});
test('mobile status requires caller authentication',()=>{box.Session.getActiveUser=()=>({getEmail:()=>''});assert.throws(()=>box.uiMobileComQueueStatus('COM-JOEL-example01'),/auth|anmeld|zugriff/i)});
test('mobile html only rendered for verified Google editor',()=>{box.Session.getActiveUser=()=>({getEmail:()=> 'cherinodiaz@outlook.com'});let r=box.doGet({parameter:{view:'mobile'}});assert.equal(r.name,'Mobile')});
test('actual signed-in HSB Google identity may open mobile when CRM editor',()=>{box.Session.getActiveUser=()=>({getEmail:()=> 'j-cherino@hsb-boden.de'});let r=box.doGet({parameter:{view:'mobile'}});assert.equal(r.name,'Mobile')});
const mobilePath=process.env.HSB_MOBILE_TEST_HTML_PATH || __dirname+'/../apps_script/Mobile.html';
const html=fs.existsSync(mobilePath)?fs.readFileSync(mobilePath,'utf8'):'';
test('mobile html invokes authorized server wrapper',()=>{assert(html.includes('uiMobileComQueueDrafts'));assert(!html.includes('uiComQueueDrafts('));assert(html.includes('uiMobileComQueueStatus'))});


test('mobile request uses script-wide locking and explicit spreadsheet access with no active document',()=>{
  const captured={appended:[],locked:0,released:0,opened:null};
  const pretendSheet={getDataRange:()=>({getValues:()=>[['Batch_ID','Owner','Type','Status','Requested']]}),appendRow:row=>captured.appended.push(row)};
  const sandbox={
    console,
    Session:{getActiveUser:()=>({getEmail:()=> 'cherinojoel@gmail.com'})},
    PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'cherinojoel@gmail.com'})},
    LockService:{getDocumentLock:()=>null,getScriptLock:()=>({waitLock:()=>captured.locked++,releaseLock:()=>captured.released++})},
    SpreadsheetApp:{getActiveSpreadsheet:()=>null,openById:id=>{captured.opened=id;return {getSheetByName:()=>pretendSheet,getOwner:()=>({getEmail:()=> 'cherinojoel@gmail.com'}),getEditors:()=>[{getEmail:()=> 'cherinojoel@gmail.com'}]}}},
    ContentService:{MimeType:{JSON:'JSON'},createTextOutput:x=>({setMimeType:()=>x})},
    HtmlService:{createHtmlOutputFromFile:name=>({setTitle:title=>({name,title})})},
  };
  vm.createContext(sandbox);vm.runInContext(source,sandbox);sandbox.nowIso_=()=> '2026-10-09T03:00:00Z';
  const r=sandbox.uiMobileComQueueDrafts({owner:'JORDI',count:1,requestId:'mobilefailguard0001'});
  assert.equal(r.ok,true,JSON.stringify(r));
  assert.equal(captured.appended.length,1);
  assert.equal(captured.locked,1);
  assert.equal(captured.released,1);
  assert.equal(captured.opened,'1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg');
});

test('mobile request cannot invent a missing BATCHES tab',()=>{
  const sandbox={
    console,
    Session:{getActiveUser:()=>({getEmail:()=> 'cherinojoel@gmail.com'})},
    PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'cherinojoel@gmail.com'})},
    LockService:{getDocumentLock:()=>null,getScriptLock:()=>({waitLock:()=>{},releaseLock:()=>{}})},
    SpreadsheetApp:{getActiveSpreadsheet:()=>null,openById:()=>({getSheetByName:()=>null,getOwner:()=>({getEmail:()=> 'cherinojoel@gmail.com'}),getEditors:()=>[{getEmail:()=> 'cherinojoel@gmail.com'}],insertSheet:()=>{throw Error('Should not create BATCHES')}})},
    ContentService:{MimeType:{JSON:'JSON'},createTextOutput:x=>({setMimeType:()=>x})},
    HtmlService:{createHtmlOutputFromFile:name=>({setTitle:title=>({name,title})})}
  };
  vm.createContext(sandbox);vm.runInContext(source,sandbox);sandbox.nowIso_=()=> '2026-10-09T03:00:00Z';
  const result=sandbox.uiMobileComQueueDrafts({owner:'JOEL',count:1,requestId:'mobiletestmissing1'});
  assert.equal(result.ok,false,JSON.stringify(result));
  assert.match(result.error,/BATCHES|fehl/i);
});


test('without configured allowlist, only confirmed Google operator may use mobile queue',()=>{
 const sandbox={
  Session:{getActiveUser:()=>({getEmail:()=> 'jordie.post@gmail.com'})},
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> ''})}
 };
 vm.createContext(sandbox);vm.runInContext(source,sandbox);
 assert.throws(()=>sandbox.mobilePrincipal_(),/berechtig|zugriff/i);
});
