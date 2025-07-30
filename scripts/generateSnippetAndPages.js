const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

//
// CONFIG — adjust these if you need to change folder names
//
const filepath = "model_descriptions";
const baseInput = path.join(process.cwd(), filepath);
const baseSnippetOutput = path.join(process.cwd(), "snippets", filepath);
const basePageOutput = path.join(process.cwd(), "pages", filepath);

//
// will collect all generated page MDX paths (relative to cwd)
//
const generatedPages = [];

/**
 * Recursively walks inputDir, parses every .yml/.yaml file,
 * writes:
 *   1) a snippet MDX under snippetDir
 *   2) a page MDX under pageDir, with frontmatter + imports
 */
function convertYamlToMdx(inputDir, snippetDir, pageDir) {
  const entries = fs.readdirSync(inputDir, { withFileTypes: true });

  for (const entry of entries) {
    const inputPath = path.join(inputDir, entry.name);

    if (entry.isDirectory()) {
      // recurse into sub‑folders
      convertYamlToMdx(inputPath, path.join(snippetDir, entry.name), path.join(pageDir, entry.name));
      continue;
    }

    if (!entry.isFile() || !/\.ya?ml$/i.test(entry.name)) continue;

    // determine output filenames
    const outputName = entry.name.replace(/\.ya?ml$/i, ".mdx");
    const snippetOutputPath = path.join(snippetDir, outputName);
    const pageOutputPath = path.join(pageDir, outputName);

    // --- 1) Snippet MDX ---
    const raw = fs.readFileSync(inputPath, "utf-8");
    const parsed = yaml.load(raw);

    const jsonString = JSON.stringify(parsed, null, 2);
    const snippetContent = `export const schema = ${jsonString};\n`;

    fs.mkdirSync(path.dirname(snippetOutputPath), { recursive: true });
    fs.writeFileSync(snippetOutputPath, snippetContent, "utf-8");
    console.log(`✅ Snippet: ${inputPath} → ${snippetOutputPath}`);

    // --- 2) Page MDX ---
    // extract title from parsed.models[0].name, fallback to filename
    let title = path.basename(outputName, ".mdx");
    if (parsed && Array.isArray(parsed.models) && parsed.models[0] && typeof parsed.models[0].name === "string") {
      title = parsed.models[0].name;
    }

    // build import path to snippet
    const rel = path
      .relative(baseInput, inputPath)
      .replace(/\\/g, "/")
      .replace(/\.ya?ml$/i, ".mdx");
    const snippetImportPath = `/snippets/${filepath}/${rel}`;

    const pageContent = `---
title: ${title}
---

import {SchemaToTable} from "/snippets/SchemaToTable.mdx";
import {schema} from "${snippetImportPath}";

<SchemaToTable schema={schema} />
`;

    fs.mkdirSync(path.dirname(pageOutputPath), { recursive: true });
    fs.writeFileSync(pageOutputPath, pageContent, "utf-8");
    console.log(`✅ Page:    ${pageOutputPath}`);

    // record it (relative to cwd)
    generatedPages.push(path.relative(process.cwd(), pageOutputPath));
  }
}

function main() {
  if (!fs.existsSync(baseInput)) {
    console.error(`❌ Input folder "${baseInput}" does not exist.`);
    process.exit(1);
  }

  // run conversion
  convertYamlToMdx(baseInput, baseSnippetOutput, basePageOutput);

  // write report.json in your snippets folder
  const report = { pages: generatedPages };
  const reportPath = path.join(baseSnippetOutput, "report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`📄 Report:  ${reportPath}`);
}

main();
