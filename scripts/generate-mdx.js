const fs = require("fs");
const path = require("path");

/**
 * Recursively walks a folder and converts all JSON files to MDX format
 * @param {string} inputDir - base input folder
 * @param {string} outputDir - base output folder
 */
function convertJsonToMdx(inputDir, outputDir) {
  const entries = fs.readdirSync(inputDir, { withFileTypes: true });

  for (const entry of entries) {
    const inputPath = path.join(inputDir, entry.name);
    const outputPath = path.join(outputDir, entry.name.replace(/\.json$/, ".mdx"));

    if (entry.isDirectory()) {
      convertJsonToMdx(inputPath, path.join(outputDir, entry.name));
    } else if (entry.isFile() && entry.name.endsWith(".json")) {
      const json = fs.readFileSync(inputPath, "utf-8");
      const parsed = JSON.parse(json);

      const mdxContent = `export const schema = ${JSON.stringify(parsed, null, 2)}\n`;

      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, mdxContent, "utf-8");

      console.log(`✅ Created: ${outputPath}`);
    }
  }
}

function main() {
  const baseInput = path.join(process.cwd(), "configuration-schema");
  const baseOutput = path.join(process.cwd(), "snippets", "configuration-schema");

  if (!fs.existsSync(baseInput)) {
    console.error(`❌ Input folder "${baseInput}" does not exist.`);
    process.exit(1);
  }

  convertJsonToMdx(baseInput, baseOutput);
}

main();
