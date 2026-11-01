import {readFile,writeFile,mkdir} from 'node:fs/promises';
const assets={};
for(const [path,file,type] of [['/','public/index.html','text/html'],['/app.js','public/app.js','application/javascript'],['/core.mjs','src/core.mjs','application/javascript']])assets[path]={body:await readFile(file,'utf8'),type:type+'; charset=utf-8'};
await mkdir('src',{recursive:true});await writeFile('src/assets.generated.mjs','export default '+JSON.stringify(assets)+';\n');
console.log('Existing HTML interface and shared planning core packaged.');
