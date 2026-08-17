# Thrivee Labs: Agent-Native Career Schema

This repository contains the implementation-facing artifacts for an evidence-aware, agent-native career profile. The canonical representation is JSON-LD; a structurally equivalent transport representation supports model APIs that reject JSON-LD property names in structured-output schemas.

The current release is **v0.1.0-draft**. It is suitable for implementation and private evaluation, but it is not yet a stable public standard.

## What is included

- A canonical JSON-LD JSON Schema.
- A provider-safe transport JSON Schema generated from the canonical schema.
- Matching TypeScript interfaces.
- Lossless canonical/transport conversion utilities.
- Synthetic examples with no real personal data.
- Validation rules for schemas, references, examples, and conversion.
- Implementation notes for extraction, ambiguity, provenance, and v0.0 migration.

Private research and evaluation data live under ignored `research/` and `tests/` directories and must not be published.

## Repository layout

```text
schemas/
  career-profile.v0.1.schema.json
  career-profile.transport.v0.1.schema.json
src/
  types.ts
  transport.ts
examples/
  career-profile.synthetic.jsonld
  career-profile.transport.synthetic.json
docs/v0.1/
  schema.md
  extraction-contract.md
  transport.md
  migration-from-v0.0.md
scripts/
  build-transport-schema.mjs
  convert-profile.mjs
  validate_examples.py
```

## Quick validation

Python 3, Node.js, and the Python `jsonschema` package are required.

```bash
python3 -m pip install -r requirements-dev.txt
npm run check
```

Regenerate the transport schema after changing the canonical schema:

```bash
npm run build:transport-schema
```

Convert an instance without changing its meaning:

```bash
node scripts/convert-profile.mjs --to-transport input.jsonld output.json
node scripts/convert-profile.mjs --to-canonical output.json restored.jsonld
```

## Design principles

- Missing information remains missing. Unknown credits, levels, taxonomy mappings, dates, and identity values are never invented.
- Origination, verification, confidence, and source location are separate provenance dimensions.
- Inferred skills require directional evidence. An explicit skill-list statement may stand on its source provenance without an engagement link.
- Interests are not automatically career intent.
- Ambiguity is represented, not silently resolved.
- Current status is tri-state: `true`, `false`, or `null`, each with an explicit basis.
- The transport representation is an ingestion boundary. Canonical storage and exchange use JSON-LD.

## Scope

v0.1 covers identity routing, career history, skills, interests, languages, personal attributes, basic career intent, provenance, and ambiguity. MCP servers, API endpoints, blockchain ledgers, decentralized registries, skill-decay models, and automated taxonomy inference are deliberately out of scope.

See [the v0.1 schema contract](docs/v0.1/schema.md) for normative behavior.

## Private resume conversion skill

Codex discovers the repository-scoped `convert-resume-to-career-profile` skill under `.agents/skills/` when working inside this repository. Invoke it with an authorized PDF:

```text
$convert-resume-to-career-profile /absolute/path/to/resume.pdf
```

The skill resolves the live extraction version through `schemas/schema-manifest.json`, validates the canonical profile and transport round-trip, and saves only ignored private outputs under `private/career-profile-runs/`. Real resumes and derived profiles must never be committed or published.

## License

Apache-2.0.
