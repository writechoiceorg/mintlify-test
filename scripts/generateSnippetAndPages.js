// convert-with-column-check.js

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

//
// CONFIG — adjust these folder names if needed
//
const SRC_DIR = path.join(process.cwd(), "model_descriptions");
const SNIPPET_DIR = path.join(process.cwd(), "snippets", "model_descriptions");
const PAGE_DIR = path.join(process.cwd(), "pages", "model_descriptions");
const REPORT_OK_PATH = path.join("report.json");
const REPORT_FAIL_PATH = path.join("broken.json");

const generatedPages = [];
const brokenYamls = [];

/**
 * Returns true if every `parsed.models` entry has a non‑empty `columns` array
 */
function hasColumns(parsed) {
  if (!Array.isArray(parsed.models) || parsed.models.length === 0) {
    return false;
  }
  return parsed.models.every((m) => Array.isArray(m.columns) && m.columns.length > 0);
}

/**
 * Walk `dir`, for each .yml/.yaml:
 *  - parse & check columns
 *  - if OK: emit snippet + page MDX, record its page path
 *  - if missing columns: record the YAML in brokenYamls
 */
function walkAndConvert(dir, snippetDir, pageDir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullSrc = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      walkAndConvert(fullSrc, path.join(snippetDir, entry.name), path.join(pageDir, entry.name));
      continue;
    }

    if (!/\.ya?ml$/i.test(entry.name)) {
      continue;
    }

    // load + parse
    let parsed;
    try {
      parsed = yaml.load(fs.readFileSync(fullSrc, "utf-8"));
    } catch (e) {
      console.warn(`⚠️  Invalid YAML, skipping: ${fullSrc}`);
      brokenYamls.push(path.relative(process.cwd(), fullSrc).replace(/\\/g, "/"));
      continue;
    }

    // check columns only
    if (!hasColumns(parsed)) {
      console.log(`❌  Missing columns, skipping: ${fullSrc}`);
      brokenYamls.push(path.relative(process.cwd(), fullSrc).replace(/\\/g, "/"));
      continue;
    }

    // prepare names
    const baseName = entry.name.replace(/\.ya?ml$/i, "");
    const snippetOut = path.join(snippetDir, `${baseName}.mdx`);
    const pageOut = path.join(pageDir, `${baseName}.mdx`);

    // 1) Snippet MDX
    const schemaJson = JSON.stringify(parsed, null, 2);
    const snippetMd = `export const schema = ${schemaJson};\n`;
    fs.mkdirSync(path.dirname(snippetOut), { recursive: true });
    fs.writeFileSync(snippetOut, snippetMd, "utf-8");

    // 2) Page MDX
    let title = baseName;
    if (parsed.models[0] && typeof parsed.models[0].name === "string") {
      title = parsed.models[0].name;
    }

    const relSnippetPath = path.relative(path.join(process.cwd(), "snippets"), snippetOut).replace(/\\/g, "/");

    const pageMd = `---
title: ${title}
---

import {SchemaToTable} from "/snippets/SchemaToTable.mdx";
import {schema} from "/snippets/${relSnippetPath}";

<SchemaToTable schema={schema} />
`;
    fs.mkdirSync(path.dirname(pageOut), { recursive: true });
    fs.writeFileSync(pageOut, pageMd, "utf-8");

    const relPage = path.relative(process.cwd(), pageOut).replace(/\\/g, "/");
    generatedPages.push(relPage);

    console.log(`✅  Generated: ${relPage}`);
  }
}

function main() {
  if (!fs.existsSync(SRC_DIR)) {
    console.error(`❌  Source directory not found: ${SRC_DIR}`);
    process.exit(1);
  }

  walkAndConvert(SRC_DIR, SNIPPET_DIR, PAGE_DIR);

  // Write the “working” report
  fs.mkdirSync(path.dirname(REPORT_OK_PATH), { recursive: true });
  fs.writeFileSync(REPORT_OK_PATH, JSON.stringify({ pages: generatedPages }, null, 2), "utf-8");
  console.log(`📄  report.json written: ${REPORT_OK_PATH}`);

  // Write the “broken” report
  fs.writeFileSync(REPORT_FAIL_PATH, JSON.stringify({ broken: brokenYamls }, null, 2), "utf-8");
  console.log(`📄  broken.json written: ${REPORT_FAIL_PATH}`);

  console.log(`✔️  Done: ${generatedPages.length} pages, ${brokenYamls.length} broken.`);
}

main();
