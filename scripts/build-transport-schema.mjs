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
 * Documents in the same `defsFamily` must keep their shared $defs byte-identical:
 * a single-file structured-output schema cannot use a cross-file $ref. The family
 * spans versions, because the v0.3 trust documents reuse the v0.2 definitions
 * verbatim rather than forking a second copy of validity, provenance and disclosure.
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
    defsFamily: "career",
    canonical: "career-profile.v0.2.schema.json",
    transport: "career-profile.transport.v0.2.schema.json",
    title: "Thrivee Agent-Native Career Profile transport v0.2",
  },
  {
    version: "0.2.0",
    defsFamily: "career",
    canonical: "opportunity-intent.v0.2.schema.json",
    transport: "opportunity-intent.transport.v0.2.schema.json",
    title: "Thrivee Agent-Native Opportunity Intent transport v0.2",
  },
  {
    version: "0.3.0",
    defsFamily: "career",
    canonical: "relationship-assertion.v0.3.schema.json",
    transport: "relationship-assertion.transport.v0.3.schema.json",
    title: "Thrivee Agent-Native Relationship Assertion transport v0.3",
  },
  {
    version: "0.3.0",
    defsFamily: "career",
    canonical: "referral-availability.v0.3.schema.json",
    transport: "referral-availability.transport.v0.3.schema.json",
    title: "Thrivee Agent-Native Referral Availability transport v0.3",
  },
  {
    version: "0.3.0",
    defsFamily: "career",
    canonical: "endorsement.v0.3.schema.json",
    transport: "endorsement.transport.v0.3.schema.json",
    title: "Thrivee Agent-Native Endorsement transport v0.3",
  },
  {
    version: "0.3.0",
    defsFamily: "career",
    canonical: "referral.v0.3.schema.json",
    transport: "referral.transport.v0.3.schema.json",
    title: "Thrivee Agent-Native Referral transport v0.3",
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
  const byFamily = new Map();
  for (const document of documents) {
    const family = document.defsFamily ?? document.version;
    const group = byFamily.get(family) ?? [];
    group.push(document);
    byFamily.set(family, group);
  }

  const failures = [];
  for (const [family, group] of byFamily) {
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
            `${family} $defs/${name} differs between ${first.canonical} and ${other.canonical}`,
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
