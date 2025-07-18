const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

/**
 * Recursively walks `inputDir`, parses every .yml/.yaml file,
 * and writes a .mdx file under `outputDir`, preserving folder structure.
 *
 * @param {string} inputDir
 * @param {string} outputDir
 */
function convertYamlToMdx(inputDir, outputDir) {
  const entries = fs.readdirSync(inputDir, { withFileTypes: true });

  for (const entry of entries) {
    const inputPath = path.join(inputDir, entry.name);

    // change .yml/.yaml → .mdx
    const outputName = entry.name.replace(/\.ya?ml$/i, ".mdx");
    const outputPath = path.join(outputDir, outputName);

    if (entry.isDirectory()) {
      // recurse into sub‑folders
      convertYamlToMdx(inputPath, path.join(outputDir, entry.name));
    } else if (entry.isFile() && /\.ya?ml$/i.test(entry.name)) {
      // load and parse the YAML
      const yamlText = fs.readFileSync(inputPath, "utf-8");
      const parsed = yaml.load(yamlText);

      // stringify to nice JSON
      const jsonString = JSON.stringify(parsed, null, 2);

      // wrap in an MDX export
      const mdxContent = `export const schema = ${jsonString};\n`;

      // ensure destination folder exists
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, mdxContent, "utf-8");
      console.log(`✅ ${inputPath} → ${outputPath}`);
    }
  }
}

function main() {
  // adjust these as needed:
  const filepath = "arcadia-yaml";
  const baseInput = path.join(process.cwd(), filepath);
  const baseOutput = path.join(process.cwd(), "snippets", filepath);

  if (!fs.existsSync(baseInput)) {
    console.error(`❌ Input folder "${baseInput}" does not exist.`);
    process.exit(1);
  }

  convertYamlToMdx(baseInput, baseOutput);
}

main();
