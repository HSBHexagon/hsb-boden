#!/usr/bin/env node
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";

const inputDir = process.argv[2];
const outputDir = process.argv[3];
const joelPdf = process.argv[4];
const jordiPdf = process.argv[5];
if (!inputDir || !outputDir || !joelPdf || !jordiPdf) {
  throw new Error("usage: repair-eml-batch.mjs INPUT_DIR OUTPUT_DIR JOEL_PDF JORDI_PDF");
}

mkdirSync(outputDir, { recursive: true });
const wrapBase64 = (value) => value.toString("base64").match(/.{1,76}/g).join("\n");
const replacementPhone = "Tel. 02562 9463030 / Mobil 0151 21886891";
let count = 0;

for (const name of readdirSync(inputDir).filter((entry) => entry.endsWith(".eml"))) {
  const input = readFileSync(join(inputDir, name), "utf8");
  const pdf = name.startsWith("jordi_") ? jordiPdf : joelPdf;
  const encoded = wrapBase64(readFileSync(pdf));
  const withPhone = input.replace(
    /\[Telefonnummer -- bitte selbst ergaenzen, keine verifizierte Nummer in dieser=\r?\n Session vorhanden\]/g,
    replacementPhone,
  );
  if (withPhone === input) throw new Error(`PHONE_PLACEHOLDER_NOT_FOUND: ${name}`);
  const output = withPhone.replace(
    /(Content-Transfer-Encoding: base64\r?\nContent-Disposition: attachment;[^\r\n]+\r?\nMIME-Version: 1\.0\r?\n\r?\n)[A-Za-z0-9+/=\r\n]+(\r?\n--[^\r\n]+--?)/,
    `$1${encoded}$2`,
  );
  if (output === withPhone) throw new Error(`PDF_ATTACHMENT_NOT_FOUND: ${name}`);
  writeFileSync(join(outputDir, basename(name)), output);
  count += 1;
}
console.log(`Korrigierte EMLs geschrieben: ${count}`);
