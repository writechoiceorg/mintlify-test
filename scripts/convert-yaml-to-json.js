const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

/**
 * Recursively walks a folder and converts all YAML files to JSON format
 * @param {string} inputDir - base input folder
 * @param {string} outputDir - base output folder
 */
function convertYamlToJson(inputDir, outputDir) {
  const entries = fs.readdirSync(inputDir, { withFileTypes: true });

  for (const entry of entries) {
    const inputPath = path.join(inputDir, entry.name);
    const outputPath = path.join(outputDir, entry.name.replace(/\.ya?ml$/, ".json"));

    if (entry.isDirectory()) {
      convertYamlToJson(inputPath, path.join(outputDir, entry.name));
    } else if (entry.isFile() && /\.ya?ml$/.test(entry.name)) {
      const yamlText = fs.readFileSync(inputPath, "utf-8");
      const parsed = yaml.load(yamlText);
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, JSON.stringify(parsed, null, 2), "utf-8");
      console.log(`✅ Converted: ${inputPath} -> ${outputPath}`);
    }
  }
}

function main() {
  const baseInput = path.join(process.cwd(), "arcadia-yaml");
  const baseOutput = path.join(process.cwd(), "configuration-schema");

  if (!fs.existsSync(baseInput)) {
    console.error(`❌ Input folder \"${baseInput}\" does not exist.`);
    process.exit(1);
  }

  convertYamlToJson(baseInput, baseOutput);
}

main();
