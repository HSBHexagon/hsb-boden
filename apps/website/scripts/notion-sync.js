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

let _clientInstance = null;

export function getNotionClient() {
  if (_clientInstance) return _clientInstance;
  if (!process.env.NOTION_TOKEN) {
    console.error('❌ NOTION_TOKEN fehlt! Export setzen:');
    console.error('  export NOTION_TOKEN=secret_xxx');
    process.exit(1);
  }
  _clientInstance = new Client({ auth: process.env.NOTION_TOKEN });
  return _clientInstance;
}

/**
 * Executes async map function over items with controlled concurrency.
 * @template T, R
 * @param {T[]} items
 * @param {number} concurrency
 * @param {(item: T, index: number) => Promise<R>} fn
 * @returns {Promise<R[]>}
 */
export async function mapConcurrent(items, concurrency, fn) {
  if (!items || items.length === 0) return [];
  const limit = Math.max(1, Math.min(concurrency || 3, items.length));
  const results = new Array(items.length);
  let index = 0;

  const workers = Array.from({ length: limit }, async () => {
    while (index < items.length) {
      const i = index++;
      results[i] = await fn(items[i], i);
    }
  });

  await Promise.all(workers);
  return results;
}

// ============================================================
// COMMANDS
// ============================================================

export async function cmdStatus(pageId, status, notionClient = getNotionClient()) {
  if (!pageId || !status) {
    console.error('Usage: notion-sync.js status <pageId> <status>');
    process.exit(1);
  }
  await notionClient.pages.update({
    page_id: pageId,
    properties: {
      Status: { select: { name: status } }
    }
  });
  console.log(`✅ Seite ${pageId} → Status: "${status}"`);
}

export async function cmdCreateDeploy(sha, env, notionClient = getNotionClient()) {
  const dbId = process.env.NOTION_DEPLOY_DB_ID;
  if (!dbId) { console.error('❌ NOTION_DEPLOY_DB_ID fehlt'); process.exit(1); }
  const shortSha = (sha || 'manual').substring(0, 7);
  const environment = env || 'Production';
  const now = new Date().toISOString();

  await notionClient.pages.create({
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

export async function cmdListDb(dbId, notionClient = getNotionClient()) {
  if (!dbId) { console.error('Usage: notion-sync.js list-db <dbId>'); process.exit(1); }
  const res = await notionClient.databases.query({ database_id: dbId, page_size: 20 });
  console.log(`\n📊 Datenbank: ${dbId} (${res.results.length} Einträge)`);
  for (const page of res.results) {
    const title = page.properties?.Name?.title?.[0]?.text?.content || '(kein Titel)';
    const status = page.properties?.Status?.select?.name || '-';
    console.log(`  • ${title} | ${status}`);
  }
}

export async function cmdBulkStatus(
  dbId,
  fromStatus,
  toStatus,
  notionClient = getNotionClient(),
  concurrency = Number(process.env.NOTION_CONCURRENCY) || 3
) {
  if (!dbId || !fromStatus || !toStatus) {
    console.error('Usage: notion-sync.js bulk-status <dbId> <fromStatus> <toStatus>');
    process.exit(1);
  }
  const res = await notionClient.databases.query({
    database_id: dbId,
    filter: { property: 'Status', select: { equals: fromStatus } }
  });
  console.log(`🔄 ${res.results.length} Seiten: "${fromStatus}" → "${toStatus}"`);

  await mapConcurrent(res.results, concurrency, async (page) => {
    await notionClient.pages.update({
      page_id: page.id,
      properties: { Status: { select: { name: toStatus } } }
    });
    const title = page.properties?.Name?.title?.[0]?.text?.content || page.id;
    console.log(`  ✅ ${title}`);
  });

  console.log(`\n✅ ${res.results.length} Einträge aktualisiert`);
}

export async function cmdReport(dbId, notionClient = getNotionClient()) {
  if (!dbId) { console.error('Usage: notion-sync.js report <dbId>'); process.exit(1); }
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const res = await notionClient.databases.query({
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

export async function cmdFristCheck(dbId, notionClient = getNotionClient()) {
  if (!dbId) { console.error('Usage: notion-sync.js frist-check <dbId>'); process.exit(1); }
  const today = new Date();
  const in7Days = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString();
  const res = await notionClient.databases.query({
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

export async function runCli(argv = process.argv, notionClient) {
  const [,, command, ...args] = argv;

  const client = notionClient || getNotionClient();

  const commands = {
    'status':       () => cmdStatus(args[0], args[1], client),
    'create-deploy':() => cmdCreateDeploy(args[0], args[1], client),
    'list-db':      () => cmdListDb(args[0], client),
    'bulk-status':  () => cmdBulkStatus(args[0], args[1], args[2], client),
    'report':       () => cmdReport(args[0], client),
    'frist-check':  () => cmdFristCheck(args[0], client),
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

  await commands[command]();
}

if (process.argv[1] && process.argv[1].endsWith('notion-sync.js')) {
  runCli().catch(err => {
    console.error('❌ Fehler:', err.message);
    process.exit(1);
  });
}
