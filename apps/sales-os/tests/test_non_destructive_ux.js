'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const dir=path.resolve(__dirname,'../apps_script'),names=['Config.gs','Engine.gs','Actions.gs','Code.gs'];
const H='/**\n * HSB Sales OS - Gesamtdatei (Config + Engine + Actions + Code).\n *\n * ERZEUGT von engine/build_single.py - nicht direkt bearbeiten.\n * Aenderungen gehoeren in die Quelldateien unter apps_script/.\n *\n * Apps Script teilt sich einen gemeinsamen Namensraum ueber alle Dateien\n * eines Projekts; das Buendeln aendert daher nichts am Verhalten.\n */\n';
const parts=[H];for(let n of names){parts.push('\n/* '+'='.repeat(66)+'\n   '+n+'\n   '+'='.repeat(66)+' */\n');parts.push(fs.readFileSync(path.join(dir,n),'utf8'));}
assert.equal(fs.readFileSync(path.join(dir,'HSB_SALES_OS.gs'),'utf8'),parts.join('\n'));
const operational=['README','ENTWURF_STEUERUNG','HEUTE JOEL','HEUTE JORDI','POSTEINGANG','INBOUND_EVENTS','ALL_LEADS','DASHBOARD','VERSAND','BATCHES','COM_ROLLOUT_GATE'];
const sheets={},log=[];const expectedValues={README:['TEILBETRIEB – NEUAKQUISE GESPERRT'],DASHBOARD:['=COUNTA(ALL_LEADS!A2:A)'],ALL_LEADS:['HSB-TEST-001']};const valuesBefore=JSON.stringify(expectedValues);let leadRangeCols=null;for(let n of [...operational,'RUNBOOK','CUSTOM_SHEET']){
  sheets[n]={hidden:n==='RUNBOOK',getName(){return n},isSheetHidden(){return this.hidden},hideSheet(){this.hidden=true;log.push('HIDE:'+n)},showSheet(){this.hidden=false;log.push('SHOW:'+n)},getLastColumn(){return n==='ALL_LEADS'?56:10},
  setFrozenRows(){return this},setFrozenColumns(){return this},
  getRange(start,col,numRows,numCols){if(n==='ALL_LEADS'){if(typeof start==='string')throw Error('A1 column beyond 56-grid');if(numCols>56)throw Error('grid width exceeded');leadRangeCols=numCols}return{setFontWeight(){return this},setFontSize(){return this},clear(){throw Error('clear')},setValues(){throw Error('write')}}}};
}
const diagnostic = 'SYNC_STATUS';
sheets[diagnostic] = {hidden:false,getName(){return diagnostic},isSheetHidden(){return this.hidden},hideSheet(){this.hidden=true;log.push('HIDE:'+diagnostic)},showSheet(){this.hidden=false;log.push('SHOW:'+diagnostic)}};
const book={getSheetByName:n=>sheets[n]||null,getSheets:()=>Object.values(sheets)};
const ctx=vm.createContext({SpreadsheetApp:{getActiveSpreadsheet:()=>book,flush(){},getUi:()=>({alert(){},ButtonSet:{OK:'OK'}})}});
for(let n of ['Actions.gs','Code.gs'])vm.runInContext(fs.readFileSync(path.join(dir,n),'utf8'),ctx);
let result=vm.runInContext('setupPremiumSheetUX()',ctx);
assert.equal(result.mode,'formatting_only');assert.equal(leadRangeCols,56,'header formatting stays in 56-col grid');assert.equal(JSON.stringify(expectedValues),valuesBefore,'CRM values and formulas preserved');assert.deepEqual(log,[]);
result=vm.runInContext('uiTidyTabs()',ctx);assert.equal(result.hidden_count,0);
assert.ok(operational.every(n=>!sheets[n].hidden));assert.equal(sheets.CUSTOM_SHEET.hidden,false);assert.equal(sheets.SYNC_STATUS.hidden,false,'SYNC_STATUS diagnostic remains visible');
sheets.RUNBOOK.hidden=false;result=vm.runInContext('uiTidyTabs()',ctx);
assert.equal(result.hidden_count,1);assert.deepEqual(log,['HIDE:RUNBOOK']);
sheets['HEUTE JOEL'].hidden=true;sheets.SYNC_STATUS.hidden=true;log.length=0;
result=vm.runInContext('uiTidyTabs()',ctx);assert.equal(result.ok,true);assert.equal(result.restored_count,1);assert.equal(sheets['HEUTE JOEL'].hidden,false);assert.equal(sheets.SYNC_STATUS.hidden,true,'deliberately hidden SYNC_STATUS stays hidden');assert.deepEqual(log,['SHOW:HEUTE JOEL']);
sheets.RUNBOOK.hidden=false;sheets.RUNBOOK.hideSheet=()=>{throw Error('permission denied')};log.length=0;
result=vm.runInContext('uiTidyTabs()',ctx);assert.equal(result.ok,false);assert.equal(result.errors.length,1);assert.match(result.errors[0],/RUNBOOK/);assert.deepEqual(log,[]);
const oldGet=book.getSheetByName;book.getSheetByName=n=>n==='DASHBOARD'?null:oldGet(n);log.length=0;
result=vm.runInContext('uiSetupPremiumSheetUX()',ctx);assert.equal(result.ok,false);assert.deepEqual(log,[]);
console.log('PASS: bundle parity, no destructive operations, safe operator tabs, fail closed');
