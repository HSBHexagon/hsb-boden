"""Stabile Zeilenbindungen im CRM (Developer-Metadaten `hsb.lead_id` je ALL_LEADS-Zeile).

`crm_write_lead_readback` schreibt nie über Zeilennummern, sondern über diese Bindungen. Hier werden
sie angelegt und per Sortier-Canary in einem temporären Tab nachgewiesen, dass Sheets sie beim
Sortieren mit der Zeile mitführt. Lead-Daten selbst werden nicht verändert.
"""
import re
import time

KEY = 'hsb.lead_id'
LEAD_RE = re.compile(r'^HSB-\d{8}-\d+$')
CANARY_TAB = 'HSB_BINDING_CANARY'
CANARY_KEY = 'hsb.canary_id'
BATCH = 400
METADATA_CHAR_LIMIT = 29_000  # Google: 30.000 Zeichen je Tabelle, Reserve für andere Metadaten


def _sheet_id(svc, sid, title):
    sheets = svc.spreadsheets().get(spreadsheetId=sid, fields='sheets.properties').execute().get('sheets', [])
    ids = [s['properties']['sheetId'] for s in sheets if s['properties']['title'] == title]
    return ids[0] if len(ids) == 1 else None


def _row_metadata(row0, sheet_id, key, value):
    return {'createDeveloperMetadata': {'developerMetadata': {
        'metadataKey': key, 'metadataValue': value, 'visibility': 'DOCUMENT',
        'location': {'dimensionRange': {'sheetId': sheet_id, 'dimension': 'ROWS',
                                        'startIndex': row0, 'endIndex': row0 + 1}}}}}


def existing_bindings(svc, sid, key=KEY):
    """{metadataValue: [startIndex, ...]} aller vorhandenen Zeilenbindungen eines Schlüssels."""
    found = svc.spreadsheets().developerMetadata().search(spreadsheetId=sid, body={'dataFilters': [
        {'developerMetadataLookup': {'metadataKey': key, 'locationType': 'ROW', 'visibility': 'DOCUMENT'}}]}).execute()
    out = {}
    for m in found.get('matchedDeveloperMetadata', []):
        meta = m['developerMetadata']
        rng = meta.get('location', {}).get('dimensionRange', {})
        out.setdefault(meta.get('metadataValue'), []).append(rng.get('startIndex'))
    return out


def ensure_bindings(svc, sid, apply=False, sleep=time.sleep, only=None):
    """Legt fehlende Bindungen an; mit `only` nur für diese Lead-IDs (Sheets begrenzt Metadaten auf ~30.000 Zeichen)."""
    rows = svc.spreadsheets().values().get(spreadsheetId=sid, range='ALL_LEADS!A1:A').execute().get('values', [])
    sheet_id = _sheet_id(svc, sid, 'ALL_LEADS')
    if not rows or rows[0][:1] != ['Lead-ID'] or sheet_id is None:
        raise RuntimeError('ALL_LEADS_HEADER_OR_SHEET_MISSING')
    ids = [(i, (r[0].strip() if r else '')) for i, r in enumerate(rows) if i > 0]
    counts = {}
    for _, lid in ids:
        counts[lid] = counts.get(lid, 0) + 1
    have = existing_bindings(svc, sid)
    result = {'rows': len(ids), 'already_bound': 0, 'created': 0, 'skipped_invalid': 0,
              'skipped_duplicate': 0, 'conflicts': 0, 'dry_run': not apply}
    requests = []
    for row0, lid in ids:
        if only is not None and lid not in only:
            continue
        if not LEAD_RE.match(lid):
            result['skipped_invalid'] += 1
        elif counts[lid] > 1:
            result['skipped_duplicate'] += 1
        elif lid in have:
            if have[lid] == [row0]:
                result['already_bound'] += 1
            else:
                result['conflicts'] += 1
        else:
            requests.append(_row_metadata(row0, sheet_id, KEY, lid))
    result['to_create'] = len(requests)
    if apply:
        if only is None:
            raise ValueError('APPLY_REQUIRES_LEADS_FILE')
        used = metadata_chars(svc, sid)
        needed = sum(len(KEY) + len(r['createDeveloperMetadata']['developerMetadata']['metadataValue']) for r in requests)
        if used + needed > METADATA_CHAR_LIMIT:
            raise RuntimeError(f'CRM_METADATA_CAPACITY:{used}+{needed}>{METADATA_CHAR_LIMIT}')
        for start in range(0, len(requests), BATCH):
            svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': requests[start:start + BATCH]}).execute()
            result['created'] += len(requests[start:start + BATCH])
            sleep(1.0)
        verify_bindings(svc, sid, {r['createDeveloperMetadata']['developerMetadata']['metadataValue'] for r in requests})
    return result


def metadata_chars(svc, sid):
    """Belegte Zeichen (Schlüssel + Wert) aller Developer-Metadaten der Tabelle."""
    found = svc.spreadsheets().developerMetadata().search(spreadsheetId=sid, body={'dataFilters': [
        {'developerMetadataLookup': {'visibility': 'DOCUMENT'}}]}).execute()
    return sum(len(m['developerMetadata'].get('metadataKey', '')) + len(m['developerMetadata'].get('metadataValue', ''))
               for m in found.get('matchedDeveloperMetadata', []))


def verify_bindings(svc, sid, lead_ids):
    """Liest die echte Lead-ID jeder gebundenen Zeile zurück; Fehlbindungen werden entfernt und gemeldet."""
    rows = svc.spreadsheets().values().get(spreadsheetId=sid, range='ALL_LEADS!A1:A').execute().get('values', [])
    found = svc.spreadsheets().developerMetadata().search(spreadsheetId=sid, body={'dataFilters': [
        {'developerMetadataLookup': {'metadataKey': KEY, 'locationType': 'ROW', 'visibility': 'DOCUMENT'}}]}).execute()
    wrong = []
    for m in found.get('matchedDeveloperMetadata', []):
        meta = m['developerMetadata']
        if meta.get('metadataValue') not in lead_ids:
            continue
        row0 = meta.get('location', {}).get('dimensionRange', {}).get('startIndex')
        cell = rows[row0][0].strip() if row0 is not None and row0 < len(rows) and rows[row0] else ''
        if cell != meta.get('metadataValue'):
            wrong.append(meta['metadataId'])
    if wrong:
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [
            {'deleteDeveloperMetadata': {'dataFilter': {'developerMetadataLookup': {'metadataId': mid}}}} for mid in wrong]}).execute()
        raise RuntimeError(f'CRM_BINDING_IDENTITY_MISMATCH:{len(wrong)}')


def sort_canary(svc, sid):
    """Temporärer Tab: 5 Zeilen binden, absteigend sortieren, prüfen, dass jede Bindung bei ihrem Wert bleibt."""
    if _sheet_id(svc, sid, CANARY_TAB) is not None:
        raise RuntimeError('CANARY_TAB_EXISTS')
    add = svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [
        {'addSheet': {'properties': {'title': CANARY_TAB}}}]}).execute()
    tab = add['replies'][0]['addSheet']['properties']['sheetId']
    try:
        values = [[f'C{i}'] for i in range(1, 6)]
        svc.spreadsheets().values().update(spreadsheetId=sid, range=f'{CANARY_TAB}!A1:A5',
                                           valueInputOption='RAW', body={'values': values}).execute()
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [
            _row_metadata(i, tab, CANARY_KEY, v[0]) for i, v in enumerate(values)]}).execute()
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [{'sortRange': {
            'range': {'sheetId': tab, 'startRowIndex': 0, 'endRowIndex': 5, 'startColumnIndex': 0, 'endColumnIndex': 1},
            'sortSpecs': [{'dimensionIndex': 0, 'sortOrder': 'DESCENDING'}]}}]}).execute()
        cells = svc.spreadsheets().values().get(spreadsheetId=sid, range=f'{CANARY_TAB}!A1:A5').execute().get('values', [])
        moved = existing_bindings(svc, sid, CANARY_KEY)
        ok = (cells == [[f'C{i}'] for i in range(5, 0, -1)]
              and all(moved.get(f'C{i}') == [5 - i] for i in range(1, 6)))
        return {'sorted': cells == [[f'C{i}'] for i in range(5, 0, -1)], 'bindings_follow_rows': ok}
    finally:
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [{'deleteSheet': {'sheetId': tab}}]}).execute()


def prune_bindings(svc, sid, keep, apply=False):
    """Entfernt nur eigene `hsb.lead_id`-Bindungen außerhalb von `keep`; Zellinhalte bleiben unberührt."""
    rows = svc.spreadsheets().values().get(spreadsheetId=sid, range='ALL_LEADS!A1:A').execute().get('values', [])
    present = [r[0].strip() for r in rows[1:] if r]
    if not keep or any(not LEAD_RE.match(k) or present.count(k) != 1 for k in keep):
        raise ValueError('PRUNE_KEEP_SET_INVALID')
    found = svc.spreadsheets().developerMetadata().search(spreadsheetId=sid, body={'dataFilters': [
        {'developerMetadataLookup': {'metadataKey': KEY, 'locationType': 'ROW', 'visibility': 'DOCUMENT'}}]}).execute()
    drop = [m['developerMetadata']['metadataId'] for m in found.get('matchedDeveloperMetadata', [])
            if m['developerMetadata'].get('metadataValue') not in keep]
    if apply:
        for start in range(0, len(drop), BATCH):
            svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': [
                {'deleteDeveloperMetadata': {'dataFilter': {'developerMetadataLookup': {'metadataId': mid}}}}
                for mid in drop[start:start + BATCH]]}).execute()
    return {'to_remove': len(drop), 'removed': len(drop) if apply else 0, 'dry_run': not apply}
