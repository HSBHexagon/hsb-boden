import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
export function database(){
 const sqlite=new DatabaseSync(':memory:');
 sqlite.exec(readFileSync(new URL('../migrations/0001.sql',import.meta.url),'utf8'));
 const db={prepare(sql){let args=[];return {bind(...a){args=a;return this},async first(){return sqlite.prepare(sql).get(...args)||null},async all(){return {results:sqlite.prepare(sql).all(...args)}},async run(){const r=sqlite.prepare(sql).run(...args);return {meta:{changes:Number(r.changes)}}},sql,args:()=>args}},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const out=[];for(const s of statements){if(s.sql.includes('RETURNING'))out.push({results:sqlite.prepare(s.sql).all(...s.args())});else {const r=sqlite.prepare(s.sql).run(...s.args());out.push({meta:{changes:Number(r.changes)}})}}sqlite.exec('COMMIT');return out}catch(e){sqlite.exec('ROLLBACK');throw e}}};return {db,sqlite};
}
