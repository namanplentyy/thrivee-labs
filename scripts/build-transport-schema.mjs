import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const schemaDirectory = path.join(repositoryRoot, "schemas");
const idBase =
  "https://raw.githubusercontent.com/namanplentyy/thrivee-labs/main/schemas";
const transportDescription =
  "Structured-output-safe transport form. Convert deterministically to canonical JSON-LD before storage or exchange.";

/**
 * Every canonical document schema and the transport schema generated from it.
 * Documents that share a version must keep their shared $defs byte-identical:
 * a single-file structured-output schema cannot use a cross-file $ref.
 */
const documents = [
  {
    version: "0.1.0",
    canonical: "career-profile.v0.1.schema.json",
    transport: "career-profile.transport.v0.1.schema.json",
    title: "Thrivee Agent-Native Career Profile transport v0.1",
  },
  {
    version: "0.2.0",
    canonical: "career-profile.v0.2.schema.json",
    transport: "career-profile.transport.v0.2.schema.json",
    title: "Thrivee Agent-Native Career Profile transport v0.2",
  },
  {
    version: "0.2.0",
    canonical: "opportunity-intent.v0.2.schema.json",
    transport: "opportunity-intent.transport.v0.2.schema.json",
    title: "Thrivee Agent-Native Opportunity Intent transport v0.2",
  },
];

function toTransportSchema(canonical, document) {
  const transport = structuredClone(canonical);

  transport.$id = `${idBase}/${document.transport}`;
  transport.title = document.title;
  transport.description = transportDescription;

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

  return transport;
}

function assertSharedDefinitionParity(canonicalByFile) {
  const byVersion = new Map();
  for (const document of documents) {
    const group = byVersion.get(document.version) ?? [];
    group.push(document);
    byVersion.set(document.version, group);
  }

  const failures = [];
  for (const [version, group] of byVersion) {
    if (group.length < 2) continue;
    const [first, ...rest] = group;
    const firstDefs = canonicalByFile.get(first.canonical).$defs ?? {};
    for (const other of rest) {
      const otherDefs = canonicalByFile.get(other.canonical).$defs ?? {};
      for (const name of Object.keys(firstDefs)) {
        if (!(name in otherDefs)) continue;
        if (
          JSON.stringify(firstDefs[name]) !== JSON.stringify(otherDefs[name])
        ) {
          failures.push(
            `v${version} $defs/${name} differs between ${first.canonical} and ${other.canonical}`,
          );
        }
      }
    }
  }

  if (failures.length > 0) {
    console.error("Shared $defs have drifted apart:");
    for (const failure of failures) console.error(`  ${failure}`);
    process.exit(1);
  }
}

const canonicalByFile = new Map();
for (const document of documents) {
  const canonicalPath = path.join(schemaDirectory, document.canonical);
  canonicalByFile.set(
    document.canonical,
    JSON.parse(await readFile(canonicalPath, "utf8")),
  );
}

assertSharedDefinitionParity(canonicalByFile);

const checkOnly = process.argv.includes("--check");
let stale = false;

for (const document of documents) {
  const canonical = canonicalByFile.get(document.canonical);
  const transportPath = path.join(schemaDirectory, document.transport);
  const serialized = `${JSON.stringify(
    toTransportSchema(canonical, document),
    null,
    2,
  )}\n`;

  if (checkOnly) {
    let current;
    try {
      current = await readFile(transportPath, "utf8");
    } catch {
      current = null;
    }
    if (current !== serialized) {
      console.error(`Transport schema is stale: schemas/${document.transport}`);
      stale = true;
    }
  } else {
    await writeFile(transportPath, serialized, "utf8");
    console.log(`Wrote schemas/${document.transport}`);
  }
}

if (checkOnly) {
  if (stale) {
    console.error("Run: node scripts/build-transport-schema.mjs");
    process.exit(1);
  }
  console.log(
    "Transport schemas are synchronized with the canonical schemas, and shared $defs match.",
  );
}
