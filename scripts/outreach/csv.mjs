// Minimaler, RFC4180-artiger CSV-Parser/-Writer ohne externe Dependency.
// Grund: package.json ist laut CLAUDE.md nicht ohne Freigabe änderbar, daher
// keine neue Library (z. B. csv-parse). Unterstützt Anführungszeichen-Felder
// mit eingebetteten Trennzeichen, Zeilenumbrüchen und "" als Escape für ".
// Delimiter ist konfigurierbar, da die Quelldateien uneinheitlich sind:
// die rohen HSB_CRM_Leads_*-Exporte nutzen ";", die HSB_OUTREACH_*-Exporte ",".

export function parseCsv(text, delimiter = ",") {
  // BOM entfernen (Excel-Exporte sind utf-8-BOM).
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);

  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  let i = 0;
  const len = text.length;

  while (i < len) {
    const char = text[i];

    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i++;
        continue;
      }
      field += char;
      i++;
      continue;
    }

    if (char === '"') {
      inQuotes = true;
      i++;
      continue;
    }
    if (char === delimiter) {
      row.push(field);
      field = "";
      i++;
      continue;
    }
    if (char === "\r") {
      i++;
      continue;
    }
    if (char === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      i++;
      continue;
    }
    field += char;
    i++;
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  // Leere Schlusszeile (Datei endet mit \n) verwerfen.
  return rows.filter((r) => !(r.length === 1 && r[0] === ""));
}

export function parseCsvRecords(text, delimiter = ",") {
  const rows = parseCsv(text, delimiter);
  if (rows.length === 0) return { header: [], records: [] };
  const [header, ...dataRows] = rows;
  const records = dataRows.map((r) =>
    Object.fromEntries(header.map((h, idx) => [h, r[idx] ?? ""])),
  );
  return { header, records };
}

function escapeField(value, delimiter) {
  const str = value === null || value === undefined ? "" : String(value);
  if (str.includes(delimiter) || str.includes('"') || str.includes("\n") || str.includes("\r")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function toCsv(header, records, delimiter = ",") {
  const lines = [header.map((h) => escapeField(h, delimiter)).join(delimiter)];
  for (const record of records) {
    lines.push(header.map((h) => escapeField(record[h], delimiter)).join(delimiter));
  }
  return lines.join("\r\n") + "\r\n";
}
