import test from 'node:test';
import assert from 'node:assert/strict';
import { Core as c } from '../public/planner-core.mjs';
import { fixture } from './fixture.mjs';
test('Wednesday absence changes only that worker and day; replacement fills shortage',()=>{
  const db=fixture(); c.assignRange(db,'test-w0','test-a','2026-10-19','2026-10-23');c.assignRange(db,'test-w1','test-a','2026-10-19','2026-10-23');c.assignRange(db,'test-w2','test-b','2026-10-19','2026-10-23');
  const unaffected=structuredClone(db.assignments.filter(a=>a.workerId!=='test-w0'||a.date!=='2026-10-21'));
  c.markAbsence(db,'test-w0','2026-10-21','2026-10-21','krank');
  assert.equal(c.daySummary(db,'2026-10-21').missing,1);
  assert.deepEqual(db.assignments,unaffected);
  assert.deepEqual(c.candidates(db,'test-a','2026-10-21').map(w=>w.id),['test-w3']);
  c.assign(db,'test-w3','test-a','2026-10-21');assert.equal(c.daySummary(db,'2026-10-21').missing,0);
  assert.throws(()=>c.assign(db,'test-w3','test-b','2026-10-21'),/bereits/);
  const text=c.whatsAppText(db,'2026-10-19');assert.match(text,/Testtreffpunkt/);assert.match(text,/06:30/);assert.doesNotMatch(text,/krank|urlaub|sonstig|Vertrauliche/i);
});
test('extension and Saturday preserve existing bookings',()=>{
 const db=fixture();c.assign(db,'test-w0','test-a','2026-10-23');const before=structuredClone(db.assignments);
 c.extendProject(db,'test-a','2026-10-26',false);assert.deepEqual(db.assignments,before);
 c.updateNeed(db,'test-a','2026-10-24','2026-10-24',1);c.assign(db,'test-w1','test-a','2026-10-24');assert.equal(c.daySummary(db,'2026-10-24').missing,0);assert.deepEqual(db.assignments[0],before[0]);
});
test('server validation rejects inactive or archived assignments, missing skills, Sunday and out of range',()=>{
 for(const mutate of [d=>d.workers[0].active=false,d=>d.projects[0].active=false,d=>d.workers[0].skills='',d=>d.projects[0].end='2026-10-20',d=>d.assignments[0].date='2026-10-25']){
 const db=fixture();c.assign(db,'test-w0','test-a','2026-10-21');mutate(db);assert.equal(c.validateDB(db),false);
 }
});
test('project has name or customer, location and bounded dates and daily needs',()=>{
 for(const mutate of [d=>d.projects[0].place='',d=>{d.projects[0].customer='';d.projects[0].title=''},d=>d.projects[0].dayNeeds={'2026-10-21':-1},d=>d.projects[0].start='1900-01-01']){
 const db=fixture();mutate(db);assert.equal(c.validateDB(db),false);
 }
});
test('WhatsApp does not imply work on gap days',()=>{
 const db=fixture();db.projects[0].dayNeeds={'2026-10-20':0,'2026-10-22':0,'2026-10-23':0};db.projects[1].active=false;
 c.assign(db,'test-w0','test-a','2026-10-19');c.assign(db,'test-w0','test-a','2026-10-21');const t=c.whatsAppText(db,'2026-10-19');assert.doesNotMatch(t,/Mo–Mi/);assert.match(t,/Mo 19/);assert.match(t,/Mi 21/);
});
test('week calculation at Thursday and year boundary',()=>{assert.equal(c.isoWeek('2026-10-19').num,43);assert.equal(c.isoWeek('2026-10-22').num,43);assert.equal(c.isoWeek('2027-01-01').num,53);});
test('reassignment suggestions use only excess staff and move only after explicit action',()=>{
 const db=fixture();c.assign(db,'test-w0','test-b','2026-10-21');c.assign(db,'test-w1','test-b','2026-10-21');
 const before=structuredClone(db.assignments);const proposals=c.suggestMoves(db,'test-a','2026-10-21');
 assert.equal(proposals.length,2);assert.deepEqual(db.assignments,before);
 c.reassign(db,'test-w1','test-a','2026-10-21');assert.equal(c.daySummary(db,'2026-10-21').projects.find(p=>p.project.id==='test-b').missing,0);
 assert.throws(()=>c.reassign(db,'test-w0','test-a','2026-10-21'),/Überbesetzung/);
});
