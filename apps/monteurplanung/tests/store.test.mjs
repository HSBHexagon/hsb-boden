import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { readPlan, writePlan } from '../lib/plan-store.mjs';
import { fixture } from './fixture.mjs';
function database() {
 const db=new DatabaseSync(':memory:');db.exec('PRAGMA foreign_keys=ON');
 db.exec(readFileSync(new URL('../drizzle/0001_planning.sql',import.meta.url),'utf8'));
 const api={prepare(sql){return {bind(...args){return {sql,args}}}},async batch(statements){db.exec('BEGIN');try{const results=statements.map(({sql,args})=>({results:db.prepare(sql).all(...args)}));db.exec('COMMIT');return results}catch(e){db.exec('ROLLBACK');throw e}}};return {db,api};
}
test('relational store persists data, refuses stale write and isolates test environment',async()=>{
 const {api,db}=database();const original=fixture();assert.equal((await readPlan(api,'production')).revision,0);
 const r=await writePlan(api,'test',original,0,'service-test');assert.equal(r.revision,1);
 const second=await readPlan(api,'test');assert.equal(second.plan.projects[0].id,'test-a');assert.equal(second.plan.workers.length,4);
 assert.equal((await readPlan(api,'production')).plan.workers.length,0);
 const changed=structuredClone(original);changed.workers[0].name='TEST geändert';
 assert.equal((await writePlan(api,'test',changed,1,'service-test')).revision,2);
 assert.equal(await writePlan(api,'test',original,1,'service-test'),null);
 assert.equal((await readPlan(api,'test')).plan.workers[0].name,'TEST geändert');
 assert.equal(db.prepare('SELECT count(*) AS n FROM planning_revisions').get().n,2);
 assert.equal(JSON.parse(db.prepare('SELECT payload FROM planning_revisions WHERE revision=1').get().payload).workers[0].name,'TEST Person 0');
});
test('duplicate assignment rolls back revision and entire transaction',async()=>{
 const {api}=database();const original=fixture();await writePlan(api,'test',original,0,'service-test');
 const invalid=structuredClone(original);invalid.assignments=[{id:'a1',workerId:'test-w0',projectId:'test-a',date:'2026-10-21'},{id:'a2',workerId:'test-w0',projectId:'test-b',date:'2026-10-21'}];
 await assert.rejects(()=>writePlan(api,'test',invalid,1,'service-test'));
 assert.equal((await readPlan(api,'test')).revision,1);assert.equal((await readPlan(api,'test')).plan.assignments.length,0);
});
test('future project documents keep their foreign key when the plan changes',async()=>{
 const {api,db}=database();const plan=fixture();await writePlan(api,'test',plan,0,'service-test');
 db.exec("CREATE TABLE future_documents(environment TEXT, project_id TEXT, FOREIGN KEY(environment,project_id) REFERENCES planning_projects(environment,id)); INSERT INTO future_documents VALUES ('test','test-a')");
 plan.projects[0].notes='TEST neue Notiz';
 assert.equal((await writePlan(api,'test',plan,1,'service-test')).revision,2);
 assert.equal(db.prepare('SELECT project_id FROM future_documents').get().project_id,'test-a');
});
test('restore can swap project numbers without breaking stable IDs',async()=>{
 const {api}=database();const original=fixture();await writePlan(api,'test',original,0,'service-test');
 const changed=structuredClone(original);changed.projects[0].number='TEST-C';await writePlan(api,'test',changed,1,'service-test');
 changed.projects[1].number='TEST-A';await writePlan(api,'test',changed,2,'service-test');
 assert.equal((await writePlan(api,'test',original,3,'service-test')).revision,4);
 assert.equal((await readPlan(api,'test')).plan.projects.find(p=>p.id==='test-a').number,'TEST-A');
});
