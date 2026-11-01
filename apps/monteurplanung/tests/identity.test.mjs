import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
test('private platform visitor identity is not compared with a global account UUID',()=>{
 const source=readFileSync(new URL('../app/api/plan/route.ts',import.meta.url),'utf8');
 const match=source.match(/function actor\(request:Request\) \{[\s\S]*?\n\}/);
 assert.ok(match,'production actor function is available');
 const getActor=vm.runInNewContext(match[0].replace('request:Request','request')+';actor',{ownerId:'2436f47b-7dc9-4e7b-8932-ebf0e4289fa8'});
 const siteUser='verified-site-specific-owner';
 assert.equal(getActor({headers:new Map([['oai-authenticated-user-id',siteUser]])}),siteUser);
});
