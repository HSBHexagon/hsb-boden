import test from 'node:test';
import assert from 'node:assert/strict';
import Core from '../src/core.mjs';
const {applyCommand}=await import('../src/commands.mjs').catch(()=>({applyCommand:()=>({})}));
function fixture(){const d=Core.emptyDB();d.workers=[{id:'a',name:'MOCK_DATA A',skills:'',crew:'1',active:true},{id:'b',name:'MOCK_DATA B',skills:'',crew:'1',active:true}];d.projects=[{id:'p',number:'MOCK_DATA-1',customer:'MOCK_DATA',place:'Test',start:'2026-10-19',end:'2026-10-24',requirement:1,dayNeeds:{},active:true}];return d;}
test('server executes named absence operation and returns affected site',()=>{const d=fixture();Core.assign(d,'a','p','2026-10-19');const r=applyCommand(d,{type:'absence',workerId:'a',from:'2026-10-19',to:'2026-10-20',absenceType:'krank'});assert.equal(d.assignments.length,0);assert.equal(r.removed[0].projectId,'p')});
test('zero demand releases assignments while keeping valid data',()=>{const d=fixture();Core.assign(d,'a','p','2026-10-19');applyCommand(d,{type:'need',projectId:'p',from:'2026-10-19',to:'2026-10-19',count:0});assert.equal(d.assignments.length,0);assert.equal(Core.validateDB(d),true)});
test('archive releases future staff and preserves past assignment',()=>{const d=fixture();Core.assign(d,'a','p','2026-10-19');Core.assign(d,'a','p','2026-10-23');applyCommand(d,{type:'project',data:{...d.projects[0],active:false}},'2026-10-21');assert.deepEqual(d.assignments.map(a=>a.date),['2026-10-19']);assert.equal(Core.daySummary(d,'2026-10-19').assigned,1)});
test('crew transfer retains assignments of unavailable team member',()=>{const d=fixture();d.projects.push({...d.projects[0],id:'q',number:'MOCK_DATA-2',requiredSkill:'Fliesen'});Core.assign(d,'a','p','2026-10-19');const r=applyCommand(d,{type:'crew',crew:'1',projectId:'q',date:'2026-10-19'});assert.equal(r.done,0);assert.equal(d.assignments[0].projectId,'p')});
test('shortening absence restores released days and keeps affected assignments for remaining days',()=>{
 const d=fixture();Core.assignRange(d,'a','p','2026-10-19','2026-10-21');Core.markAbsence(d,'a','2026-10-19','2026-10-21','krank');const id=d.absences[0].id;
 const r=applyCommand(d,{type:'edit-absence',id,from:'2026-10-19',to:'2026-10-19',absenceType:'sonstig'});
 assert.equal(r.restored,2);assert.equal(d.absences[0].id,id);assert.equal(d.absences[0].type,'sonstig');assert.deepEqual(d.absences[0].affected,[{projectId:'p',date:'2026-10-19'}]);assert.equal(Core.validateDB(d),true);
});
test('cancelling mistaken absence restores assignments without overwriting a newer allocation',()=>{
 const d=fixture();Core.assignRange(d,'a','p','2026-10-19','2026-10-20');Core.markAbsence(d,'a','2026-10-19','2026-10-20','krank');const id=d.absences[0].id;
 d.projects.push({...d.projects[0],id:'q',number:'MOCK_DATA-2'});applyCommand(d,{type:'edit-absence',id,from:'2026-10-19',to:'2026-10-19',absenceType:'krank'});Core.unassign(d,'a','2026-10-20');Core.assign(d,'a','q','2026-10-20');
 const r=applyCommand(d,{type:'cancel-absence',id});assert.equal(r.restored,1);assert.equal(d.absences.length,0);assert.equal(d.assignments.find(a=>a.date==='2026-10-20').projectId,'q');assert.equal(Core.validateDB(d),true);
});
test('absence correction rejects overlap without mutating data',()=>{
 const d=fixture();Core.markAbsence(d,'a','2026-10-19','2026-10-19','krank');Core.markAbsence(d,'a','2026-10-21','2026-10-21','urlaub');const before=JSON.stringify(d);
 assert.throws(()=>applyCommand(d,{type:'edit-absence',id:d.absences[0].id,from:'2026-10-19',to:'2026-10-21',absenceType:'krank'}),/überschneidet/);assert.equal(JSON.stringify(d),before);
});
test('absence cancellation reports invalid former projects instead of restoring invalid assignments',()=>{
 const d=fixture();Core.assign(d,'a','p','2026-10-19');Core.markAbsence(d,'a','2026-10-19','2026-10-19','krank');d.projects[0].active=false;
 const r=applyCommand(d,{type:'cancel-absence',id:d.absences[0].id});assert.equal(r.restored,0);assert.equal(r.skipped.length,1);assert.equal(d.assignments.length,0);assert.equal(Core.validateDB(d),true);
});
