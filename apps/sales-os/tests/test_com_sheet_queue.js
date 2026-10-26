const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const src = fs.readFileSync('apps_script/Code.gs','utf8');
const code = src.split('// COM_QUEUE_V2_START')[1];
assert(code, 'COM queue implementation missing');
const records = [
 ['Batch_ID','Owner','Campaign','Status','Requested','Selected','Eligible','Excluded','Shortfall','Asset_SHA256','Created_At']
];
const sh = { getDataRange(){return {getValues(){return records.map(r=>r.slice());}}},appendRow(row){records.push(row)} };
const mock = {
 CFG:{SHEET_BATCHES:'BATCHES'},
 sheet_(name){assert.equal(name,'BATCHES');return sh},
 normalizeOwner_(s){return String(s).toUpperCase()},
 nowIso_(){return '2026-10-08T18:00:00Z'},
 LockService:{getScriptLock(){return {waitLock(n){assert(n>0)},releaseLock(){}}}},
 SpreadsheetApp:{getActiveSpreadsheet(){return {getSheetByName(name){assert.equal(name,'BATCHES');return sh}}}}
};
vm.createContext(mock); vm.runInContext(code,mock);
let result=mock.uiComQueueDrafts({owner:'JOEL',count:100,requestId:'test-unique-20261008'});
assert.equal(result.ok,true);
assert.equal(records[1][3],'COM_REQUESTED');
assert.equal(records[1][4],100);
assert.equal(records[1][5],0);
result=mock.uiComQueueDrafts({owner:'JOEL',count:100,requestId:'test-unique-20261008'});
assert.equal(records.length,2,'duplicate request must be idempotent');
let activeDuplicate=mock.uiComQueueDrafts({owner:'JOEL',count:100,requestId:'test-another-20261008'});
assert.equal(activeDuplicate.data.batch_id,records[1][0],'active owner job must be reused');
assert.equal(records.length,2,'active request must not queue a second 100');

assert.equal(result.data.already_exists,true);
let status=mock.uiComQueueStatus(result.data.batch_id);
assert.equal(status.data.status,'COM_REQUESTED');
assert.equal(mock.uiComQueueDrafts({owner:'JOEL',count:101,requestId:'another-unique-20261008'}).ok,false);
assert.equal(mock.uiComQueueDrafts({owner:'WRONG',count:100,requestId:'another-unique-20261008'}).ok,false);
assert.equal(records.length,2);
records[1][16]='INSUFFICIENT_VERIFIED_LEADS';
assert.equal(mock.uiComQueueStatus(records[1][0]).data.error,'INSUFFICIENT_VERIFIED_LEADS');
console.log('COM_QUEUE_JS_TESTS_PASS 7 checks');

const html=fs.readFileSync('apps_script/Sidebar.html','utf8');
assert(html.includes('.uiComQueueDrafts('), 'Sidebar must use COM queue');
assert(html.includes('.uiComQueueStatus('), 'Sidebar must show async job state');
assert(!html.includes('}).uiJordi100('), 'Old operator-only auto-approval is forbidden');
console.log('COM_SIDEBAR_TEST_PASS');
