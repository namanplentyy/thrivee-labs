import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const canonicalPath = path.join(
  repositoryRoot,
  "schemas",
  "career-profile.v0.1.schema.json",
);
const transportPath = path.join(
  repositoryRoot,
  "schemas",
  "career-profile.transport.v0.1.schema.json",
);

const canonical = JSON.parse(await readFile(canonicalPath, "utf8"));
const transport = structuredClone(canonical);

transport.$id =
  "https://raw.githubusercontent.com/namanplentyy/thrivee-labs/main/schemas/career-profile.transport.v0.1.schema.json";
transport.title = "Thrivee Agent-Native Career Profile transport v0.1";
transport.description =
  "Structured-output-safe transport form. Convert deterministically to canonical JSON-LD before storage or exchange.";

transport.required = transport.required.map((propertyName) => {
  if (propertyName === "@context") return "jsonldContext";
  if (propertyName === "@type") return "jsonldType";
  return propertyName;
});

transport.properties.jsonldContext = transport.properties["@context"];
transport.properties.jsonldType = transport.properties["@type"];
delete transport.properties["@context"];
delete transport.properties["@type"];

const contextDefinition = transport.$defs.jsonLdContext;
contextDefinition.required = contextDefinition.required.map((propertyName) =>
  propertyName === "@vocab" ? "vocab" : propertyName,
);
contextDefinition.properties.vocab = contextDefinition.properties["@vocab"];
delete contextDefinition.properties["@vocab"];

const serialized = `${JSON.stringify(transport, null, 2)}\n`;
const checkOnly = process.argv.includes("--check");

if (checkOnly) {
  let current;
  try {
    current = await readFile(transportPath, "utf8");
  } catch {
    current = null;
  }
  if (current !== serialized) {
    console.error(
      "Transport schema is stale. Run: node scripts/build-transport-schema.mjs",
    );
    process.exit(1);
  }
  console.log("Transport schema is synchronized with the canonical schema.");
} else {
  await writeFile(transportPath, serialized, "utf8");
  console.log(`Wrote ${path.relative(repositoryRoot, transportPath)}`);
}
