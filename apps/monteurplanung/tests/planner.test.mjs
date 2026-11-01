import test from 'node:test';
import assert from 'node:assert/strict';
import { initialPlan, summary, monday, shift, weekNumber } from '../lib/planner.ts';
test('Ausfall erhöht Fehlstellen und verändert Bedarf nicht',()=>{const p=initialPlan();p.assignments['2026-10-20'].m1='Krank';const a=summary(p,'2026-10-20')[0];assert.equal(a.demand,3);assert.equal(a.assigned,2);assert.equal(a.missing,1);});
test('Freier Monteur schließt eine Fehlstelle ohne Doppelzählung',()=>{const p=initialPlan();p.assignments['2026-10-20'].m9='B';const rows=summary(p,'2026-10-20');assert.equal(rows[1].assigned,3);assert.equal(rows[1].missing,1);assert.equal(rows.reduce((s,r)=>s+r.assigned,0),9);});
test('Bedarf null, null Monteure, Überbesetzung und Bedarf null unterscheiden',()=>{const p=initialPlan();assert.equal(summary(p,'2026-10-20')[3].missing,null);p.demands['2026-10-20'].A=0;assert.equal(summary(p,'2026-10-20')[0].surplus,3);assert.equal(summary(p,'2026-10-20')[0].missing,0);assert.equal(summary(p,'2026-10-21')[0].demand,3);});
test('Kalenderwochen über Jahreswechsel und Sommerzeit',()=>{assert.equal(monday('2027-01-01'),'2026-12-28');assert.equal(weekNumber('2027-01-01'),53);assert.equal(weekNumber('2027-01-04'),1);assert.equal(shift('2026-10-19',7),'2026-10-26');});
test('Neue Woche übernimmt keine Buchungen oder Bedarfe unbemerkt',()=>{const rows=summary(initialPlan(),'2026-10-26');assert.ok(rows.every(r=>r.assigned===0&&r.demand===null));});
