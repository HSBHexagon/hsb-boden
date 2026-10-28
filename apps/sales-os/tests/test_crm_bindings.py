import pytest

import crm_bindings as cb


class _Exec:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class FakeSheets:
    """Minimaler Sheets-Ersatz: Werte je Tab, Zeilen-Metadaten, sortRange führt Metadaten mit."""

    def __init__(self, ids):
        self.tabs = {'ALL_LEADS': (0, [['Lead-ID']] + [[i] for i in ids])}
        self.meta = []
        self.batches = []

    # spreadsheets()
    def spreadsheets(self):
        return self

    def get(self, spreadsheetId, fields=None, range=None):
        if range is not None:
            title, _ = range.split('!')
            return _Exec(lambda: {'values': [list(r) for r in self.tabs[title][1]]})
        return _Exec(lambda: {'sheets': [{'properties': {'title': t, 'sheetId': sid}} for t, (sid, _) in self.tabs.items()]})

    def values(self):
        return self

    def update(self, spreadsheetId, range, valueInputOption, body):
        title, _ = range.split('!')
        sid, _ = self.tabs[title]
        self.tabs[title] = (sid, [list(r) for r in body['values']])
        return _Exec(lambda: {})

    def developerMetadata(self):
        return self

    def search(self, spreadsheetId, body):
        key = body['dataFilters'][0]['developerMetadataLookup']['metadataKey']
        return _Exec(lambda: {'matchedDeveloperMetadata': [{'developerMetadata': m} for m in self.meta if m['metadataKey'] == key]})

    def batchUpdate(self, spreadsheetId, body):
        self.batches.append(body)
        replies = []
        for req in body['requests']:
            if 'createDeveloperMetadata' in req:
                m = dict(req['createDeveloperMetadata']['developerMetadata'])
                m['metadataId'] = len(self.meta) + 1000 + len(self.batches)
                self.meta.append(m)
                replies.append({})
            elif 'deleteDeveloperMetadata' in req:
                mid = req['deleteDeveloperMetadata']['dataFilter']['developerMetadataLookup']['metadataId']
                self.meta = [m for m in self.meta if m.get('metadataId') != mid]
                replies.append({})
            elif 'addSheet' in req:
                sid = 100 + len(self.tabs)
                self.tabs[req['addSheet']['properties']['title']] = (sid, [])
                replies.append({'addSheet': {'properties': {'sheetId': sid}}})
            elif 'deleteSheet' in req:
                sid = req['deleteSheet']['sheetId']
                self.tabs = {t: v for t, v in self.tabs.items() if v[0] != sid}
                self.meta = [m for m in self.meta if m['location']['dimensionRange']['sheetId'] != sid]
                replies.append({})
            elif 'sortRange' in req:
                sid = req['sortRange']['range']['sheetId']
                title = next(t for t, v in self.tabs.items() if v[0] == sid)
                rows = self.tabs[title][1]
                order = sorted(range(len(rows)), key=lambda i: rows[i][0], reverse=True)
                self.tabs[title] = (sid, [rows[i] for i in order])
                new_index = {old: new for new, old in enumerate(order)}
                for m in self.meta:
                    rng = m['location']['dimensionRange']
                    if rng['sheetId'] == sid:
                        rng['startIndex'] = new_index[rng['startIndex']]
                        rng['endIndex'] = rng['startIndex'] + 1
                replies.append({})
        return _Exec(lambda: {'replies': replies})


def test_dry_run_counts_without_writing():
    svc = FakeSheets(['HSB-20260708-00001', 'HSB-20260708-00002', 'kaputt', 'HSB-20260708-00002'])
    res = cb.ensure_bindings(svc, 'x')
    assert res['to_create'] == 1 and res['skipped_invalid'] == 1 and res['skipped_duplicate'] == 2
    assert svc.batches == [] and res['dry_run'] is True


def test_apply_creates_row_bindings_once_and_is_idempotent():
    svc = FakeSheets(['HSB-20260708-00001', 'HSB-20260708-00002'])
    res = cb.ensure_bindings(svc, 'x', apply=True, sleep=lambda s: None)
    assert res['created'] == 2
    assert cb.existing_bindings(svc, 'x') == {'HSB-20260708-00001': [1], 'HSB-20260708-00002': [2]}
    again = cb.ensure_bindings(svc, 'x', apply=True, sleep=lambda s: None)
    assert again['created'] == 0 and again['already_bound'] == 2


def test_misplaced_binding_counts_as_conflict_not_rebound():
    svc = FakeSheets(['HSB-20260708-00001'])
    svc.meta.append(cb._row_metadata(5, 0, cb.KEY, 'HSB-20260708-00001')['createDeveloperMetadata']['developerMetadata'])
    res = cb.ensure_bindings(svc, 'x', apply=True, sleep=lambda s: None)
    assert res['conflicts'] == 1 and res['created'] == 0


def test_wrong_header_refuses():
    svc = FakeSheets([])
    svc.tabs['ALL_LEADS'] = (0, [['Firma']])
    with pytest.raises(RuntimeError, match='ALL_LEADS_HEADER'):
        cb.ensure_bindings(svc, 'x')


def test_sort_canary_proves_bindings_follow_rows_and_cleans_up():
    svc = FakeSheets(['HSB-20260708-00001'])
    assert cb.sort_canary(svc, 'x') == {'sorted': True, 'bindings_follow_rows': True}
    assert cb.CANARY_TAB not in svc.tabs
    assert not [m for m in svc.meta if m['metadataKey'] == cb.CANARY_KEY]
    assert svc.tabs['ALL_LEADS'][1] == [['Lead-ID'], ['HSB-20260708-00001']]


def test_only_and_prune_limit_bindings_to_pilot():
    svc = FakeSheets(['HSB-20260708-00001', 'HSB-20260708-00002', 'HSB-20260708-00003'])
    cb.ensure_bindings(svc, 'x', apply=True, sleep=lambda s: None)
    keep = {'HSB-20260708-00002'}
    assert cb.prune_bindings(svc, 'x', keep) == {'to_remove': 2, 'removed': 0, 'dry_run': True}
    assert cb.prune_bindings(svc, 'x', keep, apply=True)['removed'] == 2
    assert cb.existing_bindings(svc, 'x') == {'HSB-20260708-00002': [2]}
    res = cb.ensure_bindings(svc, 'x', only=keep)
    assert res['to_create'] == 0 and res['already_bound'] == 1


def test_only_binds_just_the_listed_leads():
    svc = FakeSheets(['HSB-20260708-00001', 'HSB-20260708-00002'])
    res = cb.ensure_bindings(svc, 'x', apply=True, sleep=lambda s: None, only={'HSB-20260708-00001'})
    assert res['created'] == 1 and cb.existing_bindings(svc, 'x') == {'HSB-20260708-00001': [1]}
