#!/usr/bin/env node
/**
 * notion-sync.js
 * Universelles CLI-Tool für alle Notion-Operationen
 * 
 * Verwendung:
 *   NOTION_TOKEN=secret_xxx node scripts/notion-sync.js <command> [options]
 *
 * Commands:
 *   status <pageId> <status>   - Status einer Seite ändern
 *   create-deploy <sha> <env>  - Deploy-Eintrag erstellen
 *   list-db <dbId>             - Datenbank-Einträge auflisten
 *   bulk-status <dbId> <from> <to> - Massenstatus-Update
 *   report <dbId>              - Wochenbericht generieren
 *   frist-check <dbId>         - Fällige Fristen anzeigen
 */

import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

if (!process.env.NOTION_TOKEN) {
  console.error('❌ NOTION_TOKEN fehlt! Export setzen:');
  console.error('  export NOTION_TOKEN=secret_xxx');
  process.exit(1);
}

const [,, command, ...args] = process.argv;

// ============================================================
// COMMANDS
// ============================================================

async function cmdStatus(pageId, status) {
  if (!pageId || !status) {
    console.error('Usage: notion-sync.js status <pageId> <status>');
    process.exit(1);
  }
  await notion.pages.update({
    page_id: pageId,
    properties: {
      Status: { select: { name: status } }
    }
  });
  console.log(`✅ Seite ${pageId} → Status: "${status}"`);
}

async function cmdCreateDeploy(sha, env) {
  const dbId = process.env.NOTION_DEPLOY_DB_ID;
  if (!dbId) { console.error('❌ NOTION_DEPLOY_DB_ID fehlt'); process.exit(1); }
  const shortSha = (sha || 'manual').substring(0, 7);
  const environment = env || 'Production';
  const now = new Date().toISOString();

  await notion.pages.create({
    parent: { database_id: dbId },
    properties: {
      'Name': { title: [{ text: { content: `Deploy ${shortSha} → ${environment}` } }] },
      'Status': { select: { name: '✅ Erfolgreich' } },
      'Umgebung': { select: { name: environment } },
      'Commit SHA': { rich_text: [{ text: { content: shortSha } }] },
      'Deployed At': { date: { start: now } },
    }
  });
  console.log(`✅ Deploy ${shortSha} → ${environment} in Notion eingetragen`);
}

async function cmdListDb(dbId) {
  if (!dbId) { console.error('Usage: notion-sync.js list-db <dbId>'); process.exit(1); }
  const res = await notion.databases.query({ database_id: dbId, page_size: 20 });
  console.log(`\n📊 Datenbank: ${dbId} (${res.results.length} Einträge)`);
  for (const page of res.results) {
    const title = page.properties?.Name?.title?.[0]?.text?.content || '(kein Titel)';
    const status = page.properties?.Status?.select?.name || '-';
    console.log(`  • ${title} | ${status}`);
  }
}

async function cmdBulkStatus(dbId, fromStatus, toStatus) {
  if (!dbId || !fromStatus || !toStatus) {
    console.error('Usage: notion-sync.js bulk-status <dbId> <fromStatus> <toStatus>');
    process.exit(1);
  }
  const res = await notion.databases.query({
    database_id: dbId,
    filter: { property: 'Status', select: { equals: fromStatus } }
  });
  console.log(`🔄 ${res.results.length} Seiten: "${fromStatus}" → "${toStatus}"`);
  for (const page of res.results) {
    await notion.pages.update({
      page_id: page.id,
      properties: { Status: { select: { name: toStatus } } }
    });
    const title = page.properties?.Name?.title?.[0]?.text?.content || page.id;
    console.log(`  ✅ ${title}`);
  }
  console.log(`\n✅ ${res.results.length} Einträge aktualisiert`);
}

async function cmdReport(dbId) {
  if (!dbId) { console.error('Usage: notion-sync.js report <dbId>'); process.exit(1); }
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const res = await notion.databases.query({
    database_id: dbId,
    filter: {
      property: 'Deployed At',
      date: { after: oneWeekAgo }
    }
  });
  const success = res.results.filter(p => p.properties?.Status?.select?.name?.includes('Erfolgreich'));
  const failed  = res.results.filter(p => p.properties?.Status?.select?.name?.includes('Fehlgeschlagen'));
  console.log(`\n📈 === WOCHENBERICHT: Deployments ===`);
  console.log(`  Gesamt:       ${res.results.length}`);
  console.log(`  Erfolgreich:  ${success.length} ✅`);
  console.log(`  Fehlschlag:   ${failed.length} ❌`);
  console.log(`  Zeitraum:     letzte 7 Tage`);
}

async function cmdFristCheck(dbId) {
  if (!dbId) { console.error('Usage: notion-sync.js frist-check <dbId>'); process.exit(1); }
  const today = new Date();
  const in7Days = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString();
  const res = await notion.databases.query({
    database_id: dbId,
    filter: {
      and: [
        { property: 'Frist', date: { before: in7Days } },
        { property: 'Frist', date: { is_not_empty: true } }
      ]
    },
    sorts: [{ property: 'Frist', direction: 'ascending' }]
  });
  console.log(`\n⏰ === FRISTEN in den nächsten 7 Tagen ===`);
  if (res.results.length === 0) {
    console.log('  ✅ Keine fälligen Fristen!');
    return;
  }
  for (const page of res.results) {
    const title = page.properties?.Name?.title?.[0]?.text?.content || '(kein Titel)';
    const frist = page.properties?.Frist?.date?.start || 'unbekannt';
    const daysLeft = Math.ceil((new Date(frist) - today) / (1000 * 60 * 60 * 24));
    const icon = daysLeft < 0 ? '🔴' : daysLeft <= 3 ? '🟠' : '🟡';
    console.log(`  ${icon} ${title}`);
    console.log(`     Frist: ${frist} (${daysLeft >= 0 ? `in ${daysLeft} Tagen` : `${Math.abs(daysLeft)} Tage Überzogen!`})`);
  }
}

// ============================================================
// MAIN DISPATCHER
// ============================================================

const commands = {
  'status':       () => cmdStatus(args[0], args[1]),
  'create-deploy':() => cmdCreateDeploy(args[0], args[1]),
  'list-db':      () => cmdListDb(args[0]),
  'bulk-status':  () => cmdBulkStatus(args[0], args[1], args[2]),
  'report':       () => cmdReport(args[0]),
  'frist-check':  () => cmdFristCheck(args[0]),
};

if (!command || !commands[command]) {
  console.log('🛠️  Notion Sync CLI\n');
  console.log('Commands:');
  Object.keys(commands).forEach(cmd => console.log(`  notion-sync.js ${cmd}`));
  console.log('\nBeispiele:');
  console.log('  node scripts/notion-sync.js list-db <DB_ID>');
  console.log('  node scripts/notion-sync.js frist-check <DB_ID>');
  console.log('  node scripts/notion-sync.js report <DB_ID>');
  process.exit(0);
}

commands[command]().catch(err => {
  console.error('❌ Fehler:', err.message);
  process.exit(1);
});
