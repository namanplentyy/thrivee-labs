# Structured-output transport

The canonical profile is JSON-LD. Some model structured-output adapters reject property names beginning with `@`, including `@context`, `@type`, and `@vocab`. v0.1 therefore defines a transport representation with provider-safe aliases.

## Alias mapping

| Transport property | Canonical JSON-LD property |
|---|---|
| `jsonldContext` | `@context` |
| `jsonldContext.vocab` | `@context.@vocab` |
| `jsonldType` | `@type` |

All other properties and values are identical. The transport form does not change IDs, claims, provenance, evidence, dates, ambiguity, or intent.

## Source of truth

`schemas/career-profile.v0.1.schema.json` is authoritative. `schemas/career-profile.transport.v0.1.schema.json` is generated from it by `scripts/build-transport-schema.mjs`.

After editing the canonical schema:

```bash
npm run build:transport-schema
npm run check
```

The check fails if the checked-in transport schema is stale or contains any property beginning with `@`.

## Conversion

`scripts/convert-profile.mjs` and `src/transport.ts` implement the same lossless mapping.

```bash
node scripts/convert-profile.mjs --to-canonical transport.json profile.jsonld
node scripts/convert-profile.mjs --to-transport profile.jsonld transport.json
```

Conversion does not validate the instance. Validate against the input schema before conversion and the output schema after conversion.

## Storage rule

The transport form is an ingestion and generation boundary only. Persist and exchange the canonical JSON-LD representation unless a specific integration contract requires the transport form.
