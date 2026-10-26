// Regression: native checkbox trigger retired, single secure dialog link instead.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const gs=fs.readFileSync('apps_script/Code.gs','utf8');
const bundle=fs.readFileSync('apps_script/HSB_SALES_OS.gs','utf8');
const side=fs.readFileSync('apps_script/Sidebar.html','utf8');
const mobile=fs.readFileSync('apps_script/Mobile.html','utf8');
for (const src of [gs,bundle]) {
 assert(!src.includes('function onEdit('),'old onEdit trigger must be removed');
 assert(!src.includes('SHEET_DRAFT_BUTTONS_START'),'old checkbox logic must be removed');
 assert(src.includes('uiComQueueDrafts('),'existing guarded COM queue kept');
 assert(src.includes('uiComQueueStatus('),'server status retained');
 assert(src.includes('function uiOpenComControlSheet()'),'sheet navigation retained');
}
assert(side.includes('id="comOpenLink"'),'sidebar now uses dialog link');
assert(side.includes("el('comOpenLink').href"),'dialog link follows owner selection');
assert(!side.includes('id="jordi100Button" onclick='),'fixed 100-draft button removed');
assert(side.includes('owner='),'owner passed to dialog');
const script=mobile.match(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/i);
assert(script,'mobile JS found');
assert(script[1].includes('google.script.url.getLocation'),'mobile reads URL owner query');
assert(script[1].includes('uiMobileComQueueDrafts'),'guarded queue wrapper retained');
const owner={value:'JOEL'};
const sandbox={document:{getElementById:(id)=>id==='owner'?owner:{value:'',disabled:false,textContent:'',className:''}},google:{script:{url:{getLocation:fn=>fn({parameter:{owner:'JORDI'}})}}}};
vm.createContext(sandbox);vm.runInContext(script[1],sandbox);
assert.equal(owner.value,'JORDI','Jordi-specific link should preselect Jordi');
sandbox.applyOwnerFromQuery_({owner:'JOEL'});assert.equal(owner.value,'JOEL');
sandbox.applyOwnerFromQuery_({owner:'FAKE'});assert.equal(owner.value,'JOEL','invalid owner ignored');
console.log('CRM_DIALOG_LINK_TESTS_PASS 14 checks');

// Initial server HTML chooses the owner before asynchronous browser callbacks.
const renderer=gs.match(/function renderComMobile_\(e\) \{[\s\S]*?\n\}/)[0];
const server={HtmlService:{createTemplateFromFile:()=>({
 evaluate(){return {setTitle:()=>this.mobileOwner};}
})}};
vm.createContext(server);vm.runInContext(renderer,server);
for (const [requested,wanted] of [['JORDI','JORDI'],['jordi','JORDI'],['JOEL','JOEL'],['<script>','JOEL'],[undefined,'JOEL']]) {
 assert.equal(server.renderComMobile_({parameter:{owner:requested}}),wanted);
}
assert(mobile.includes('mobileOwner === "JORDI"'),'Jordi selected in initial HTML');
console.log('SERVER_OWNER_RENDER_TESTS_PASS 6 checks');
