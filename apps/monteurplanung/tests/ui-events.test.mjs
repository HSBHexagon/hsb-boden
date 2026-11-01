import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../public/planner-ui.mjs', import.meta.url), 'utf8');
const start = source.indexOf("document.addEventListener('click',");
const end = source.indexOf("document.addEventListener('submit',", start);
assert.ok(start >= 0 && end > start, 'Planner click handler must be present');
const clickHandlerSource = source.slice(start, end);

function harness() {
  let onClick;
  const calls = [];
  const context = vm.createContext({
    day: '2026-10-20',
    document: { addEventListener(type, handler) {
      assert.equal(type, 'click');
      onClick = handler;
    } },
    renderPlan: () => calls.push(['renderPlan']),
    showAssign: (...args) => calls.push(['showAssign', ...args]),
    showMoves: (...args) => calls.push(['showMoves', ...args]),
    Core: {
      unassign: (_db, ...args) => calls.push(['unassign', ...args]),
      reassign: (_db, ...args) => calls.push(['reassign', ...args]),
    },
    txn: async fn => fn({}),
    fullname: () => 'Testmonteur',
    confirm: () => true,
    closeModal() {},
    showToast() {},
  });
  vm.runInContext(clickHandlerSource, context);
  return {
    calls,
    context,
    click: dataset => onClick({ target: { closest: () => ({ dataset }) } }),
  };
}

for (const [action, expected] of [
  ['remove', ['unassign', 'worker-1', '2026-10-21']],
  ['assign', ['showAssign', 'project-1', '2026-10-21']],
  ['moves', ['showMoves', 'project-1', '2026-10-21']],
  ['move', ['reassign', 'worker-1', 'project-1', '2026-10-21']],
]) {
  test(`dated ${action} button executes its action`, async () => {
    const h = harness();
    await h.click({ action, date: '2026-10-21', worker: 'worker-1', project: 'project-1' });
    assert.deepEqual(h.calls, [expected]);
  });
}

test('plain date button still changes the selected day and renders the plan', async () => {
  const h = harness();
  await h.click({ date: '2026-10-21' });
  assert.equal(h.context.day, '2026-10-21');
  assert.deepEqual(h.calls, [['renderPlan']]);
});
