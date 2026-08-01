import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

function usage() {
  console.error(
    "Usage: node scripts/convert-profile.mjs (--to-canonical|--to-transport) <input.json> [output.json]",
  );
  process.exit(2);
}

export function toCanonical(transport) {
  const { jsonldContext, jsonldType, ...profile } = transport;
  if (!jsonldContext || !jsonldType) {
    throw new Error("Transport input requires jsonldContext and jsonldType.");
  }

  const { vocab, ...context } = jsonldContext;
  if (!vocab) {
    throw new Error("Transport jsonldContext requires vocab.");
  }

  return {
    "@context": {
      "@vocab": vocab,
      ...context,
    },
    "@type": jsonldType,
    ...profile,
  };
}

export function toTransport(canonical) {
  const { "@context": jsonldContext, "@type": jsonldType, ...profile } =
    canonical;
  if (!jsonldContext || !jsonldType) {
    throw new Error("Canonical input requires @context and @type.");
  }

  const { "@vocab": vocab, ...context } = jsonldContext;
  if (!vocab) {
    throw new Error("Canonical @context requires @vocab.");
  }

  return {
    jsonldContext: {
      vocab,
      ...context,
    },
    jsonldType,
    ...profile,
  };
}

const invokedAsScript = process.argv[1]
  ? fileURLToPath(import.meta.url) === path.resolve(process.argv[1])
  : false;

if (invokedAsScript) {
  const [mode, inputPath, outputPath] = process.argv.slice(2);
  if (
    !["--to-canonical", "--to-transport"].includes(mode) ||
    !inputPath
  ) {
    usage();
  }

  const input = JSON.parse(await readFile(inputPath, "utf8"));
  const output =
    mode === "--to-canonical" ? toCanonical(input) : toTransport(input);
  const serialized = `${JSON.stringify(output, null, 2)}\n`;

  if (outputPath) {
    await writeFile(outputPath, serialized, "utf8");
    console.log(`Wrote ${outputPath}`);
  } else {
    process.stdout.write(serialized);
  }
}
